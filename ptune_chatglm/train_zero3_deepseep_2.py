from accelerate import Accelerator, DeepSpeedPlugin
from transformers import AutoTokenizer, AutoModel, AdamW, get_scheduler
from torch.utils.data import DataLoader
import torch
import peft
from utils.common_utils import CastOutputToFloat, second2time, save_model
from data_handle.data_loader import get_data
from glm_config import ProjectConfig
from torch.utils.tensorboard import SummaryWriter
from transformers.trainer_pt_utils import get_parameter_names
from torch import nn
from accelerate import DistributedType
import time
import os
import traceback

pc = ProjectConfig()

def build_objects():
    tokenizer = AutoTokenizer.from_pretrained(pc.pre_model, trust_remote_code=True)
    model = AutoModel.from_pretrained(pc.pre_model, trust_remote_code=True)
    model = model.half()
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    model.config.use_cache = False

    if pc.use_lora:
        model.transformer.output_layer = CastOutputToFloat(model.transformer.output_layer)
        lora_cfg = peft.LoraConfig(
            task_type=peft.TaskType.CAUSAL_LM,
            r=pc.lora_rank,
            lora_alpha=32,
            lora_dropout=0.1,
            inference_mode=False,
        )
        model = peft.get_peft_model(model, lora_cfg)

    train_dl, dev_dl = get_data()

    decay_keys = get_parameter_names(model, [nn.LayerNorm, nn.RMSNorm])
    decay_keys = [n for n in decay_keys if "bias" not in n]

    optim_groups = [
        {
            "params": [p for n, p in model.named_parameters() if n in decay_keys and p.requires_grad],
            "weight_decay": pc.weight_decay,
        },
        {
            "params": [p for n, p in model.named_parameters() if n not in decay_keys and p.requires_grad],
            "weight_decay": 0.0,
        },
    ]
    optim_groups = [g for g in optim_groups if g["params"]]
    optimizer = AdamW(optim_groups, lr=pc.learning_rate)

    warmup_steps = int(pc.warmup_ratio * len(train_dl) * pc.epochs)
    scheduler = get_scheduler(
        "linear", optimizer=optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=len(train_dl) * pc.epochs,
    )

    return tokenizer, model, optimizer, scheduler, train_dl, dev_dl

def evaluate(engine, dl):
    """计算验证集平均 loss"""
    engine.eval()
    losses = []
    with torch.no_grad():
        for batch in dl:
            out = engine(
                input_ids=batch["input_ids"],
                labels=batch["labels"],
            )
            losses.append(out.loss.item())
    engine.train()
    return sum(losses) / len(losses)

def main():
    ds_plugin = DeepSpeedPlugin(zero_stage=3)
    accelerator = Accelerator(
        log_with="tensorboard",
        project_dir=pc.log_dir,
        mixed_precision="fp16",
        deepspeed_plugin=ds_plugin
    )

    if accelerator.distributed_type == DistributedType.DEEPSPEED:
        print(f"✅ running with DeepSpeed, world size = {accelerator.num_processes}")
    else:
        raise RuntimeError(f"unexpected distributed backend: {accelerator.distributed_type}")

    writer = None
    try:
        tok, model, optim, sched, train_dl, dev_dl = build_objects()

        if accelerator.is_main_process:
            writer = SummaryWriter(log_dir=pc.log_dir)

        model, optim, sched, train_dl, dev_dl = accelerator.prepare(
            model, optim, sched, train_dl, dev_dl
        )

        steps_per_epoch = len(train_dl)
        total_steps = steps_per_epoch * pc.epochs

        best_loss = float("inf")
        global_step = 0
        tic = time.time()

        optim.zero_grad(set_to_none=True)
        for epoch in range(1, pc.epochs + 1):
            epoch_step = 0
            for batch in train_dl:
                with accelerator.accumulate(model):
                    epoch_step += 1
                    outputs = model(
                        input_ids=batch["input_ids"],
                        labels=batch["labels"],
                    )
                    loss = outputs.loss
                    accelerator.backward(loss)

                    if accelerator.sync_gradients:
                        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0, norm_type=2.0)
                        optim.step()
                        sched.step()
                        optim.zero_grad()

                    if accelerator.sync_gradients:
                        global_step += 1
                        if global_step % pc.logging_steps == 0:
                            speed = pc.logging_steps / (time.time() - tic)
                            left = total_steps - global_step
                            eta = second2time(int(left / speed)) if speed else "∞"
                            pct = global_step / total_steps * 100
                            text = (f"[E{epoch}] "
                                    f"step {epoch_step}/{steps_per_epoch} | "
                                    f"global {global_step}/{total_steps} ({pct:5.2f}%) | "
                                    f"loss {loss.item():.4f} | {speed:.2f} step/s | ETA {eta} s")
                            if writer is not None:
                                writer.add_scalar("train/loss", loss.item(), global_step)
                                writer.add_scalar("train/speed", speed, global_step)
                                writer.add_scalar("train/pct", pct, global_step)
                            print(text)
                            tic = time.time()

                        if global_step % pc.save_freq == 0:
                            model.eval()
                            eval_loss_local = evaluate(model, dev_dl)
                            model.train()

                            loss_tensor = torch.tensor([eval_loss_local], device=accelerator.device)
                            eval_loss = accelerator.gather(loss_tensor).mean().item()

                            accelerator.wait_for_everyone()

                            if accelerator.is_main_process and eval_loss < best_loss:
                                print("[LOG] 开始保存 best checkpoint ...")
                                best_loss = eval_loss
                                base_path = os.path.join(pc.save_dir, "best")
                                unwrapped = accelerator.unwrap_model(model)

                                if pc.use_ptuning:
                                    ptune_dir = os.path.join(base_path, "ptuning")
                                    print(f"[LOG] 开始保存 Prefix Encoder 到 {ptune_dir}")
                                    os.makedirs(ptune_dir, exist_ok=True)
                                    torch.save(
                                        unwrapped.transformer.prefix_encoder.state_dict(),
                                        os.path.join(ptune_dir, "prefix_encoder.bin")
                                    )
                                    print(f"[LOG] Prefix Encoder 保存完成")

                                if pc.use_lora:
                                    lora_dir = os.path.join(base_path, "lora")
                                    print(f"[LOG] 开始保存 LoRA Adapter 到 {lora_dir}")
                                    os.makedirs(lora_dir, exist_ok=True)
                                    accelerator.unwrap_model(model).save_pretrained(lora_dir)
                                    tok.save_pretrained(lora_dir)
                                    print(f"[LOG] LoRA Adapter 保存完成")

                                merged_dir = os.path.join(base_path, "merged")
                                print(f"[LOG] 开始合并并保存完整模型到 {merged_dir}")
                                os.makedirs(merged_dir, exist_ok=True)

                                from peft import PeftModel
                                if pc.use_lora:
                                    base_model = AutoModel.from_pretrained(
                                        pc.pre_model,
                                        trust_remote_code=True,
                                        config=unwrapped.config
                                    )
                                    peft_model = PeftModel.from_pretrained(
                                        model=base_model,
                                        model_id=lora_dir
                                    )
                                    merged_model = peft_model.merge_and_unload()
                                else:
                                    merged_model = unwrapped

                                merged_model.save_pretrained(merged_dir)
                                tok.save_pretrained(merged_dir)
                                print(f"[LOG] 完整模型保存完成")
                                text1 = f"✔ Saved best checkpoint to {merged_dir} (eval loss={eval_loss:.4f})"
                                if writer is not None:
                                    writer.add_text("dev/log", text1, global_step)
                                print(text1)

                            accelerator.wait_for_everyone()

    except Exception as e:
        if accelerator.is_main_process:
            print("训练过程中发生异常：", e)
            traceback.print_exc()
        raise
    finally:
        if writer is not None:
            writer.close()

if __name__ == "__main__":
    main()
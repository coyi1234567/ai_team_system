# -*- coding:utf-8 -*-
import os  # 操作系统接口，用于处理文件路径等
import time  # 时间管理，用于测量推理耗时
import torch  # PyTorch 核心库，用于张量运算和模型推理

from transformers import AutoTokenizer, AutoModel  # Transformers 库的模型和分词器接口

# 预测函数：传入模型、分词器，以及指令和输入文本，返回模型生成的回答

def inference(
        model,
        tokenizer,
        instruction: str,
        sentence: str
    ) -> str:
    """
    模型推理函数

    Args:
        model: 加载并放在指定设备上的预训练/微调模型
        tokenizer: 对应模型的分词器，用于文本的编码和解码
        instruction (str): 人类编写的指令，指导模型完成特定任务
        sentence (str): 具体输入内容，可选，如果为空则只使用指令

    Returns:
        str: 模型生成的回答文本（不包含指令前缀）
    """
    # 在推理阶段不需要计算梯度，节省显存与计算
    with torch.no_grad():
        # 构造输入字符串：先写 Instruction
        input_text = f"Instruction: {instruction}\n"
        # 如果有额外的输入句子，就加入 Input 标签
        if sentence:
            input_text += f"Input: {sentence}\n"
        # 最后在 Answer 标签后等待模型生成
        input_text += "Answer: "

        # 使用 tokenizer 将输入编码成模型能接受的张量形式，返回 pytorch tensors
        batch = tokenizer(input_text, return_tensors="pt")

        # 将编码后的 input_ids 移动到模型所在设备，然后调用 generate 生成新 tokens
        out = model.generate(
            input_ids=batch["input_ids"].to(device),
            max_new_tokens=max_new_tokens,  # 生成的最大新 token 数
            temperature=0  # temperature=0 表示贪心解码
        )

        # 把生成的 token 序列解码回文本
        out_text = tokenizer.decode(out[0], skip_special_tokens=True)
        # 从解码后的文本中分割出 Answer: 之后的部分作为最终回答
        print("=== raw out_text ===\n", out_text)
        answer = out_text.split('Answer: ')[-1].strip()
        return answer


if __name__ == '__main__':
    # 如果作为脚本直接运行，则执行下面的示例推理流程
    from rich import print  # 引入 rich 库的打印，用于美化控制台输出

    # 推理时使用的设备，可以是 'cuda:0'、'cpu'、'mps:0' 等，根据硬件环境选择
    device = 'cuda:1'
    # 限制每次推理生成的最大 token 数量
    max_new_tokens = 300
    # 微调后检查点的模型路径
    # model_path = "/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/checkpoints/ptune/model_800"
    model_path = "/home/ubuntu/data/pycharm_project_377/GPU_32_pythonProject/LLM/ptune_chatglm/checkpoints/train_half/best/merged"

    # 加载分词器，使用模型保存目录下的 tokenizer 配置
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True  # 允许加载自定义模型代码
    )

    # 加载模型，并切换到半精度以节省显存，然后移动到指定设备
    model = AutoModel.from_pretrained(
        model_path,
        trust_remote_code=True
    ).half().to(device)

    # 示例样本列表，每个样本包含 instruction 和 input 两部分
    samples = [
        {
            'instruction': "现在你是一个非常厉害的SPO抽取器。",
            'input': (
                "下面这句中包含了哪些三元组，用json列表的形式回答，不要输出除json外的其他答案。\n\n"
                "73获奖记录人物评价：黄磊是一个特别幸运的演员，拍第一部戏就碰到了导演陈凯歌，"
                "而且在他的下一部电影《夜半歌声》中演对手戏的张国荣、吴倩莲、黎明等都是著名的港台演员。"
            ),
        },
        {
            'instruction': "你现在是一个很厉害的阅读理解器，严格按照人类指令进行回答。",
            'input': (
                "下面子中的主语是什么类别，输出成列表形式。\n\n"
                "第N次入住了，就是方便去客户那里哈哈。还有啥说的"
            )
        }
    ]

    # 记录推理开始时间
    start = time.time()
    # 对每个样本执行 inference，并打印结果
    for i, sample in enumerate(samples):
        res = inference(
            model,
            tokenizer,
            sample['instruction'],
            sample['input']
        )
        print(f'res {i}:')
        print(res)

    # 打印总耗时
    print(f'Used {round(time.time() - start, 2)}s.')
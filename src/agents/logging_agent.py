import os
import sys
import datetime
import json as _json
from crewai import Agent, Task
from pydantic import PrivateAttr
from typing import Optional

class LoggingAgent(Agent):
    """
    带有自动日志、产物落盘、代码块提取能力的Agent基类。
    - 自动将输入输出日志写入llm_log.txt
    - 自动将产物/代码块落盘到对应文件
    - 强制结构化产出，支持多文件和action
    """
    _project_id: str = PrivateAttr(default="")
    _project_dir: str = PrivateAttr(default="")

    def __init__(self, *args, project_id: str = "", project_dir: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._project_id = project_id or ""
        self._project_dir = project_dir or ""

    def execute_task(self, task: Task, context: Optional[str] = None, tools=None):
        task_prompt = task.prompt()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        role = self.role
        task_name = getattr(task, 'name', 'unknown')
        # === 自动注入目标文件内容 ===
        file_path = None
        if context and isinstance(context, str) and '__file_path__:' in context:
            # 约定context中包含__file_path__:xxx，自动注入
            for line in context.splitlines():
                if line.startswith('__file_path__:'):
                    file_path = line.replace('__file_path__:', '').strip()
                    break
        if file_path:
            file_content = self._read_file_content(file_path)
            if file_content:
                context = f"【当前{file_path}内容】\n{file_content}\n\n" + (context or "")
        # 控制台打印输入
        print(f"\n================ LLM调用日志 ================")
        print(f"[{now}] 角色: {role} 任务: {task_name}")
        print(f"【输入Prompt】\n{task_prompt}")
        if context:
            print(f"【上下文】\n{context}")
        sys.stdout.flush()
        # 调用原始Agent逻辑
        result = super().execute_task(task, context, tools)
        # 控制台打印输出
        print(f"【输出Result】\n{result}")
        print(f"============================================\n")
        sys.stdout.flush()
        # 日志落盘
        if self._project_dir:
            log_path = os.path.join(self._project_dir, 'llm_log.txt')
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"[{now}] 角色: {role} 任务: {task_name}\n")
                f.write(f"【输入Prompt】\n{task_prompt}\n")
                if context:
                    f.write(f"【上下文】\n{context}\n")
                f.write(f"【输出Result】\n{result}\n")
                f.write(f"--------------------------------------------\n")
        # === 自动产出落盘机制（结构化产出） ===
        if self._project_dir and isinstance(self._project_dir, str) and self._project_dir.strip() != "" and task_name:
            try:
                # 尝试解析结构化JSON产出
                files = _json.loads(result) if isinstance(result, str) else result
                if isinstance(files, dict):
                    files = [files]
                for file_obj in files:
                    self._save_file_by_action(file_obj)
            except Exception as e:
                print(f"[LoggingAgent] 结构化产出解析失败，回退到原始代码块提取: {e}")
                self._extract_and_write_code_blocks(result)
        return result

    def _save_file_by_action(self, file_obj):
        """根据action参数保存文件，支持create/replace/append/insert/delete"""
        file_path = file_obj.get("file_path")
        content = file_obj.get("content", "")
        action = file_obj.get("action", "replace")
        if not file_path:
            return
        abs_path = os.path.join(self._project_dir, file_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        if action == "replace" or action == "create":
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
        elif action == "append":
            with open(abs_path, 'a', encoding='utf-8') as f:
                f.write(content)
        elif action == "insert":
            # 简单插入到文件开头
            old = ""
            if os.path.exists(abs_path):
                with open(abs_path, 'r', encoding='utf-8') as f:
                    old = f.read()
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content + '\n' + old)
        elif action == "delete":
            if os.path.exists(abs_path):
                os.remove(abs_path)

    def _read_file_content(self, file_path: str) -> str:
        abs_path = os.path.join(self._project_dir, file_path)
        if os.path.exists(abs_path):
            with open(abs_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def _extract_block(self, text: str, block_name: str) -> Optional[str]:
        """提取如```Dockerfile ...```或```block_name ...```的内容"""
        import re
        pattern = rf'```{block_name}([\s\S]*?)```'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _extract_and_write_code_blocks(self, text: str):
        """自动提取并写入代码块到对应文件"""
        import re
        code_blocks = re.findall(r'```(\w+)?\n([\s\S]*?)```', text)
        for lang, code in code_blocks:
            ext_map = {
                'python': '.py', 'js': '.js', 'javascript': '.js', 'ts': '.ts', 'java': '.java',
                'go': '.go', 'c': '.c', 'cpp': '.cpp', 'html': '.html', 'css': '.css',
                'sh': '.sh', 'bash': '.sh', 'Dockerfile': 'Dockerfile',
            }
            ext = ext_map.get(lang.lower(), '.txt') if lang else '.txt'
            # 文件名自动递增防止覆盖
            base = lang if lang else 'code'
            idx = 1
            while True:
                fname = f'{base}_{idx}{ext}' if ext != 'Dockerfile' else 'Dockerfile'
                fpath = os.path.join(self._project_dir, fname)
                if not os.path.exists(fpath):
                    break
                idx += 1
            # Dockerfile 特殊处理
            if ext == 'Dockerfile':
                fpath = os.path.join(self._project_dir, 'Dockerfile')
            os.makedirs(os.path.dirname(fpath), exist_ok=True)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(code.strip() + '\n') 
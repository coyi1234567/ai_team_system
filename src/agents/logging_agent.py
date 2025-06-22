import os
import sys
import datetime
from crewai import Agent, Task
from pydantic import PrivateAttr
from typing import Optional

class LoggingAgent(Agent):
    """
    带有自动日志、产物落盘、代码块提取能力的Agent基类。
    - 自动将输入输出日志写入llm_log.txt
    - 自动将产物/代码块落盘到对应文件
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
        # === 自动产出落盘机制 ===
        if self._project_dir and isinstance(self._project_dir, str) and self._project_dir.strip() != "" and task_name:
            project_dir: str = self._project_dir
            name_map = {
                'requirement_analysis': '需求分析.md',
                'technical_design': '技术设计.md',
                'ui_design': 'UI设计.md',
                'algorithm_design': '算法设计.md',
                'frontend_development': 'frontend/前端开发.md',
                'backend_development': 'backend/后端开发.md',
                'data_analysis': '数据分析报告.md',
                'testing': '测试报告.md',
                'deployment': '部署文档.md',
                'documentation': '项目文档.md',
                'acceptance': '项目验收报告.md',
            }
            out_file = name_map.get(task_name, f'{task_name}.md')
            if out_file and isinstance(out_file, str):
                out_path = os.path.join(project_dir, out_file)
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                if 'Dockerfile' in result:
                    dockerfile_path = os.path.join(project_dir, 'Dockerfile')
                    docker_content = self._extract_block(result, 'Dockerfile')
                    if docker_content:
                        with open(dockerfile_path, 'w', encoding='utf-8') as f:
                            f.write(docker_content.strip() + '\n')
                self._extract_and_write_code_blocks(result)
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(result.strip() + '\n')
        return result

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
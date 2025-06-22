import re
import subprocess
from typing import Tuple

def extract_error_summary(log: str) -> str:
    """自动提取日志中的关键报错信息"""
    lines = log.splitlines()
    error_lines = [l for l in lines if re.search(r'(error|exception|fail|traceback|not found|denied|refused|exit code)', l, re.I)]
    return '\n'.join(error_lines[-10:]) if error_lines else '\n'.join(lines[-10:])

def run_command_with_log(cmd: str, cwd: str, log_path: str) -> Tuple[int, str, str]:
    """执行命令并记录日志，返回(exitcode, stdout, stderr)"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=120)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[CMD] {cmd}\n[OUT]\n{result.stdout}\n[ERR]\n{result.stderr}\n")
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[CMD] {cmd}\n[EXCEPTION] {str(e)}\n")
        return -1, '', str(e) 
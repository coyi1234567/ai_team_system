import os
from typing import List, Optional
from crewai import Crew, Task, Agent
from agents import LoggingAgent
from tools.mcp_tool import MCPTool
from utils.log_utils import extract_error_summary, run_command_with_log
from mcp_server import MCPServer

class AiTeamCrew:
    def __init__(self, project_id: Optional[str] = None, project_dir: Optional[str] = None):
        pid = str(project_id) if project_id is not None else ""
        pdir = str(project_dir) if project_dir is not None else ""
        self.project_id = pid
        self.project_dir = pdir
        self.mcp_tool = MCPTool(workspace_path=project_dir)
        # 这里可根据实际业务动态生成Agent
        self.agents = []
        self.crew = None

    def auto_execute_and_fix(self, file_to_run: str, agent_list: List[Agent], run_type: str = 'python', custom_cmd: Optional[str] = None, use_mcp: bool = False, max_retry: int = 3) -> bool:
        log_path = os.path.join(self.project_dir, 'auto_exec_log.txt')
        mcp = MCPServer(workspace_path=self.project_dir) if use_mcp else None
        for attempt in range(1, max_retry+1):
            # 构造命令
            if run_type == 'python':
                cmd = f'python {file_to_run}'
            elif run_type == 'shell':
                cmd = f'bash {file_to_run}'
            elif run_type == 'npm':
                cmd = f'npm run {file_to_run}'
            elif run_type == 'pytest':
                cmd = f'pytest {file_to_run or ""}'
            elif run_type == 'docker':
                cmd = f'docker build -t tempimg . && docker run --rm tempimg'
            elif run_type == 'custom' and custom_cmd:
                cmd = custom_cmd
            else:
                return False
            # 执行命令
            if use_mcp and mcp:
                if run_type in ['python', 'shell', 'pytest']:
                    result = mcp.execute_code(os.path.join(self.project_dir, file_to_run))
                    exitcode = getattr(result, 'exit_code', 1)
                    out = getattr(result, 'output', '')
                    err = getattr(result, 'error', '')
                    logs = out + '\n' + err
                elif run_type == 'docker':
                    image_name = f"{os.path.basename(self.project_dir)}:latest"
                    build_result = mcp.build_docker_image(self.project_dir, image_name)
                    logs = getattr(build_result, 'logs', '')
                    if not build_result.success:
                        exitcode = 1
                        out = ''
                        err = build_result.message
                    else:
                        run_result = mcp.run_docker_container(image_name, f"{os.path.basename(self.project_dir)}-container")
                        logs += '\n' + getattr(run_result, 'logs', '')
                        exitcode = 0 if run_result.success else 1
                        out = run_result.logs
                        err = run_result.message if not run_result.success else ''
                else:
                    exitcode, out, err, logs = 1, '', 'MCP暂不支持该类型', 'MCP暂不支持该类型'
            else:
                exitcode, out, err = run_command_with_log(cmd, self.project_dir, log_path)
                logs = out + '\n' + err
            # 日志归档
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"[SUMMARY_ATTEMPT_{attempt}]\n{extract_error_summary(logs)}\n")
            if exitcode == 0:
                return True
            # 失败时多Agent多轮修正
            summary = extract_error_summary(logs)
            fix_prompt = f"自动执行命令失败，日志摘要如下：\n{summary}\n请修正产出，确保下次执行通过。"
            for agent in agent_list:
                fix_task = Task(name=f"auto_fix_{run_type}_attempt{attempt}", description=fix_prompt, expected_output="请修正产出代码/配置。", agent=agent)
                agent.execute_task(fix_task, context=fix_prompt, tools=agent.tools)
        return False

    def kickoff(self, inputs: dict):
        # 这里只保留主流程调度，具体Agent/Task链路可根据业务自定义
        context = dict(inputs) if inputs else {}
        project_dir = self.project_dir
        # 示例：自动执行main.py
        main_py = os.path.join(project_dir, 'main.py')
        if os.path.exists(main_py):
            self.auto_execute_and_fix(
                file_to_run='main.py',
                agent_list=self.agents,
                run_type='python', use_mcp=True, max_retry=3)
        # 其它类型可按需扩展
        return {} 
from typing import Optional, Dict, Any
from crewai.tools import BaseTool
from mcp_server import MCPServer
from pydantic import PrivateAttr
import logging

logger = logging.getLogger(__name__)

class MCPTool(BaseTool):
    """
    Agent工具：封装MCPServer常用操作，便于Agent链路调用
    
    支持的操作：
    - write_code: 生成并写入代码文件
    - read_file: 读取文件内容
    - execute_code: 执行代码文件
    - run_shell_command: 执行shell命令
    - deploy_project: 部署项目到Docker
    - build_image: 构建Docker镜像
    - run_container: 运行Docker容器
    """

    _mcp: MCPServer = PrivateAttr()

    def __init__(self, workspace_path: Optional[str] = None, **kwargs):
        super().__init__(
            name="MCPTool",
            description="""MCP协议工具，支持代码生成、文件读写、命令执行等操作。
            
            参数格式：
            - write_code: {"file_path": "文件路径", "requirements": "需求描述"}
            - read_file: {"file_path": "文件路径"}
            - execute_code: {"file_path": "文件路径", "args": ["参数1", "参数2"]}
            - run_shell_command: {"cmd": "shell命令"}
            - deploy_project: {"project_path": "项目路径", "language": "python", "port": 8000}
            - build_image: {"project_path": "项目路径", "image_name": "镜像名称"}
            - run_container: {"image_name": "镜像名称", "container_name": "容器名称", "port": 8000}
            
            返回值：
            - 成功：返回操作结果和详细信息
            - 失败：返回错误信息和建议的修复方案
            """,
            **kwargs
        )
        self._mcp = MCPServer(workspace_path=workspace_path)
        logger.info(f"MCPTool初始化完成，工作目录: {workspace_path}")

    def write_code(self, file_path: str, requirements: str) -> str:
        """生成并写入代码到文件"""
        try:
            logger.info(f"开始生成代码: {file_path}")
            result = self._mcp.generate_code(requirements, file_path)
            if result.success:
                logger.info(f"代码生成成功: {file_path}")
                return f"✅ 代码已成功生成并写入到 {file_path}\n文件大小: {len(result.content)} 字符"
            else:
                logger.error(f"代码生成失败: {result.message}")
                return f"❌ 代码生成失败: {result.message}\n建议: 检查需求描述是否清晰，文件路径是否有效"
        except Exception as e:
            logger.error(f"代码生成异常: {e}")
            return f"❌ 代码生成异常: {str(e)}\n建议: 检查系统环境和权限设置"

    def read_file(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            logger.info(f"开始读取文件: {file_path}")
            result = self._mcp.read_file(file_path)
            if result.success:
                logger.info(f"文件读取成功: {file_path}")
                return f"文件内容 ({len(result.content)} 字符):\n{result.content}"
            else:
                logger.error(f"文件读取失败: {result.message}")
                return f"❌ 文件读取失败: {result.message}\n建议: 检查文件是否存在，路径是否正确"
        except Exception as e:
            logger.error(f"文件读取异常: {e}")
            return f"❌ 文件读取异常: {str(e)}\n建议: 检查文件权限和系统状态"

    def execute_code(self, file_path: str, args: Optional[list] = None) -> str:
        """执行代码文件"""
        try:
            logger.info(f"开始执行代码: {file_path}, 参数: {args}")
            result = self._mcp.execute_code(file_path, args)
            if result.success:
                logger.info(f"代码执行成功: {file_path}")
                return f"✅ 代码执行成功 (退出码: {result.exit_code})\n输出:\n{result.output}"
            else:
                logger.error(f"代码执行失败: {result.message}")
                return f"❌ 代码执行失败: {result.message}\n错误输出:\n{result.error}\n建议: 检查代码语法、依赖和环境配置"
        except Exception as e:
            logger.error(f"代码执行异常: {e}")
            return f"❌ 代码执行异常: {str(e)}\n建议: 检查文件权限和系统环境"

    def run_shell_command(self, cmd: str) -> str:
        """执行shell命令"""
        try:
            logger.info(f"开始执行shell命令: {cmd}")
            result = self._mcp.run_shell_command(cmd)
            if result.success:
                logger.info(f"Shell命令执行成功: {cmd}")
                return f"✅ Shell命令执行成功 (退出码: {result.exit_code})\n输出:\n{result.output}"
            else:
                logger.error(f"Shell命令执行失败: {result.message}")
                return f"❌ Shell命令执行失败: {result.message}\n错误输出:\n{result.error}\n建议: 检查命令语法、权限和环境变量"
        except Exception as e:
            logger.error(f"Shell命令执行异常: {e}")
            return f"❌ Shell命令执行异常: {str(e)}\n建议: 检查系统权限和命令可用性"
        
    def _run(self, tool_input: str) -> str:
        """BaseTool要求的_run方法 - 智能解析输入并调用相应方法"""
        try:
            # 尝试解析JSON格式的输入
            import json
            try:
                params = json.loads(tool_input)
                action = params.get("action", "")
                
                if action == "write_code":
                    return self.write_code(params.get("file_path", ""), params.get("requirements", ""))
                elif action == "read_file":
                    return self.read_file(params.get("file_path", ""))
                elif action == "execute_code":
                    return self.execute_code(params.get("file_path", ""), params.get("args"))
                elif action == "run_shell_command":
                    return self.run_shell_command(params.get("cmd", ""))
                else:
                    return f"❌ 未知操作: {action}\n支持的操作: write_code, read_file, execute_code, run_shell_command"
                    
            except json.JSONDecodeError:
                # 如果不是JSON格式，返回使用说明
                return f"""MCPTool使用说明:
                
输入格式应为JSON，例如：
{{"action": "write_code", "file_path": "main.py", "requirements": "创建一个简单的Hello World程序"}}
{{"action": "read_file", "file_path": "main.py"}}
{{"action": "execute_code", "file_path": "main.py", "args": ["arg1", "arg2"]}}
{{"action": "run_shell_command", "cmd": "ls -la"}}

当前输入: {tool_input}
"""
        except Exception as e:
            logger.error(f"MCPTool._run异常: {e}")
            return f"❌ MCPTool执行异常: {str(e)}" 
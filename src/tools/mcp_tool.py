from typing import Optional
from crewai.tools import BaseTool
from mcp_server import MCPServer
from pydantic import PrivateAttr

class MCPTool(BaseTool):
    """
    Agent工具：封装MCPServer常用操作，便于Agent链路调用
    """
    
    _mcp: MCPServer = PrivateAttr()

    def __init__(self, workspace_path: Optional[str] = None, **kwargs):
        super().__init__(
            name="MCPTool",
            description="MCP协议工具，支持代码生成、文件读写、命令执行等操作",
            **kwargs
        )
        self._mcp = MCPServer(workspace_path=workspace_path)

    def write_code(self, file_path: str, requirements: str) -> str:
        result = self._mcp.generate_code(requirements, file_path)
        return result.message

    def read_file(self, file_path: str) -> str:
        result = self._mcp.read_file(file_path)
        return result.content if result.success else result.message

    def execute_code(self, file_path: str, args=None) -> str:
        result = self._mcp.execute_code(file_path, args)
        return result.output if result.success else result.error

    def run_shell_command(self, cmd: str) -> str:
        result = self._mcp.run_shell_command(cmd)
        return result.output if result.success else result.error
        
    def _run(self, tool_input: str) -> str:
        """BaseTool要求的_run方法"""
        # 这里可以根据tool_input解析出具体的操作
        # 暂时返回一个默认响应
        return f"MCPTool执行: {tool_input}" 
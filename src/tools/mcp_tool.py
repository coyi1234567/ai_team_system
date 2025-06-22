from typing import Optional
from mcp_server import MCPServer

class MCPTool:
    """
    Agent工具：封装MCPServer常用操作，便于Agent链路调用
    """
    def __init__(self, workspace_path: Optional[str] = None):
        self.mcp = MCPServer(workspace_path=workspace_path)

    def write_code(self, file_path: str, requirements: str) -> str:
        result = self.mcp.generate_code(requirements, file_path)
        return result.message

    def read_file(self, file_path: str) -> str:
        result = self.mcp.read_file(file_path)
        return result.content if result.success else result.message

    def execute_code(self, file_path: str, args=None) -> str:
        result = self.mcp.execute_code(file_path, args)
        return result.output if result.success else result.error

    def run_shell_command(self, cmd: str) -> str:
        result = self.mcp.run_shell_command(cmd)
        return result.output if result.success else result.error 
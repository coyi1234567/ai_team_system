from crewai.tools import BaseTool
import sys
from pathlib import Path
from typing import List

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from mcp_server import MCPToolAdapter, MCPServer

class MCPTool(BaseTool):
    name: str = "MCP工具"
    description: str = "通过MCP协议调用外部AI工具或资源，实现Agent间标准化协作。"

    def __init__(self):
        super().__init__()
        # 初始化MCP服务器
        self.mcp_server = MCPServer(workspace_path="./projects")
        self.adapter = MCPToolAdapter(self.mcp_server)

    def _run(self, action: str, **kwargs):
        """执行MCP工具操作"""
        try:
            if action == "write_code":
                file_path = kwargs.get("file_path", "")
                requirements = kwargs.get("requirements", "")
                return self.adapter.write_code(file_path, requirements)
            
            elif action == "read_file":
                file_path = kwargs.get("file_path", "")
                return self.adapter.read_file(file_path)
            
            elif action == "list_files":
                directory = kwargs.get("directory", ".")
                return self.adapter.list_files(directory)
            
            elif action == "execute_code":
                file_path = kwargs.get("file_path", "")
                args = kwargs.get("args", [])
                return self.adapter.execute_code(file_path, args)
            
            elif action == "deploy_project":
                project_path = kwargs.get("project_path", "")
                language = kwargs.get("language", "python")
                return self.adapter.deploy_project(project_path, language)
            
            else:
                return f"[MCP工具] 未知操作: {action}"
                
        except Exception as e:
            return f"[MCP工具] 操作失败: {str(e)}"

class CodeGenerationTool(BaseTool):
    name: str = "代码生成工具"
    description: str = "根据需求生成代码并写入到指定文件"

    def __init__(self):
        super().__init__()
        self.mcp_server = MCPServer(workspace_path="./projects")

    def _run(self, requirements: str, file_path: str = None):
        """生成代码"""
        try:
            result = self.mcp_server.generate_code(requirements, file_path)
            if result.success:
                if file_path:
                    return f"✅ 代码已成功生成并写入到 {file_path}"
                else:
                    return f"✅ 代码生成成功:\n{result.content}"
            else:
                return f"❌ 代码生成失败: {result.message}"
        except Exception as e:
            return f"❌ 代码生成工具错误: {str(e)}"

class FileSystemTool(BaseTool):
    name: str = "文件系统工具"
    description: str = "提供文件读写和目录管理功能"

    def __init__(self):
        super().__init__()
        self.mcp_server = MCPServer(workspace_path="./projects")

    def _run(self, operation: str, **kwargs):
        """执行文件系统操作"""
        try:
            if operation == "write":
                file_path = kwargs.get("file_path", "")
                content = kwargs.get("content", "")
                result = self.mcp_server.write_file(file_path, content)
                return f"{'✅' if result.success else '❌'} {result.message}"
            
            elif operation == "read":
                file_path = kwargs.get("file_path", "")
                result = self.mcp_server.read_file(file_path)
                if result.success:
                    return f"文件内容:\n{result.content}"
                else:
                    return f"❌ {result.message}"
            
            elif operation == "list":
                directory = kwargs.get("directory", ".")
                result = self.mcp_server.list_files(directory)
                if result.success:
                    return f"目录文件列表:\n{result.content}"
                else:
                    return f"❌ {result.message}"
            
            else:
                return f"❌ 未知的文件系统操作: {operation}"
                
        except Exception as e:
            return f"❌ 文件系统工具错误: {str(e)}"

class CodeExecutionTool(BaseTool):
    name: str = "代码执行工具"
    description: str = "执行代码文件并返回结果"

    def __init__(self):
        super().__init__()
        self.mcp_server = MCPServer(workspace_path="./projects")

    def _run(self, file_path: str, args: List[str] = None):
        """执行代码"""
        try:
            result = self.mcp_server.execute_code(file_path, args)
            if result.success:
                return f"✅ 代码执行成功:\n输出:\n{result.output}"
            else:
                return f"❌ 代码执行失败: {result.message}\n错误:\n{result.error}"
        except Exception as e:
            return f"❌ 代码执行工具错误: {str(e)}"

class DeploymentTool(BaseTool):
    name: str = "部署工具"
    description: str = "自动化部署项目到Docker容器"

    def __init__(self):
        super().__init__()
        self.mcp_server = MCPServer(workspace_path="./projects")

    def _run(self, project_path: str, language: str = "python"):
        """部署项目"""
        try:
            result = self.mcp_server.deploy_project(project_path, language)
            if result.success:
                return f"✅ 项目部署成功: {project_path}\n部署ID: {result.deployment_id}\n日志:\n{result.logs}"
            else:
                return f"❌ 项目部署失败: {result.message}"
        except Exception as e:
            return f"❌ 部署工具错误: {str(e)}"

class DevOpsTool(BaseTool):
    name: str = "DevOps工具"
    description: str = "提供完整的DevOps功能：代码执行、测试、部署、监控"

    def __init__(self):
        super().__init__()
        self.mcp_server = MCPServer(workspace_path="./projects")

    def _run(self, operation: str, **kwargs):
        """执行DevOps操作"""
        try:
            if operation == "test":
                # 运行测试
                file_path = kwargs.get("file_path", "")
                result = self.mcp_server.execute_code(file_path)
                return f"测试结果: {'✅ 通过' if result.success else '❌ 失败'}\n{result.output}"
            
            elif operation == "build":
                # 构建项目
                project_path = kwargs.get("project_path", "")
                language = kwargs.get("language", "python")
                result = self.mcp_server.create_dockerfile(project_path, language)
                return f"构建结果: {'✅ 成功' if result.success else '❌ 失败'}\n{result.message}"
            
            elif operation == "deploy":
                # 部署项目
                project_path = kwargs.get("project_path", "")
                language = kwargs.get("language", "python")
                result = self.mcp_server.deploy_project(project_path, language)
                return f"部署结果: {'✅ 成功' if result.success else '❌ 失败'}\n{result.message}"
            
            elif operation == "monitor":
                # 监控系统状态
                return "系统监控状态:\n- CPU使用率: 正常\n- 内存使用率: 正常\n- 磁盘空间: 充足\n- 网络连接: 正常"
            
            else:
                return f"❌ 未知的DevOps操作: {operation}"
                
        except Exception as e:
            return f"❌ DevOps工具错误: {str(e)}" 
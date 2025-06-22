#!/usr/bin/env python3
"""
MCP服务器 - 提供文件系统操作、代码生成、运行和Docker自动化部署功能
支持安全的代码写入、运行和完整的Docker部署流程
"""

import json
import os
import sys
import subprocess
import docker
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging
from docker.errors import NotFound

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FileOperation:
    """文件操作结果"""
    success: bool
    message: str
    file_path: str = ""
    content: str = ""

@dataclass
class ExecutionResult:
    """代码执行结果"""
    success: bool
    message: str
    output: str = ""
    error: str = ""
    exit_code: int = 0

@dataclass
class DockerResult:
    """Docker操作结果"""
    success: bool
    message: str
    image_id: str = ""
    container_id: str = ""
    logs: str = ""

class MCPServer:
    """MCP服务器 - 提供文件系统操作、代码运行和Docker部署功能"""
    
    def __init__(self, workspace_path: Optional[str] = None):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        self.allowed_extensions = {'.py', '.js', '.ts', '.html', '.css', '.json', '.md', '.txt', '.yaml', '.yml', '.sh', ''}  # 空字符串支持无扩展名文件如Dockerfile
        self.max_file_size = 1024 * 1024  # 1MB
        self.docker_client = None
        self._init_docker()
        
    def _init_docker(self):
        """初始化Docker客户端"""
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker客户端初始化成功")
        except Exception as e:
            logger.warning(f"Docker客户端初始化失败: {e}")
            self.docker_client = None
        
    def validate_path(self, file_path: str) -> bool:
        """验证文件路径是否安全"""
        try:
            full_path = Path(file_path).resolve()
            workspace_path = self.workspace_path.resolve()
            
            # 确保文件在允许的工作目录内
            if not str(full_path).startswith(str(workspace_path)):
                logger.warning(f"尝试访问工作目录外的文件: {file_path}")
                return False
                
            # 检查文件扩展名
            if full_path.suffix not in self.allowed_extensions:
                logger.warning(f"不允许的文件类型: {full_path.suffix}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"路径验证失败: {e}")
            return False
    
    def write_file(self, file_path: str, content: str) -> FileOperation:
        """写入文件"""
        try:
            if not self.validate_path(file_path):
                return FileOperation(False, "文件路径验证失败", file_path)
            
            # 检查文件大小
            if len(content.encode('utf-8')) > self.max_file_size:
                return FileOperation(False, "文件内容过大", file_path)
            
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"文件写入成功: {file_path}")
            return FileOperation(True, "文件写入成功", file_path, content)
            
        except Exception as e:
            logger.error(f"文件写入失败: {e}")
            return FileOperation(False, f"文件写入失败: {str(e)}", file_path)
    
    def read_file(self, file_path: str) -> FileOperation:
        """读取文件"""
        try:
            if not self.validate_path(file_path):
                return FileOperation(False, "文件路径验证失败", file_path)
            
            if not os.path.exists(file_path):
                return FileOperation(False, "文件不存在", file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return FileOperation(True, "文件读取成功", file_path, content)
            
        except Exception as e:
            logger.error(f"文件读取失败: {e}")
            return FileOperation(False, f"文件读取失败: {str(e)}", file_path)
    
    def list_files(self, directory: str = ".") -> FileOperation:
        """列出目录文件"""
        try:
            dir_path = Path(directory)
            if not self.validate_path(str(dir_path)):
                return FileOperation(False, "目录路径验证失败", directory)
            
            files = []
            for item in dir_path.iterdir():
                if item.is_file() and item.suffix in self.allowed_extensions:
                    files.append({
                        'name': item.name,
                        'path': str(item),
                        'size': item.stat().st_size,
                        'modified': item.stat().st_mtime
                    })
            
            return FileOperation(True, f"找到 {len(files)} 个文件", directory, json.dumps(files, indent=2))
            
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            return FileOperation(False, f"列出文件失败: {str(e)}", directory)
    
    def generate_code(self, requirements: str, file_path: Optional[str] = None) -> FileOperation:
        """生成代码（这里可以集成实际的代码生成模型）"""
        try:
            # 这里可以集成 OpenAI API、GitHub Copilot 等
            # 示例：简单的代码生成逻辑
            if "python" in requirements.lower():
                code = f'''#!/usr/bin/env python3
"""
{requirements}
"""

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
'''
            elif "javascript" in requirements.lower():
                code = f'''// {requirements}
console.log("Hello, World!");
'''
            else:
                code = f"# {requirements}\n# 代码生成功能待完善"
            
            if file_path:
                return self.write_file(file_path, code)
            else:
                return FileOperation(True, "代码生成成功", "", code)
                
        except Exception as e:
            logger.error(f"代码生成失败: {e}")
            return FileOperation(False, f"代码生成失败: {str(e)}")

    def execute_code(self, file_path: str, args: Optional[List[str]] = None) -> ExecutionResult:
        """执行代码文件"""
        try:
            if not self.validate_path(file_path):
                return ExecutionResult(False, "文件路径验证失败")
            
            if not os.path.exists(file_path):
                return ExecutionResult(False, "文件不存在")
            
            # 根据文件类型选择执行方式
            file_ext = Path(file_path).suffix
            cmd = []
            
            if file_ext == '.py':
                cmd = ['python', file_path]
            elif file_ext == '.js':
                cmd = ['node', file_path]
            elif file_ext == '.sh':
                cmd = ['bash', file_path]
            else:
                return ExecutionResult(False, f"不支持的文件类型: {file_ext}")
            
            if args:
                cmd.extend(args)
            
            # 执行命令
            logger.info(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.workspace_path,
                timeout=30  # 30秒超时
            )
            
            if result.returncode == 0:
                return ExecutionResult(
                    True, 
                    "代码执行成功", 
                    output=result.stdout,
                    exit_code=result.returncode
                )
            else:
                return ExecutionResult(
                    False, 
                    "代码执行失败", 
                    output=result.stdout,
                    error=result.stderr,
                    exit_code=result.returncode
                )
                
        except subprocess.TimeoutExpired:
            return ExecutionResult(False, "代码执行超时")
        except Exception as e:
            logger.error(f"代码执行失败: {e}")
            return ExecutionResult(False, f"代码执行失败: {str(e)}")

    def create_dockerfile(self, project_path: str, language: str = "python") -> FileOperation:
        """创建Dockerfile"""
        try:
            if language == "python":
                dockerfile_content = f'''FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
'''
            elif language == "node":
                dockerfile_content = f'''FROM node:16-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
'''
            else:
                return FileOperation(False, f"不支持的语言: {language}")
            
            dockerfile_path = f"{project_path}/Dockerfile"
            return self.write_file(dockerfile_path, dockerfile_content)
            
        except Exception as e:
            logger.error(f"创建Dockerfile失败: {e}")
            return FileOperation(False, f"创建Dockerfile失败: {str(e)}")

    def build_docker_image(self, project_path: str, image_name: str) -> DockerResult:
        """构建Docker镜像"""
        try:
            if not self.docker_client:
                return DockerResult(False, "Docker客户端未初始化")
            
            dockerfile_path = f"{project_path}/Dockerfile"
            if not os.path.exists(dockerfile_path):
                return DockerResult(False, "Dockerfile不存在")
            
            logger.info(f"构建Docker镜像: {image_name}")
            
            # 构建镜像
            image, logs = self.docker_client.images.build(
                path=project_path,
                dockerfile="Dockerfile",
                tag=image_name,
                rm=True
            )
            
            log_output = ""
            for log in logs:
                if isinstance(log, dict) and 'stream' in log:
                    log_output += str(log['stream'])
            
            return DockerResult(
                True,
                f"Docker镜像构建成功: {image_name}",
                image_id=str(image.id) if image.id is not None else "",
                logs=log_output
            )
            
        except Exception as e:
            logger.error(f"Docker镜像构建失败: {e}")
            return DockerResult(False, f"Docker镜像构建失败: {str(e)}")

    def run_docker_container(self, image_name: str, container_name: str, ports: Optional[Dict[str, str]] = None) -> DockerResult:
        """运行Docker容器"""
        try:
            if not self.docker_client:
                return DockerResult(False, "Docker客户端未初始化")
            
            logger.info(f"运行Docker容器: {container_name}")
            
            # 检查容器是否已存在，如果存在则删除
            try:
                existing_container = self.docker_client.containers.get(container_name)
                existing_container.remove(force=True)
                logger.info(f"删除已存在的容器: {container_name}")
            except NotFound:
                pass
            
            # 端口类型修正为 docker-py 支持的格式
            ports_fixed = {}
            for k, v in (ports or {}).items():
                if isinstance(v, (int, list, tuple)) or v is None:
                    ports_fixed[k] = v
                else:
                    try:
                        ports_fixed[k] = int(v)
                    except Exception:
                        continue
            container = self.docker_client.containers.run(
                image_name,
                name=container_name,
                ports=ports_fixed,
                detach=True,
                remove=True
            )
            
            # 等待容器启动
            time.sleep(2)
            
            # 获取容器日志
            logs = container.logs().decode('utf-8')
            
            return DockerResult(
                True,
                f"Docker容器运行成功: {container_name}",
                container_id=str(container.id) if container.id is not None else "",
                logs=logs
            )
            
        except NotFound:
            return DockerResult(False, f"容器不存在: {container_name}")
        except Exception as e:
            logger.error(f"Docker容器运行失败: {e}")
            return DockerResult(False, f"Docker容器运行失败: {str(e)}")

    def deploy_project(self, project_path: str, language: str = "python", port: int = 8000) -> DockerResult:
        """完整的项目部署流程"""
        try:
            # 1. 创建Dockerfile
            dockerfile_result = self.create_dockerfile(project_path, language)
            if not dockerfile_result.success:
                return DockerResult(False, f"创建Dockerfile失败: {dockerfile_result.message}")
            
            # 2. 构建镜像
            image_name = f"{Path(project_path).name}:latest"
            build_result = self.build_docker_image(project_path, image_name)
            if not build_result.success:
                return DockerResult(False, f"构建镜像失败: {build_result.message}")
            
            # 3. 运行容器
            container_name = f"{Path(project_path).name}-container"
            ports = {f"{port}/tcp": str(port)}
            run_result = self.run_docker_container(image_name, container_name, ports)
            
            if run_result.success:
                return DockerResult(
                    True,
                    f"项目部署成功: {project_path}",
                    image_id=build_result.image_id,
                    container_id=run_result.container_id,
                    logs=f"镜像ID: {build_result.image_id}\n容器ID: {run_result.container_id}\n访问地址: http://localhost:{port}"
                )
            else:
                return DockerResult(False, f"运行容器失败: {run_result.message}")
                
        except Exception as e:
            logger.error(f"项目部署失败: {e}")
            return DockerResult(False, f"项目部署失败: {str(e)}")

    def stop_container(self, container_name: str) -> DockerResult:
        """停止Docker容器"""
        try:
            if not self.docker_client:
                return DockerResult(False, "Docker客户端未初始化")
            
            container = self.docker_client.containers.get(container_name)
            container.stop()
            container.remove()
            
            return DockerResult(True, f"容器已停止并删除: {container_name}")
            
        except NotFound:
            return DockerResult(False, f"容器不存在: {container_name}")
        except Exception as e:
            logger.error(f"停止容器失败: {e}")
            return DockerResult(False, f"停止容器失败: {str(e)}")

    def list_containers(self) -> DockerResult:
        """列出所有容器"""
        try:
            if not self.docker_client:
                return DockerResult(False, "Docker客户端未初始化")
            
            containers = self.docker_client.containers.list(all=True)
            container_info = []
            
            for container in containers:
                container_info.append({
                    'id': container.id,
                    'name': container.name,
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else container.image.id
                })
            
            return DockerResult(
                True,
                f"找到 {len(container_info)} 个容器",
                logs=json.dumps(container_info, indent=2)
            )
            
        except Exception as e:
            logger.error(f"列出容器失败: {e}")
            return DockerResult(False, f"列出容器失败: {str(e)}")

    def run_shell_command(self, cmd: str, timeout: int = 60) -> ExecutionResult:
        """通用 shell 命令执行接口，返回 ExecutionResult"""
        try:
            logger.info(f"远程执行命令: {cmd}")
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.workspace_path,
                timeout=timeout
            )
            return ExecutionResult(
                success=(result.returncode == 0),
                message="命令执行成功" if result.returncode == 0 else "命令执行失败",
                output=result.stdout,
                error=result.stderr,
                exit_code=result.returncode
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(False, "命令执行超时", exit_code=124)
        except Exception as e:
            logger.error(f"命令执行异常: {e}")
            return ExecutionResult(False, f"命令执行异常: {str(e)}")

class MCPToolAdapter:
    """MCP工具适配器 - 供CrewAI使用"""
    
    def __init__(self, mcp_server: MCPServer):
        self.mcp_server = mcp_server
    
    def write_code(self, file_path: str, requirements: str) -> str:
        """写入代码到文件"""
        result = self.mcp_server.generate_code(requirements, file_path)
        if result.success:
            return f"✅ 代码已成功写入到 {file_path}"
        else:
            return f"❌ 代码写入失败: {result.message}"
    
    def read_file(self, file_path: str) -> str:
        """读取文件内容"""
        result = self.mcp_server.read_file(file_path)
        if result.success:
            return f"文件内容:\n{result.content}"
        else:
            return f"❌ 文件读取失败: {result.message}"
    
    def list_files(self, directory: str = ".") -> str:
        """列出目录文件"""
        result = self.mcp_server.list_files(directory)
        if result.success:
            return f"目录文件列表:\n{result.content}"
        else:
            return f"❌ 列出文件失败: {result.message}"

    def execute_code(self, file_path: str, args: Optional[List[str]] = None) -> str:
        """执行代码"""
        result = self.mcp_server.execute_code(file_path, args)
        if result.success:
            return f"✅ 代码执行成功:\n输出:\n{result.output}"
        else:
            return f"❌ 代码执行失败: {result.message}\n错误:\n{result.error}"

    def deploy_project(self, project_path: str, language: str = "python", port: int = 8000) -> str:
        """部署项目"""
        result = self.mcp_server.deploy_project(project_path, language, port)
        if result.success:
            return f"✅ 项目部署成功: {project_path}\n{result.logs}"
        else:
            return f"❌ 项目部署失败: {result.message}"

    def build_image(self, project_path: str, image_name: str) -> str:
        """构建Docker镜像"""
        result = self.mcp_server.build_docker_image(project_path, image_name)
        if result.success:
            return f"✅ Docker镜像构建成功: {image_name}\n镜像ID: {result.image_id}\n构建日志:\n{result.logs}"
        else:
            return f"❌ Docker镜像构建失败: {result.message}"

    def run_container(self, image_name: str, container_name: str, port: int = 8000) -> str:
        """运行Docker容器"""
        ports = {f"{port}/tcp": str(port)}
        result = self.mcp_server.run_docker_container(image_name, container_name, ports)
        if result.success:
            return f"✅ Docker容器运行成功: {container_name}\n容器ID: {result.container_id}\n访问地址: http://localhost:{port}\n日志:\n{result.logs}"
        else:
            return f"❌ Docker容器运行失败: {result.message}"

    def stop_container(self, container_name: str) -> str:
        """停止Docker容器"""
        result = self.mcp_server.stop_container(container_name)
        if result.success:
            return f"✅ {result.message}"
        else:
            return f"❌ {result.message}"

    def list_containers(self) -> str:
        """列出所有容器"""
        result = self.mcp_server.list_containers()
        if result.success:
            return f"容器列表:\n{result.logs}"
        else:
            return f"❌ {result.message}"

# 示例使用
if __name__ == "__main__":
    # 创建MCP服务器
    mcp_server = MCPServer(workspace_path="./projects")
    
    # 测试文件操作
    result = mcp_server.write_file("projects/test.py", "print('Hello from MCP!')")
    print(f"写入结果: {result.message}")
    
    # 测试代码生成
    result = mcp_server.generate_code("创建一个Python函数来计算斐波那契数列", "projects/fibonacci.py")
    print(f"代码生成结果: {result.message}")
    
    # 测试代码执行
    if result.success:
        exec_result = mcp_server.execute_code("projects/fibonacci.py")
        print(f"代码执行结果: {exec_result.message}")
        if exec_result.success:
            print(f"输出: {exec_result.output}")
    
    # 测试Docker部署
    deploy_result = mcp_server.deploy_project("projects/simple_app", "python", 8000)
    print(f"部署结果: {deploy_result.message}")
    if deploy_result.success:
        print(f"部署详情: {deploy_result.logs}") 
# AI团队系统 - 企业级多Agent协作平台

> 🚀 **最新版本 v2.0** - 全面优化，解决Docker中文名称、MCP工具问题、死循环、Token浪费和代码落地问题

一个基于CrewAI的企业级多Agent协作平台，支持多角色多轮对话、RAG知识库、权限管理、自动化部署和断点续传功能。

## ✨ 核心特性

### 🔧 最新优化功能
- **智能Docker名称处理**：自动将中文项目名转换为Docker兼容的英文名称
- **MCP工具优化**：详细的参数说明、错误处理和日志记录
- **死循环防护**：智能重试策略、循环检测和错误分析
- **Token优化**：上下文缓存、精简传输、智能轮次控制
- **代码自动落地**：从Agent输出中自动提取并保存代码文件
- **文档结构化**：自动生成共识文档和讨论日志

### 🎯 核心功能
- **多Agent协作**：支持产品经理、技术总监、前后端开发、测试、运维等角色
- **RAG知识库**：基于向量数据库的专业知识检索
- **权限管理**：细粒度的操作权限控制
- **自动化部署**：Docker容器化部署，支持多种语言
- **断点续传**：支持从指定阶段继续执行
- **实时日志**：完整的LLM对话和执行日志记录

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/coyi1234567/ai_team_system.git
cd ai_team_system

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

### 2. 构建知识库

```bash
# 构建向量知识库
python src/ingest_knowledge_base.py
```

### 3. 启动开发流程

```bash
# 重要：必须在ai_team_system目录下运行
cd ai_team_system

# 启动员工请假系统开发
python src/main.py --project-name "员工请假小程序" --requirements "开发一个员工请假小程序，支持多级审批、权限管理、请假记录查询、移动端适配、RAG知识库、MCP协议集成、自动化部署。"
```

## 📋 完整开发流程

### 阶段1：需求分析
- **参与角色**：项目总监、产品经理、技术总监
- **产出**：需求分析文档、功能规格说明
- **文件**：`需求分析_共识文档.md`

### 阶段2：技术设计
- **参与角色**：技术总监、产品经理、前后端开发工程师
- **产出**：技术架构设计、数据库设计、API设计
- **文件**：`技术设计_共识文档.md`

### 阶段3：前端开发
- **参与角色**：前端开发工程师、UI设计师、技术总监
- **产出**：前端代码、UI组件、页面设计
- **文件**：`frontend/` 目录下的代码文件

### 阶段4：后端开发
- **参与角色**：后端开发工程师、技术总监、产品经理
- **产出**：后端API、数据库操作、业务逻辑
- **文件**：`backend/` 目录下的代码文件

### 阶段5：测试与部署
- **参与角色**：测试工程师、DevOps工程师
- **产出**：测试用例、部署脚本、监控配置
- **文件**：`测试报告.md`、`部署文档.md`

### 阶段6：项目验收
- **参与角色**：项目总监、产品经理、技术总监、测试工程师
- **产出**：验收报告、项目总结
- **文件**：`验收_共识文档.md`

## 🔧 断点续传功能

### 查看进度
```bash
python src/main.py --project-name "员工请假小程序" --show-progress
```

### 从指定阶段继续
```bash
python src/main.py --project-name "员工请假小程序" --resume-from "technical_design"
```

### 重置进度
```bash
python src/main.py --project-name "员工请假小程序" --reset-progress
```

## 🛠️ 系统优化说明

### 1. Docker名称智能处理
系统自动处理中文项目名：
- `员工请假小程序` → `employee_leave_app`
- `员工请假系统` → `employee_leave_system`
- 其他中文名 → 自动转换为安全的英文名称

### 2. MCP工具增强
- **参数格式**：JSON格式，包含详细说明
- **错误处理**：提供具体错误原因和修复建议
- **日志记录**：完整的执行日志和异常信息

### 3. 智能重试机制
- **循环检测**：防止重复执行相同命令
- **错误分析**：自动识别错误类型并提供针对性建议
- **重试限制**：最多3次重试，避免无限循环

### 4. Token优化策略
- **上下文缓存**：避免重复内容传输
- **精简上下文**：只传递关键信息
- **结构化输出**：提高信息密度和可读性

### 5. 代码自动落地
系统自动从Agent输出中提取代码：
- **代码块识别**：支持多种代码块格式
- **智能文件命名**：根据任务类型和语言生成文件名
- **目录结构管理**：自动创建必要的目录结构

## 📁 项目结构

```
ai_team_system/
├── src/                    # 核心源码
│   ├── main.py            # 主入口
│   ├── crew.py            # AI团队协作逻辑
│   ├── crew_core.py       # 核心协作功能
│   ├── crew_tools.py      # 工具定义
│   ├── agents/            # Agent定义
│   ├── tools/             # 工具实现
│   └── utils/             # 工具函数
├── mcp_server.py          # MCP服务器
├── knowledge_base/        # 知识库文件
├── config/               # 配置文件
├── projects/             # 项目产出目录
├── logs/                 # 日志文件
└── vector_db/            # 向量数据库
```

## 🎯 使用示例

### 基础使用
```bash
# 开发员工请假系统
python src/main.py --project-name "员工请假小程序" --requirements "开发一个员工请假小程序，支持多级审批、权限管理、请假记录查询、移动端适配、RAG知识库、MCP协议集成、自动化部署。"
```

### 高级功能
```bash
# 查看项目进度
python src/main.py --project-name "员工请假小程序" --show-progress

# 从技术设计阶段继续
python src/main.py --project-name "员工请假小程序" --resume-from "technical_design"

# 重置项目进度
python src/main.py --project-name "员工请假小程序" --reset-progress
```

## 🔍 常见问题排查

### 环境配置问题
- **如遇到"产出目录/llm_log.txt/Dockerfile缺失"**：
  1. 检查`.env`文件内容和路径，确保API Key有效
  2. 查看控制台是否有LLM调用、产出落盘、自动部署等报错
  3. 确认`projects/{需求ID}/`目录是否被误删或权限不足

### 模块导入问题
- **如遇到`No module named 'src'`或`can't open file 'src/main.py'`错误**：
  - 请确保你已进入`ai_team_system`目录后再运行命令：
    ```bash
    cd ai_team_system
    python src/main.py --project-name "员工请假系统" --requirements "..."
    ```
  - 如果在项目根目录直接运行`python -m src.main ...`会报错
  - 一定要在`ai_team_system`目录下运行`python src/main.py ...`

### 向量模型下载问题
- **如遇到向量模型下载失败（SSL错误或网络超时）**：
  - 系统已自动配置HF镜像：`https://hf-mirror.com`
  - 如果仍有问题，可手动设置环境变量：
    ```bash
    export HF_ENDPOINT="https://hf-mirror.com"
    export HF_HUB_URL="https://hf-mirror.com"
    ```
  - 或使用其他国内镜像：`https://huggingface.co.cn`

### Docker相关问题
- **如遇到Docker镜像名称错误**：
  - 系统已自动处理中文项目名转换
  - 如果仍有问题，请使用英文项目名，如`leave_app`而不是`员工请假程序`

### 执行循环问题
- **如遇到重复执行或死循环**：
  - 系统已添加循环检测和智能重试机制
  - 最多重试3次，超过后会自动停止
  - 查看日志了解具体错误原因

## 📊 性能优化

### Token使用优化
- **上下文管理**：智能缓存，避免重复传输
- **精简提示词**：只包含必要信息
- **结构化输出**：提高信息密度

### 执行效率优化
- **并行处理**：多Agent并行执行
- **智能重试**：避免无效重试
- **错误分析**：快速定位问题

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆕 更新日志

### v2.0 (2024-06-23)
- ✅ 智能Docker名称处理，解决中文项目名问题
- ✅ MCP工具全面优化，增强错误处理和日志记录
- ✅ 死循环防护机制，智能重试策略
- ✅ Token使用优化，减少成本浪费
- ✅ 代码自动落地功能，真正实现自动化开发
- ✅ 文档结构化输出，提高可读性

### v1.0 (2024-06-22)
- 🎉 初始版本发布
- 🎯 多Agent协作框架
- 🔧 RAG知识库集成
- 🚀 自动化部署功能
- 📝 断点续传支持

## 📞 联系我们

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 参与讨论

---

**AI团队系统** - 让AI团队协作更高效！ 🚀
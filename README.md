# AI团队系统（多Agent + RAG知识库 + 权限管理）

## 项目简介
本系统是面向企业级AI团队的多智能体（Multi-Agent）协作平台，支持专业角色分工、MCP协议工具集成、本地RAG知识库检索、企业级RBAC+ABAC权限管理，助力AI项目高效落地。

---

## 主要功能
- **多Agent协作**：支持项目总监、产品经理、技术总监、前后端、算法、UI、数据分析、测试、DevOps、文员等11大专业角色，流程全覆盖。
- **MCP协议工具**：统一MCP协议接口，支持文件/代码/部署/自动化等标准化操作。
- **本地RAG知识库**：支持Chroma向量库+BM25关键词混合检索，知识块可按角色/文件分权。
- **企业级权限管理**：RBAC+ABAC混合模型，支持用户/角色/资源/操作多维权限，个人特批优先。
- **一键知识库构建**：自动分块、嵌入、索引，支持txt/md/yaml等多格式批量导入。
- **可扩展API**：支持集成API服务、管理后台、前端等。
- **需求驱动全自动部署**：只需下达需求，AI团队自动完成代码生成、文档、测试、Docker镜像构建与容器部署，无需手动输入任何参数。
- **需求ID唯一+自动归档清理**：每个需求有唯一ID（如项目名），每次执行同名需求时，系统会自动归档并清理旧产出、日志、Docker容器，保证每次都是全新环境。所有需求ID与内容的映射关系记录在`projects/project_index.json`，支持历史追溯和环境隔离。

---

## 目录结构
```
ai_team_system/
├── src/                  # 核心代码
│   ├── main.py           # Typer命令行入口（已集成全自动部署+需求ID唯一+自动归档清理）
│   ├── crew.py           # 多Agent团队与流程
│   ├── crew_tools.py     # MCP工具适配
│   ├── rag_api.py        # RAG检索+权限API
│   ├── permission_manager.py # 权限管理
│   └── ingest_knowledge_base.py # 知识库向量化/索引
├── knowledge_base/       # 角色知识库（分角色/分文件夹）
├── vector_db/            # 本地Chroma向量库/BM25索引
├── config/               # 角色、模型、团队配置
├── projects/             # 项目输出及project_index.json
├── archive/              # 历史归档产出
├── requirements.txt      # 依赖
└── README.md             # 项目说明
```

---

## 环境变量与自动加载

本项目所有敏感配置（如OPENAI_API_KEY）均存放于根目录的.env文件，例如：
```
OPENAI_API_BASE=https://api.openai-proxy.org/v1
OPENAI_API_KEY=sk-xxxxxx
```
- **自动加载机制**：主程序已集成python-dotenv，运行时会自动加载.env，无需手动source。
- **常见问题排查**：如遇到LLM相关API报错，请优先检查.env文件内容和路径，确保key有效。
- **无需手动source .env**：直接运行python -m src.main ... 即可，环境变量会自动生效。

---

## 快速上手

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 构建知识库索引
> 支持knowledge_base/下txt、md、yaml等批量导入，自动分块、嵌入、索引
```bash
python src/ingest_knowledge_base.py
```

### 3. 启动AI团队项目（全自动部署，无需参数！）
```bash
python -m src.main --project-name "员工请假小程序" --requirements "开发一个员工请假小程序，支持多级审批、权限管理、请假记录查询、移动端适配、RAG知识库、MCP协议集成、自动化部署。"
```
- 系统会自动完成需求分析、代码/文档/测试/部署脚本生成、Docker镜像构建与容器部署。
- 你无需手动输入任何部署参数，服务自动上线。
- 每次执行同名需求时，系统会自动归档并清理旧产出、日志、Docker容器，保证环境唯一。
- 所有需求ID与内容的映射关系可在`projects/project_index.json`查阅。

### 3.1 断点续传功能
系统支持断点续传，可以从中断的地方继续执行：

```bash
# 查看项目进度
python -m src.main --project-name "员工请假系统" --show-progress

# 从指定阶段继续执行
python -m src.main --project-name "员工请假系统" --requirements "开发一个员工请假系统..." --resume-from "frontend_code"

# 重置项目进度，重新开始
python -m src.main --project-name "员工请假系统" --reset-progress
```

**可用阶段**：
- `requirement_analysis` - 需求分析
- `technical_design` - 技术设计  
- `ui_design` - UI设计
- `frontend_development` - 前端开发讨论
- `frontend_code` - 前端代码生成
- `backend_development` - 后端开发讨论
- `backend_code` - 后端代码生成
- `data_analysis` - 数据分析
- `testing` - 测试
- `deployment` - 部署
- `documentation` - 文档
- `acceptance` - 验收
- `auto_execution` - 自动执行

**断点续传优势**：
- 支持长时间项目的分段执行
- 避免重复执行已完成的工作
- 可以针对特定阶段进行调试和优化
- 进度状态自动保存，支持多项目并行

### 4. RAG知识库检索（带权限）
```python
from src.rag_api import rag_search
# user_id, role, query, top_k
print(rag_search("u001", "boss", "项目管理最佳实践"))
```

---

## 权限管理说明
- 权限规则存储于config/permissions.json
- 支持用户/角色/资源/操作多维度，个人特批优先
- 可通过src/permission_manager.py增删查权限

---

## MCP协议工具说明
- 统一MCP协议接口，支持文件读写、代码生成、执行、Docker部署等
- 详见src/crew_tools.py、mcp_server.py

---

## 依赖环境
- Python 3.9+
- 主要依赖：crewai, typer, rich, pyyaml, openai, chromadb, sentence-transformers, scikit-learn, docker

---

## 典型场景
- 企业AI团队协作、知识管理、权限管控、自动化交付
- AI项目全流程自动化、专业分工、知识安全

---

## 贡献与反馈
欢迎提交Issue/PR，或联系AI团队共建更强大的智能协作平台！

---

## 多角色多轮对话与共识机制

- 需求分析、技术设计、前端开发、后端开发、验收等关键阶段，均支持多角色多轮对话，自动产出共识文档和对话日志。
- 每个阶段可灵活配置参与角色、对话轮数、最终汇总角色，产出更真实、可复核。
- 所有对话过程、共识产出自动归档于产出目录，便于溯源和复盘。
- 主流程上下文链路自动传递，确保各阶段产出高度协作和一致。

### 完整开发流程

系统采用"讨论先行，代码后行"的协作模式：

1. **需求分析阶段**：项目总监 + 产品经理 + 技术总监多轮讨论
   - 深入分析用户需求、功能需求、非功能性需求
   - 确定项目范围、风险评估和应对策略
   - 产出需求分析共识文档

2. **技术设计阶段**：技术总监 + 产品经理 + 前端开发 + 后端开发多轮讨论
   - 系统架构设计和技术选型
   - 数据库设计和API接口规范
   - 安全架构和性能优化策略
   - 产出技术设计共识文档

3. **UI设计阶段**：UI设计师单Agent执行
   - 基于需求和技术方案设计用户界面
   - 交互设计和视觉设计规范
   - 响应式设计和设计系统构建
   - 产出UI设计文档

4. **前端开发阶段**：
   - **讨论阶段**：前端开发 + UI设计师 + 技术总监多轮讨论
     - 确定前端技术栈和架构
     - 组件设计和状态管理方案
     - 性能优化和用户体验策略
   - **代码生成阶段**：前端开发单Agent执行
     - 基于讨论结果生成完整前端代码
     - 包含组件库、工具函数、测试用例
     - 自动提取代码块并写入项目目录

5. **后端开发阶段**：
   - **讨论阶段**：后端开发 + 技术总监 + 产品经理多轮讨论
     - 确定后端技术栈和架构
     - API设计和数据库操作方案
     - 安全性和性能优化策略
   - **代码生成阶段**：后端开发单Agent执行
     - 基于讨论结果生成完整后端代码
     - 包含API接口、数据库脚本、业务逻辑
     - 自动提取代码块并写入项目目录

6. **其他阶段**：数据分析、测试、部署、文档、验收
   - 各专业角色基于前期成果进行专项工作
   - 自动生成相应的报告和配置文档

7. **自动执行与修正**：
   - 系统自动检测并执行生成的代码文件
   - 支持Python、Shell、npm、pytest、Docker等多种执行类型
   - 多Agent协作修正执行中的问题
   - 确保代码能够正常运行和部署

---

## 产出目录结构示例

每次下达新需求，系统会自动在 `projects/{需求ID}/` 下生成独立产出目录，所有代码、文档、日志、Dockerfile等均归档于此。例如：

```
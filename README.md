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

---

## 目录结构
```
ai_team_system/
├── src/                  # 核心代码
│   ├── main.py           # Typer命令行入口
│   ├── crew.py           # 多Agent团队与流程
│   ├── crew_tools.py     # MCP工具适配
│   ├── rag_api.py        # RAG检索+权限API
│   ├── permission_manager.py # 权限管理
│   └── ingest_knowledge_base.py # 知识库向量化/索引
├── knowledge_base/       # 角色知识库（分角色/分文件夹）
├── vector_db/            # 本地Chroma向量库/BM25索引
├── config/               # 角色、模型、团队配置
├── projects/             # 项目输出
├── requirements.txt      # 依赖
└── README.md             # 项目说明
```

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

### 3. 启动AI团队项目
```bash
python -m src.main
# 或自定义项目
python -m src.main --project-name "智能客服系统" --requirements "开发一个AI客服平台..."
```

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

## 🏆 AI团队系统业务验收标准

### 业务需求（唯一测试用例）

> **开发一个员工请假小程序**
>
> - 支持员工在线提交请假申请
> - 支持主管/HR多级审批
> - 支持请假记录查询、统计
> - 支持移动端适配
> - 权限管理、自动化部署、RAG知识库问答、MCP协议集成

### 测试方法

1. 运行如下命令，给AI团队下达需求：
   ```bash
   python -m src.main --project-name "员工请假小程序" --requirements "开发一个员工请假小程序，支持多级审批、权限管理、请假记录查询、移动端适配、RAG知识库、MCP协议集成、自动化部署。"
   ```
2. 检查AI团队产出：
   - 前后端代码
   - 数据库设计
   - API文档
   - 测试用例
   - 部署脚本
   - 权限配置
3. 实际运行/部署/访问小程序，验证功能是否可用。

### 验收标准

- 只有当"员工请假小程序"能真实跑起来、可用，才算AI团队系统通过测试。 
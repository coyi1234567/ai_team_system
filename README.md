# AI团队系统

一个基于LLM的智能开发团队协作系统，支持从需求分析到部署运维的全流程自动化。

## 🚀 功能特点

- **智能团队协作**: 模拟真实开发团队的工作流程
- **角色专业化**: 每个团队成员都有明确的职责和技能
- **流程自动化**: 从需求分析到项目交付的完整流程
- **LLM驱动**: 基于OpenAI GPT-4的智能决策和内容生成
- **可视化界面**: 丰富的命令行界面和进度展示

## 📋 团队成员

| 角色 | 姓名 | 职责 | 技能 |
|------|------|------|------|
| 项目总监 | 张总 | 项目决策、资源分配、最终验收 | 项目管理、商务谈判 |
| 产品经理 | 李产品 | 需求分析、产品规划、用户体验 | 需求分析、产品设计 |
| 技术负责人 | 王架构 | 技术架构、技术选型、代码审查 | 系统设计、架构规划 |
| 前端开发 | 陈前端 | 用户界面、前端交互、响应式设计 | React、TypeScript、CSS |
| 后端开发 | 刘后端 | 后端服务、数据库设计、API开发 | Python、FastAPI、数据库 |
| 测试工程师 | 赵测试 | 测试计划、质量保证、缺陷管理 | 测试设计、自动化测试 |
| DevOps工程师 | 孙运维 | 系统部署、运维监控、自动化 | Docker、Kubernetes、CI/CD |

## 🛠️ 安装配置

### 1. 克隆项目
```bash
git clone <repository-url>
cd ai_team_system
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
创建 `.env` 文件：
```bash
OPENAI_API_KEY=your-openai-api-key
```

### 4. 检查配置文件
确保 `config/team_config.yaml` 配置文件存在。

## 🎯 使用方法

### 初始化系统
```bash
python main.py init
```

### 查看团队信息
```bash
python main.py team
```

### 创建项目
```bash
python main.py create \
  --name "在线图书管理系统" \
  --description "一个功能完整的图书管理平台" \
  --requirements "开发一个在线图书管理系统，功能包括用户注册、图书管理、借阅归还等"
```

### 执行项目
```bash
python main.py execute --id "项目ID"
```

### 列出所有项目
```bash
python main.py list
```

### 运行演示
```bash
python main.py demo
```

### 查看帮助
```bash
python main.py help
```

## 📊 项目流程

1. **需求分析** (1-2天)
   - 产品经理分析客户需求
   - 制定产品方案和用户故事
   - 风险评估和项目规划

2. **技术设计** (1-2天)
   - 技术负责人设计系统架构
   - 技术栈选型和数据库设计
   - API接口设计和部署方案

3. **开发实现** (5-10天)
   - 前端开发实现用户界面
   - 后端开发实现业务逻辑
   - 数据库设计和API开发

4. **测试验证** (2-3天)
   - 测试工程师制定测试计划
   - 执行功能测试和性能测试
   - 缺陷管理和质量保证

5. **部署运维** (1-2天)
   - DevOps工程师配置部署环境
   - 系统部署和监控配置
   - 自动化流程和运维文档

6. **项目验收** (1天)
   - 项目总监进行最终验收
   - 交付清单和项目总结
   - 客户培训和后续支持

## 🏗️ 技术架构

### 前端技术栈
- React 18
- TypeScript
- Tailwind CSS
- Vite

### 后端技术栈
- Python 3.11
- FastAPI
- SQLAlchemy
- Pydantic

### 数据库
- PostgreSQL
- Redis

### 部署技术
- Docker
- Docker Compose
- Nginx

### 监控工具
- Prometheus
- Grafana
- ELK Stack

## 📁 项目结构

```
ai_team_system/
├── config/
│   └── team_config.yaml      # 团队配置文件
├── src/
│   ├── __init__.py
│   ├── models.py             # 数据模型
│   ├── llm_client.py         # LLM客户端
│   └── team_manager.py       # 团队管理器
├── main.py                   # 主程序入口
├── requirements.txt          # 依赖包
├── README.md                 # 项目说明
└── .env                      # 环境变量
```

## 🔧 配置说明

### 团队配置 (config/team_config.yaml)
- 团队成员信息
- 技能和职责定义
- 项目流程配置
- 技术栈配置
- 质量标准

### 环境变量 (.env)
- `OPENAI_API_KEY`: OpenAI API密钥
- 其他配置项

## 🎨 界面展示

系统提供丰富的命令行界面：
- 彩色输出和进度条
- 表格展示项目信息
- 实时进度更新
- 详细的项目报告

## 🔍 故障排除

### 常见问题

1. **配置文件不存在**
   - 确保 `config/team_config.yaml` 文件存在
   - 检查文件路径和权限

2. **API密钥错误**
   - 检查 `.env` 文件中的 `OPENAI_API_KEY`
   - 确保API密钥有效且有足够余额

3. **依赖包安装失败**
   - 使用虚拟环境
   - 更新pip版本
   - 检查Python版本兼容性

### 调试模式
```bash
# 设置调试环境变量
export DEBUG=1
python main.py demo
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License

## 📞 联系方式

如有问题或建议，请提交 Issue 或联系开发团队。

---

**AI团队系统** - 让AI驱动团队协作，让开发更智能！ 
# AI团队系统 - CrewAI版本

基于CrewAI框架的智能多Agent协作系统，支持11个专业角色的智能团队协作，集成MCP工具，实现标准化Agent协作。

## 🎯 核心特性

- 🤖 **11个专业角色**: 项目总监、产品经理、技术总监、算法工程师、UI设计师、前后端开发、数据分析师、测试工程师、DevOps工程师、项目文员
- 📋 **11个阶段流程**: 需求分析 → 技术设计 → UI设计 → 算法设计 → 前端开发 → 后端开发 → 数据分析 → 测试验证 → 部署运维 → 文档整理 → 项目验收
- 🧠 **智能算法**: 集成机器学习算法，提供智能解决方案
- 🎨 **专业设计**: UI设计师确保产品美观易用
- 📊 **数据分析**: 数据分析师提供数据洞察
- 📝 **文档管理**: 项目文员确保信息有序管理
- 🔧 **MCP工具**: 集成MCP协议，支持标准化工具调用
- 💻 **代码生成**: 自动生成前端、后端代码和数据库设计
- 🚀 **部署脚本**: 自动生成Docker配置和部署脚本

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd ai_team_system

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥
```bash
export OPENAI_API_KEY="your-api-key-here"
export OPENAI_API_BASE="https://api.openai-proxy.org/v1"  # 可选
```

### 3. 运行系统
```bash
# 初始化系统
python main.py init

# 查看团队信息
python main.py team

# 运行演示项目
python main.py demo

# 创建自定义项目
python main.py create --name "项目名称" --description "项目描述" --requirements "项目需求"
```

## 📁 项目结构

```
ai_team_system/
├── src/                      # 源代码
│   ├── crew.py              # CrewAI团队定义
│   ├── crew_tools.py        # MCP工具实现
│   ├── main.py              # CrewAI入口
│   └── __init__.py          # 模块初始化
├── config/                  # 配置文件
├── knowledge_base/          # 角色知识库
├── projects/               # 项目输出目录
├── main.py                 # 主程序入口
├── requirements.txt        # 依赖包
└── README.md              # 项目说明
```

## 👥 团队成员

| 角色 | 姓名 | 经验 | 专业领域 |
|------|------|------|----------|
| 👔 项目总监 | 张总 | 15年 | 项目管理、资源协调、风险管理 |
| 📋 产品经理 | 李产品 | 8年 | 需求分析、产品设计、用户体验 |
| 🏗️ 技术总监 | 王技术 | 12年 | 系统架构、技术选型、性能优化 |
| 🧠 算法工程师 | 陈算法 | 10年 | 机器学习、数据挖掘、智能算法 |
| 🎨 UI设计师 | 林设计 | 7年 | 界面设计、交互设计、视觉设计 |
| 💻 前端开发 | 陈前端 | 6年 | React、TypeScript、前端优化 |
| ⚙️ 后端开发 | 刘后端 | 8年 | FastAPI、数据库、微服务 |
| 📊 数据分析师 | 赵数据 | 5年 | 数据分析、商业智能、可视化 |
| 🔍 测试工程师 | 赵测试 | 7年 | 测试策略、自动化测试、质量保障 |
| 🚀 DevOps工程师 | 孙运维 | 6年 | Docker、K8s、CI/CD |
| 📝 项目文员 | 王文员 | 4年 | 文档管理、会议记录、进度跟踪 |

## 🎮 使用方法

### 命令行操作
```bash
# 查看团队信息
python main.py team

# 创建新项目
python main.py create --name "智能客服系统" --description "基于AI的智能客服平台" --requirements "详细需求描述"

# 运行演示项目
python main.py demo

# 查看帮助
python main.py help
```

### 项目流程

1. **需求分析** - 产品经理深入分析用户需求，制定产品规划
2. **技术设计** - 技术总监设计系统架构，制定技术方案
3. **UI设计** - UI设计师设计用户界面，确保美观易用
4. **算法设计** - 算法工程师设计智能算法，提供AI能力
5. **前端开发** - 前端工程师实现用户界面和交互
6. **后端开发** - 后端工程师实现业务逻辑和API服务
7. **数据分析** - 数据分析师提供数据洞察和业务分析
8. **测试验证** - 测试工程师进行全面测试和质量保障
9. **部署运维** - DevOps工程师部署系统并配置监控
10. **文档整理** - 项目文员整理项目文档和交付物
11. **项目验收** - 项目总监进行最终验收和交付

## 🔧 MCP工具集成

系统集成了MCP（Model Context Protocol）工具，支持：

- **标准化工具调用**: 每个Agent都可以通过MCP协议调用外部工具
- **资源共享**: Agent间可以共享工具和资源
- **可扩展性**: 支持集成更多MCP生态工具
- **互操作性**: 与其他MCP兼容系统无缝协作

## 💰 成本控制

### 模型价格（每1000 tokens）
- **gpt-4o-mini**: $0.15 输入 / $0.6 输出
- **gpt-4o**: $2.5 输入 / $10 输出

### 成本优化策略
- 使用 `gpt-4o-mini` 作为默认模型
- 为不同角色配置合适的模型
- 启用MCP工具减少重复计算

## 🚀 部署选项

### 本地开发环境
```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export OPENAI_API_KEY="your-api-key"

# 运行系统
python main.py init
python main.py demo
```

### 云服务器部署
```bash
# 上传代码
scp -r ai_team_system/ user@server:/home/user/

# SSH登录并部署
ssh user@server
cd ai_team_system
pip install -r requirements.txt
python main.py init
```

### Docker容器部署
```bash
# 构建镜像
docker build -t ai-team-system .

# 运行容器
docker run -d \
  --name ai-team-system \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your-api-key" \
  -v $(pwd)/projects:/app/projects \
  ai-team-system
```

## 🔍 故障排除

### 常见问题
1. **API调用失败**: 检查API密钥和网络连接
2. **依赖安装失败**: 升级pip并重新安装
3. **权限问题**: 设置正确的文件权限

### 日志查看
```bash
# 启用详细日志
export CREWAI_VERBOSE=1
python main.py demo
```

## 📈 未来规划

- [ ] 集成更多MCP生态工具
- [ ] 支持更多AI模型和提供商
- [ ] 增加可视化界面
- [ ] 支持团队协作和版本控制
- [ ] 集成项目管理工具

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

## �� 许可证

MIT License 
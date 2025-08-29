# ResVizCopilot 2.0

## 项目简介

ResVizCopilot 2.0 是一个科研智能体项目，集成了研究树数据库管理和智能体流式交互系统。项目支持工程级别的数据持久化，确保程序可以在进程关闭后从文件中恢复所有数据。

## 核心功能

### 1. 研究树管理
- **问题节点管理**：支持创建、更新、删除根问题和子问题
- **解决方案管理**：为问题创建、更新、删除解决方案
- **快照系统**：每次修改操作都会创建新的快照，保证历史数据完整性
- **树状结构**：支持层级嵌套的问题-解决方案结构

### 2. 智能体交互
- **流式传输**：支持Server-Sent Events (SSE)实时数据传输
- **智能体调用**：集成多种智能体，支持不同场景的智能交互
- **消息管理**：统一的消息操作接口，支持增量更新和回溯操作

### 3. 工程管理
- **数据持久化**：自动保存和恢复数据库数据和消息列表数据
- **工程版本控制**：支持工程的保存、加载、另存为、删除等操作
- **自动恢复**：程序启动时自动加载最新的工程存档
- **文件冲突处理**：自动处理文件名冲突，添加数字后缀

## 系统架构

### 核心组件

1. **ProjectManager**：项目管理器，负责数据持久化和工程管理
2. **DatabaseManager**：数据库管理器，管理研究树的快照和节点数据
3. **MessageManager**：消息管理器，处理消息的创建、更新和分发
4. **智能体系统**：提供各种智能交互功能

### 数据流

```
用户操作 → 路由接口 → 管理器 → 数据持久化
    ↓
智能体响应 → 消息更新 → 快照创建 → 自动保存
```

## 安装和运行

### 环境要求
- Python 3.8+
- FastAPI
- uvicorn

### 安装依赖
```bash
pip install -r backend/requirements.txt
```

### 环境配置
项目支持通过环境变量进行配置，可以创建 `.env` 文件或设置系统环境变量：

1. **复制示例配置文件**：
```bash
cp backend/env.example backend/.env
```

2. **编辑配置文件**，设置必要的参数：
   - `DEEPSEEK_API_KEY`: 你的DeepSeek API密钥
   - `DEEPSEEK_BASE_URL`: DeepSeek API基础URL
   - 代理配置（可选）：
     - `HTTP_PROXY`: HTTP代理地址
     - `HTTPS_PROXY`: HTTPS代理地址
     - `NO_PROXY`: 不使用代理的地址列表

### 启动服务
```bash
export PYTHONPATH=/path/to/ResVizCopilot-2.0.0:$PYTHONPATH
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8008 --reload
```

### 运行测试
```bash
python test_CLI_frontend.py
```

## API接口

### 工程管理接口

| 接口名称 | 方法 | 路径 | 功能描述 |
|---------|------|------|----------|
| 创建新工程 | POST | `/projects` | 创建新的研究工程 |
| 保存当前工程 | POST | `/projects/save` | 保存当前工程状态 |
| 另存为工程 | POST | `/projects/save-as` | 将当前工程另存为新名称 |
| 加载工程 | GET | `/projects/{project_name}` | 从文件加载指定工程 |
| 获取工程列表 | GET | `/projects` | 获取所有已保存的工程 |
| 删除工程 | DELETE | `/projects/{project_name}` | 删除指定工程 |
| 获取当前工程信息 | GET | `/projects/current/info` | 获取当前工程详细信息 |

### 研究树接口

| 接口名称 | 方法 | 路径 | 功能描述 |
|---------|------|------|----------|
| 获取当前快照 | GET | `/research-tree/snapshots/current` | 获取当前数据库快照 |
| 创建根问题 | POST | `/research-tree/problems/root` | 创建根级别的问题节点 |
| 更新根问题 | PATCH | `/research-tree/problems/root/{problem_id}` | 更新指定的根问题 |
| 删除根问题 | DELETE | `/research-tree/problems/root/{problem_id}` | 删除指定的根问题 |
| 创建解决方案 | POST | `/research-tree/problems/{problem_id}/solutions` | 为问题创建解决方案 |
| 更新解决方案 | PATCH | `/research-tree/solutions/{solution_id}` | 更新指定的解决方案 |
| 删除解决方案 | DELETE | `/research-tree/solutions/{solution_id}` | 删除指定的解决方案 |
| 设置选中解决方案 | POST | `/research-tree/problems/{problem_id}/selected-solution` | 设置问题的选中解决方案 |

### 智能体接口

| 接口名称 | 方法 | 路径 | 功能描述 |
|---------|------|------|----------|
| 启动智能体 | POST | `/agents/messages` | 启动智能体并开始流式交互 |
| 获取消息历史 | GET | `/agents/messages/history` | 获取所有历史消息 |
| 继续未完成消息 | GET | `/agents/messages/continue/{message_id}` | 继续传输未完成的消息 |

## 数据持久化

### 存档文件结构
工程数据保存在 `data/projects/` 文件夹下，文件格式为JSON，包含以下信息：

```json
{
  "project_name": "工程名称",
  "created_at": "创建时间",
  "updated_at": "更新时间",
  "messages": {
    "消息ID": "消息数据"
  },
  "message_order": ["消息ID列表"],
  "snapshot_map": {
    "快照ID": "快照数据"
  },
  "current_snapshot_id": "当前快照ID"
}
```

### 自动恢复机制
- 程序启动时自动查找最新的工程存档
- 如果找到存档，自动加载恢复数据
- 如果没有存档，自动创建新的空工程
- 支持错误处理和后备机制

### 文件冲突处理
- 自动检测文件名冲突
- 添加数字后缀避免覆盖：`工程名(1).json`、`工程名(2).json`
- 保持原工程文件不变

## 使用说明

### 基本操作流程

1. **启动程序**：运行测试文件或启动后端服务
2. **自动恢复**：程序会自动加载最新存档或创建新工程
3. **创建问题**：使用研究树接口创建根问题和解决方案
4. **调用智能体**：启动智能体进行交互
5. **保存工程**：手动保存或自动保存工程状态
6. **工程管理**：创建、加载、删除不同的工程

### 测试功能

测试文件 `test_CLI_frontend.py` 提供了完整的交互式测试环境：

- **研究树操作**：创建、查看、管理研究树结构
- **智能体调用**：测试各种智能体功能
- **工程管理**：完整的工程生命周期管理
- **数据可视化**：树状结构显示和消息历史查看

## 技术特点

### 设计原则
- **单一职责**：每个管理器负责特定的功能领域
- **数据一致性**：通过共享实例确保数据同步
- **错误处理**：完善的异常处理和日志记录
- **扩展性**：模块化设计，易于添加新功能

### 性能优化
- **内存管理**：智能的快照管理，避免内存泄漏
- **流式传输**：支持实时数据传输，提升用户体验
- **异步处理**：使用异步编程提高并发性能

### 数据安全
- **快照机制**：每次修改创建新快照，保护历史数据
- **文件备份**：自动处理文件冲突，避免数据丢失
- **错误恢复**：支持从错误状态自动恢复

## 开发指南

### 代码结构
```
backend/
├── project_manager.py      # 项目管理器
├── database/               # 数据库相关
│   ├── database_manager.py # 数据库管理器
│   └── schemas/           # 数据模型
├── message/                # 消息管理
│   ├── message_manager.py  # 消息管理器
│   └── schemas/           # 消息模型
├── routers/                # API路由
│   ├── projects.py        # 工程管理路由
│   ├── research_tree.py   # 研究树路由
│   └── agents.py          # 智能体路由
└── utils/                  # 工具函数
```

### 添加新功能
1. 在相应的管理器中添加业务逻辑
2. 在路由文件中添加API接口
3. 在测试文件中添加测试用例
4. 更新README文档

### 调试和测试
- 使用日志系统记录关键操作
- 通过测试文件验证功能完整性
- 检查数据持久化是否正确
- 验证错误处理机制

## 代理配置

### 配置代理
如果你的网络环境需要通过代理访问外网，可以在 `.env` 文件中配置代理：

```bash
# HTTP代理
HTTP_PROXY=http://proxy.example.com:8080

# HTTPS代理  
HTTPS_PROXY=http://proxy.example.com:8080

# 不使用代理的地址（可选）
NO_PROXY=localhost,127.0.0.1
```

代理配置会自动应用到所有LLM API调用中。

### 代理配置示例
- **HTTP代理**: `HTTP_PROXY=http://192.168.1.100:8080`
- **HTTPS代理**: `HTTPS_PROXY=http://192.168.1.100:8080`
- **认证代理**: `HTTPS_PROXY=http://username:password@proxy.example.com:8080`
- **排除本地地址**: `NO_PROXY=localhost,127.0.0.1,192.168.1.0/24`

## 常见问题

### Q: 程序启动后没有自动加载存档？
A: 检查 `data/projects/` 文件夹是否存在，以及是否有有效的JSON存档文件。

### Q: 保存工程时出现错误？
A: 检查文件权限和磁盘空间，确保 `data/projects/` 文件夹可写。

### Q: 加载工程后数据不完整？
A: 检查存档文件是否损坏，可以尝试删除损坏的文件重新创建。

### Q: 如何备份工程数据？
A: 直接复制 `data/projects/` 文件夹即可，所有工程数据都在其中。

## 更新日志

### v2.0.0
- 新增工程管理系统
- 实现数据持久化功能
- 支持工程版本控制
- 优化用户交互体验
- 完善错误处理机制

## 贡献指南

欢迎提交Issue和Pull Request来改进项目。在提交代码前，请确保：

1. 代码符合项目的编码规范
2. 添加了必要的测试用例
3. 更新了相关文档
4. 通过了所有测试

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交GitHub Issue
- 发送邮件至项目维护者
- 参与项目讨论

---

**注意**：本项目仍在积极开发中，API接口可能会有变化，请关注更新日志。

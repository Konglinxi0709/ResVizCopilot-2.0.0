# ResVizCopilot 2.0 流式智能体系统

## 🎯 项目概述

基于ProjectManager架构的智能体流式传输系统，支持SSE协程解耦、XML解析验证、错误重试和快照管理的完整解决方案。

**核心特性**：
- 🔄 统一重试机制（LLM调用+解析+验证）
- 🎭 智能提示词策略（自动识别输入类型）
- 📝 PydanticV2验证器体系（类型安全保障）
- 🔗 SSE流式传输（协程独立运行）
- 📸 快照对象管理（状态回溯支持）

---

## 📡 接口定义

### 智能体交互接口

#### 发送消息 - SSE流式响应
```http
POST /agents/messages
Content-Type: application/json

{
  "content": "用户消息内容",
  "title": "消息标题",
  "agent_name": "default"
}
```

**响应**: `text/event-stream` 格式
```javascript
data: {
  "event": "patch",
  "data": {
    "message_id": "uuid",
    "thinking_delta": "思考过程增量",
    "content_delta": "内容增量", 
    "action_title": "行动标题",
    "snapshot_id": "快照ID",
    "finished": true
  }
}
```

#### 获取消息历史
```http
GET /agents/messages/history
```

#### 继续未完成消息
```http
GET /agents/messages/continue/{message_id}
```

#### 停止生成
```http
POST /agents/messages/stop
```

### 测试调试接口

#### 会话状态查询
```http
GET /test/session/status
```

#### LLM错误模拟
```http
POST /test/llm/simulate-error
Content-Type: application/json

{
  "error_rate": 0.3,
  "error_types": ["network", "timeout", "api_error"]
}
```

#### 延迟配置
```http
POST /test/llm/delay
Content-Type: application/json

{
  "delay_per_token": 0.05
}
```

---

## 🏗️ 系统架构

### 整体架构类图

```mermaid
classDiagram
    %% 路由层
    class FastAPIApp {
        +include_router()
        +CORS配置
    }
    
    class AgentsRouter {
        +POST /agents/messages
        +GET /agents/messages/history  
        +GET /agents/messages/continue
        +POST /agents/messages/stop
    }
    
    class TestRouter {
        +GET /test/session/status
        +POST /test/llm/simulate-error
        +POST /test/llm/delay
        +GET /test/queue/status
    }
    
    %% 核心管理层
    class ProjectManager {
        -DataManager data_manager
        -Dict agents
        -Queue patch_queue
        -List subscribers
        +register_agent()
        +publish_patch()
        +subscribe_patches()
        +get_message_history()
        +get_database_snapshot()
    }
    
    class DataManager {
        -Dict database
        -Dict snapshots
        +execute_action()
        +create_snapshot()
        +rollback_to_snapshot()
        +get_database_state()
    }
    
    %% 智能体层
    class AgentBase {
        <<abstract>>
        +MockLLMClient llm_client
        +RetryWrapper retry_wrapper
        +XMLParser xml_parser
        +process_user_message()
        +_call_llm_with_retry()
        +_execute_action()
        +stop_processing()
        +is_processing()
    }
    
    class SimpleAgent {
        +PromptStrategy prompt_strategy
        +_agent_process()
        +_handle_structured_output()
        +_assess_situation()
        +reset_conversation()
    }
    
    %% 提示词策略层
    class PromptStrategy {
        -Dict prompt_templates
        -Dict validator_mapping
        +determine_prompt_type()
        +get_prompt_and_validator()
        +reset_conversation()
    }
    
    class PromptType {
        <<enumeration>>
        CHAT
        CREATE_PROBLEM
        QUERY_PROBLEMS
        UPDATE_PROBLEM
    }
    
    %% 验证器层
    class CreateResearchProblemOutput {
        +title: str
        +params: CreateResearchProblemParams
    }
    
    class QueryProblemsOutput {
        +title: str
        +params: QueryProblemsParams
    }
    
    class UpdateProblemOutput {
        +title: str
        +params: UpdateProblemParams
    }
    
    %% LLM客户端层
    class MockLLMClient {
        -Dict response_templates
        -float delay_per_token
        -float error_rate
        +stream_generate()
        +_determine_response_type()
        +simulate_error()
        +set_delay()
    }
    
    %% 重试机制层
    class RetryWrapper {
        -int max_retries
        -float base_delay
        -Dict retry_stats
        +execute_with_retry()
        +_should_retry()
        +_calculate_delay()
        +get_retry_stats()
    }
    
    %% XML解析层
    class XMLParser {
        +xml_to_dict()
        +validate_with_pydantic()
        +parse_and_validate()
        +extract_xml_from_content()
    }
    
    %% 数据模型层
    class Message {
        +id: str
        +role: str
        +status: str
        +title: str
        +thinking: str
        +content: str
        +action_title: str
        +action_params: Dict
        +snapshot_id: str
        +created_at: datetime
        +updated_at: datetime
    }
    
    class Patch {
        +message_id: Optional[str]
        +thinking_delta: str
        +content_delta: str
        +title: Optional[str]
        +action_title: Optional[str]
        +action_params: Optional[Dict]
        +snapshot_id: Optional[str]
        +finished: bool
        +rollback: bool
        +apply_to_message()
    }
    
    %% 关系定义
    FastAPIApp --> AgentsRouter
    FastAPIApp --> TestRouter
    AgentsRouter --> ProjectManager
    TestRouter --> ProjectManager
    
    ProjectManager --> DataManager
    ProjectManager --> AgentBase
    
    AgentBase <|-- SimpleAgent
    AgentBase --> MockLLMClient
    AgentBase --> RetryWrapper
    AgentBase --> XMLParser
    
    SimpleAgent --> PromptStrategy
    PromptStrategy --> PromptType
    PromptStrategy --> CreateResearchProblemOutput
    PromptStrategy --> QueryProblemsOutput
    PromptStrategy --> UpdateProblemOutput
    
    ProjectManager --> Message
    ProjectManager --> Patch
    XMLParser --> CreateResearchProblemOutput
    XMLParser --> QueryProblemsOutput
    XMLParser --> UpdateProblemOutput
```

### 架构分层说明

| 层级 | 组件 | 职责 |
|------|------|------|
| **路由层** | FastAPI + Routers | HTTP接口暴露，请求路由分发 |
| **管理层** | ProjectManager + DataManager | 消息管理，数据持久化，快照控制 |
| **智能体层** | AgentBase + SimpleAgent | 业务逻辑处理，智能决策 |
| **策略层** | PromptStrategy + Validators | 提示词选择，输出验证 |
| **工具层** | LLMClient + RetryWrapper + XMLParser | 基础服务，重试机制，数据解析 |
| **模型层** | Message + Patch | 数据结构定义，状态管理 |

---

## 🔄 核心流程

### 智能体处理流程

```mermaid
flowchart TD
    A[用户发送消息] --> B{检查智能体状态}
    B -->|正在处理中| C[返回429错误<br/>请等待完成]
    B -->|空闲状态| D[创建用户消息<br/>启动智能体协程]
    
    D --> E[智能体开始处理]
    E --> F[评估当前处境<br/>决定是否继续]
    F -->|需要处理| G[提示词策略识别<br/>用户输入类型]
    F -->|无需处理| Z[任务完成]
    
    G --> H{输入类型判断}
    H -->|chat普通聊天| I[生成聊天提示词<br/>无验证器]
    H -->|create_problem| J[生成创建问题提示词<br/>有验证器]
    H -->|query_problems| K[生成查询提示词<br/>有验证器]
    H -->|update_problem| L[生成更新提示词<br/>有验证器]
    
    I --> M[调用LLM<br/>_call_llm_with_retry]
    J --> M
    K --> M
    L --> M
    
    M --> N{是否有验证器}
    N -->|无验证器| O[LLM流式生成<br/>返回文本内容]
    N -->|有验证器| P[LLM + XML解析 + 验证<br/>统一重试机制]
    
    O --> Q[发布内容Patch<br/>流式传输给前端]
    P --> R{解析验证是否成功}
    R -->|失败| S[触发重试机制<br/>指数回退延迟]
    R -->|成功| T[获得结构化输出<br/>BaseModel对象]
    
    S --> U{重试次数检查}
    U -->|未超限| V[回溯消息状态<br/>重新执行]
    U -->|超过限制| W[发布错误Patch<br/>终止处理]
    V --> M
    
    T --> X[处理结构化输出<br/>执行数据库行动]
    X --> Y[创建快照<br/>发布行动结果Patch]
    
    Q --> F
    Y --> F
    W --> Z
    
    Z --> AA[发布完成状态<br/>智能体变为空闲]
    
    style A fill:#e1f5fe
    style Z fill:#c8e6c9
    style W fill:#ffcdd2
    style M fill:#fff3e0
    style P fill:#f3e5f5
    style X fill:#e8f5e8
```

### SSE流式传输流程

```mermaid
flowchart TD
    A[SSE连接建立] --> B[订阅ProjectManager<br/>patch消息队列]
    B --> C[异步监听<br/>patch事件流]
    
    C --> D{收到新Patch}
    D -->|thinking_delta| E[发送思考过程<br/>event: patch]
    D -->|content_delta| F[发送内容增量<br/>event: patch]
    D -->|action完成| G[发送行动结果<br/>包含snapshot对象]
    D -->|finished: true| H[发送完成标记<br/>关闭连接]
    D -->|rollback: true| I[发送回溯信号<br/>清理后续消息]
    
    E --> J[前端实时显示<br/>思考过程]
    F --> K[前端实时显示<br/>回复内容]
    G --> L[前端更新数据库<br/>snapshot对象替换]
    I --> M[前端回溯状态<br/>删除后续消息]
    
    J --> C
    K --> C
    L --> C
    M --> C
    H --> N[连接关闭<br/>清理资源]
    
    style A fill:#e1f5fe
    style H fill:#c8e6c9
    style N fill:#f5f5f5
    style G fill:#e8f5e8
    style I fill:#fff3e0
```

### 重试机制流程

```mermaid
flowchart TD
    A[重试机制触发] --> B[检查异常类型]
    B --> C{是否可重试错误}
    C -->|网络错误<br/>超时错误| D[计算延迟时间<br/>指数回退算法]
    C -->|验证错误<br/>格式错误| E[发布不可重试错误<br/>终止流程]
    
    D --> F{重试次数检查}
    F -->|未超过限制| G[回溯到指定消息ID<br/>rollback_message_id]
    F -->|超过限制| H[发布重试失败通知<br/>抛出最后异常]
    
    G --> I[发布重试通知Patch<br/>显示等待时间]
    I --> J[异步等待<br/>await asyncio.sleep]
    J --> K[重新执行函数<br/>LLM+解析+验证]
    
    K --> L{执行结果}
    L -->|成功| M[返回结果<br/>更新统计信息]
    L -->|再次失败| A
    
    style A fill:#fff3e0
    style E fill:#ffcdd2
    style H fill:#ffcdd2
    style M fill:#c8e6c9
    style K fill:#f3e5f5
```

---

## ⏱️ 交互时序

### 完整消息处理时序

```mermaid
sequenceDiagram
    participant 前端 as 前端客户端
    participant Router as AgentsRouter
    participant PM as ProjectManager
    participant Agent as SimpleAgent
    participant Strategy as PromptStrategy
    participant LLM as MockLLMClient
    participant Parser as XMLParser
    participant DM as DataManager
    
    前端->>Router: POST /agents/messages<br/>{content, title, agent_name}
    Router->>PM: 获取指定智能体
    PM->>Agent: 检查处理状态
    Agent-->>Router: 返回状态检查结果
    
    alt 智能体空闲
        Router->>PM: 启动SSE流
        PM->>Agent: process_user_message(content, title)
        Agent->>PM: 发布用户消息Patch
        PM->>前端: SSE: 用户消息事件
        
        Agent->>Agent: 启动智能体协程
        Agent->>Strategy: get_prompt_and_validator(content)
        Strategy-->>Agent: 返回(prompt, validator)
        
        Agent->>LLM: _call_llm_with_retry(prompt, title, validator)
        
        alt 有验证器
            LLM->>LLM: stream_generate(prompt, message_id)
            loop 流式生成
                LLM->>PM: 发布thinking_delta Patch
                PM->>前端: SSE: 思考过程事件
                LLM->>PM: 发布content_delta Patch
                PM->>前端: SSE: 内容增量事件
            end
            LLM-->>Agent: 返回完整content
            
            Agent->>Parser: extract_xml_from_content(content)
            Parser-->>Agent: 返回XML片段
            Agent->>Parser: xml_to_dict(xml_fragment)
            Parser-->>Agent: 返回数据字典
            Agent->>Parser: validate_with_pydantic(data, validator)
            Parser-->>Agent: 返回验证对象
            
            Agent->>Agent: _handle_structured_output(result)
            Agent->>DM: execute_action(action_type, params)
            DM->>DM: 创建快照
            DM-->>Agent: 返回执行结果{success, snapshot_id}
            
            Agent->>PM: 发布行动结果Patch
            PM->>前端: SSE: 行动完成事件<br/>(包含snapshot对象)
        else 无验证器
            LLM->>LLM: stream_generate(prompt, message_id)
            loop 流式生成
                LLM->>PM: 发布content_delta Patch
                PM->>前端: SSE: 内容增量事件
            end
            LLM->>PM: 发布完成Patch
            PM->>前端: SSE: 完成事件
        end
        
        Agent->>PM: 发布最终完成Patch
        PM->>前端: SSE: 连接关闭
    else 智能体忙碌
        Router-->>前端: HTTP 429: 智能体正在处理中
    end
```

### 重试机制时序

```mermaid
sequenceDiagram
    participant Agent as SimpleAgent
    participant Retry as RetryWrapper
    participant LLM as MockLLMClient
    participant Parser as XMLParser
    participant PM as ProjectManager
    
    Agent->>Retry: execute_with_retry(llm_parse_validate)
    
    loop 重试循环 (最多3次)
        Retry->>Retry: 记录尝试次数
        
        Retry->>LLM: stream_generate(prompt, message_id)
        alt LLM调用成功
            LLM-->>Retry: 返回完整content
            Retry->>Parser: extract_xml_from_content(content)
            
            alt XML提取成功
                Parser-->>Retry: 返回XML片段
                Retry->>Parser: xml_to_dict(xml_fragment)
                
                alt XML解析成功
                    Parser-->>Retry: 返回数据字典
                    Retry->>Parser: validate_with_pydantic(data, validator)
                    
                    alt 验证成功
                        Parser-->>Retry: 返回验证对象
                        Retry-->>Agent: 返回最终结果
                    else 验证失败
                        Parser->>Parser: 抛出XMLValidationError
                        Retry->>Retry: 检查错误类型(不可重试)
                        Retry->>PM: 发布错误通知Patch
                        Retry->>Agent: 抛出验证异常
                    end
                else XML解析失败
                    Parser->>Parser: 抛出XMLValidationError
                    Retry->>Retry: 检查错误类型(不可重试)
                    Retry->>PM: 发布错误通知Patch
                    Retry->>Agent: 抛出解析异常
                end
            else XML提取失败
                Retry->>Retry: 检查错误类型(不可重试)
                Retry->>PM: 发布错误通知Patch
                Retry->>Agent: 抛出提取异常
            end
        else LLM调用失败
            LLM->>LLM: 抛出NetworkError/TimeoutError
            Retry->>Retry: 检查错误类型(可重试)
            
            alt 未超过重试限制
                Retry->>PM: 发布回溯Patch(rollback_message_id)
                Retry->>Retry: 计算延迟时间(指数回退)
                Retry->>PM: 发布重试通知Patch
                Retry->>Retry: await asyncio.sleep(delay)
                Note over Retry: 继续下一次重试
            else 超过重试限制
                Retry->>PM: 发布重试失败Patch
                Retry->>Agent: 抛出最后异常
            end
        end
    end
```

---

## 🧪 测试体系

### 测试架构

| 测试类型 | 文件 | 覆盖范围 | 运行方式 |
|----------|------|----------|----------|
| **单元测试** | `test_unit.py` | 组件独立功能 | `pytest tests/test_unit.py -v` |
| **集成测试** | `test_integration.py` | 端到端流程 | `pytest tests/test_integration.py -v` |
| **API测试** | `test_api.py` | HTTP接口 | `pytest tests/test_api.py -v` |
| **快速验证** | `quick_test.py` | 核心功能 | `python quick_test.py` |

### 单元测试用例

#### 1. 消息模型测试 (TestMessage)
```bash
# 测试消息创建和补丁应用
pytest tests/test_unit.py::TestMessage::test_message_creation -v
pytest tests/test_unit.py::TestMessage::test_patch_application -v
```

**测试内容**：
- ✅ Message对象创建和字段验证
- ✅ Patch补丁应用逻辑
- ✅ 增量更新vs替换更新机制
- ✅ 时间戳自动更新

#### 2. 智能体验证器测试 (TestSimpleAgentValidators)
```bash
# 测试验证器和提示词策略
pytest tests/test_unit.py::TestSimpleAgentValidators -v
```

**测试内容**：
- ✅ CreateResearchProblemOutput验证器
- ✅ PydanticV2字段验证规则
- ✅ PromptStrategy输入类型识别
- ✅ 提示词模板选择逻辑

#### 3. 数据管理器测试 (TestDataManager)
```bash
# 测试数据持久化和快照
pytest tests/test_unit.py::TestDataManager -v
```

**测试内容**：
- ✅ 研究问题CRUD操作
- ✅ 快照创建和回溯
- ✅ 数据库状态管理
- ✅ 执行结果返回格式

#### 4. 项目管理器测试 (TestProjectManager)
```bash
# 测试消息管理和发布订阅
pytest tests/test_unit.py::TestProjectManager -v
```

**测试内容**：
- ✅ 消息历史管理
- ✅ Patch发布订阅机制
- ✅ 智能体注册和获取
- ✅ 并发消息处理

#### 5. XML解析器测试 (TestXMLParser)
```bash
# 测试XML解析和验证
pytest tests/test_unit.py::TestXMLParser -v
```

**测试内容**：
- ✅ XML转字典解析
- ✅ PydanticV2验证集成
- ✅ XML片段提取
- ✅ 错误处理和异常

#### 6. 重试机制测试 (TestRetryWrapper)
```bash
# 测试重试逻辑
pytest tests/test_unit.py::TestRetryWrapper -v
```

**测试内容**：
- ✅ 指数回退算法
- ✅ 可重试vs不可重试错误
- ✅ 重试统计信息
- ✅ 回溯机制

### 集成测试用例

#### 1. 基本消息流程测试
```bash
pytest tests/test_integration.py::TestIntegration::test_basic_message_flow -v
```

**测试内容**：
- 🔄 用户消息→智能体处理→响应生成
- 🔄 SSE流式传输完整链路
- 🔄 Patch发布订阅机制
- 🔄 消息历史记录

#### 2. XML解析和行动执行测试
```bash
pytest tests/test_integration.py::TestIntegration::test_xml_parsing_and_action_execution -v
```

**测试内容**：
- 🔄 提示词策略自动识别
- 🔄 LLM生成→XML解析→验证
- 🔄 结构化输出→数据库行动
- 🔄 快照创建和前端同步

#### 3. 错误重试机制测试
```bash
pytest tests/test_integration.py::TestIntegration::test_error_retry_mechanism -v
```

**测试内容**：
- 🔄 网络错误模拟和重试
- 🔄 重试通知消息发布
- 🔄 指数回退延迟验证
- 🔄 重试失败处理

#### 4. SSE断连重连测试
```bash
pytest tests/test_integration.py::TestIntegration::test_sse_reconnection -v
```

**测试内容**：
- 🔄 连接中断模拟
- 🔄 继续消息功能
- 🔄 历史状态同步
- 🔄 实时流恢复

### API测试用例

#### 1. 基本接口测试
```bash
pytest tests/test_api.py::TestAPI::test_root_endpoint -v
pytest tests/test_api.py::TestAPI::test_health_check -v
```

#### 2. 智能体接口测试
```bash
pytest tests/test_api.py::TestAPI::test_send_message -v
pytest tests/test_api.py::TestAPI::test_message_history -v
pytest tests/test_api.py::TestAPI::test_stop_generation -v
```

#### 3. 测试接口验证
```bash
pytest tests/test_api.py::TestAPI::test_session_status -v
pytest tests/test_api.py::TestAPI::test_llm_configuration -v
```

### 快速验证脚本

```bash
# 运行所有核心功能验证
python quick_test.py
```

**验证项目**：
- ✅ 验证器功能测试
- ✅ 提示词策略测试  
- ✅ XML解析测试
- ✅ LLM输出测试

### 批量测试运行

#### 运行所有测试
```bash
# 运行完整测试套件
pytest tests/ -v

# 并行运行加速
pytest tests/ -v -n auto
```

#### 按类型运行
```bash
# 仅单元测试
pytest tests/test_unit.py -v

# 仅集成测试  
pytest tests/test_integration.py -v

# 仅API测试
pytest tests/test_api.py -v
```

#### 按功能模块运行
```bash
# 测试智能体相关
pytest -k "agent" -v

# 测试消息处理
pytest -k "message" -v

# 测试XML解析
pytest -k "xml" -v

# 测试重试机制
pytest -k "retry" -v
```

### 测试配置和环境

#### 启动测试服务器
```bash
# 启动开发服务器
python main.py

# 服务器运行在 http://localhost:8080
```

#### 测试数据准备
```bash
# 重置测试环境
rm -rf __pycache__ tests/__pycache__

# 安装依赖
pip install -r requirements.txt
```

#### 调试模式运行
```bash
# 详细输出模式
pytest tests/ -v -s

# 遇到失败时停止
pytest tests/ -v -x

# 重新运行失败的测试
pytest tests/ --lf
```

---

## 🚀 快速开始

### 环境准备

```bash
# 1. 进入项目目录
cd /path/to/ResVizCopilot-2.0.0/tests/stream_case2

# 2. 安装依赖
pip install -r requirements.txt

# 3. 验证核心功能
python quick_test.py
```

### 启动服务

```bash
# 启动开发服务器
python main.py

# 服务运行在 http://localhost:8080
```

### 使用示例

#### 1. 发送消息（普通聊天）
```bash
curl -X POST "http://localhost:8080/agents/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "你好", "title": "问候"}'
```

#### 2. 发送消息（创建研究问题）
```bash
curl -X POST "http://localhost:8080/agents/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "请创建一个关于AI安全的研究问题", "title": "创建研究问题"}'
```

#### 3. 查看消息历史
```bash
curl "http://localhost:8080/agents/messages/history"
```

#### 4. 获取会话状态
```bash
curl "http://localhost:8080/test/session/status"
```

### 前端集成示例

```javascript
// SSE连接示例
const eventSource = new EventSource('/agents/messages');

eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.event === 'patch') {
        const patch = data.data;
        
        // 处理不同类型的更新
        if (patch.thinking_delta) {
            updateThinking(patch.thinking_delta);
        }
        
        if (patch.content_delta) {
            updateContent(patch.content_delta);
        }
        
        if (patch.action_title && patch.snapshot) {
            updateDatabase(patch.snapshot);
        }
        
        if (patch.finished) {
            eventSource.close();
        }
    }
};

// 发送消息
async function sendMessage(content) {
    const response = await fetch('/agents/messages', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            content: content,
            title: '用户消息',
            agent_name: 'default'
        })
    });
    
    return response;
}
```

### 开发调试

#### 配置LLM模拟错误
```bash
curl -X POST "http://localhost:8080/test/llm/simulate-error" \
  -H "Content-Type: application/json" \
  -d '{"error_rate": 0.3, "error_types": ["network", "timeout"]}'
```

#### 调整响应延迟
```bash
curl -X POST "http://localhost:8080/test/llm/delay" \
  -H "Content-Type: application/json" \
  -d '{"delay_per_token": 0.1}'
```

#### 停止生成
```bash
curl -X POST "http://localhost:8080/agents/messages/stop"
```

---

## 📈 性能特性

### 核心优势

| 特性 | 传统方案 | 本方案 | 改进效果 |
|------|----------|---------|----------|
| **重试范围** | 单独重试LLM | LLM+解析+验证统一重试 | 🔄 更完整的错误恢复 |
| **类型安全** | 手动解析验证 | PydanticV2自动验证 | ✅ 零运行时类型错误 |
| **提示词管理** | 硬编码模板 | 智能策略选择 | 🎯 自适应输入处理 |
| **流式传输** | 简单SSE | ProjectManager解耦 | ⚡ 协程独立运行 |
| **错误处理** | 基础重试 | 指数回退+分类处理 | 🛡️ 更强错误恢复能力 |

### 扩展性设计

- **模块化架构**：各层职责清晰，易于替换和扩展
- **插件化验证器**：新行动类型仅需添加验证器
- **策略模式**：提示词策略独立，支持动态扩展
- **统一接口**：AgentBase抽象接口，支持多种智能体实现

---

## 🏆 项目总结

ResVizCopilot 2.0流式智能体系统通过重图表轻文字的设计理念，提供了一套完整的智能体协程解耦解决方案。

### 🎯 核心成就

- **🔄 统一重试机制**：LLM调用、XML解析、验证一体化重试
- **🎭 智能提示词策略**：自动识别输入类型，选择最佳处理方式  
- **📝 类型安全验证**：PydanticV2确保输出格式完全可控
- **🔗 SSE协程解耦**：智能体独立运行，前端实时响应
- **📸 快照状态管理**：支持状态回溯和错误恢复

### 🛠️ 技术价值

通过丰富的**Mermaid图表**展示系统设计：
- **类图**：清晰展现组件关系和职责分工
- **流程图**：详细描述核心业务逻辑和处理流程
- **时序图**：完整呈现组件间交互和消息流转

### 🧪 测试保障

全面的测试体系确保系统稳定性：
- **单元测试**：组件功能验证
- **集成测试**：端到端流程验证  
- **API测试**：接口规范验证
- **快速验证**：核心功能一键检查

该系统为智能体协程解耦提供了一个**健壮、可扩展、易维护**的完整解决方案。

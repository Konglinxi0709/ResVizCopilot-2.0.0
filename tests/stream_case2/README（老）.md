# ResVizCopilot 2.0 智能体模块重构案例

## 概述

本案例展示了智能体模块的重大重构，将LLM调用、XML解析和验证整合到一个统一的重试机制中，实现了更加灵活和健壮的智能体架构。

## 重构要点

### 1. 核心架构改进

#### AgentBase 基类优化
- **删除分离的解析函数**：移除了 `_parse_output_with_retry` 和 `_parse_output` 抽象方法
- **统一重试机制**：将LLM调用、XML解析、验证全部纳入同一个重试范围
- **可选验证器支持**：`_call_llm_with_retry` 增加可选的PydanticV2验证器参数

#### 新的调用流程
```python
# 有验证器：LLM + XML解析 + 验证（全部重试）
result = await self._call_llm_with_retry(
    prompt, title, validator, rollback_id
)

# 无验证器：仅LLM调用（重试）
content = await self._call_llm_with_retry(
    prompt, title, None, rollback_id
)
```

### 2. SimpleAgent 完全重构

#### 提示词策略模式
- **PromptStrategy 类**：智能识别用户输入类型，选择对应的提示词模板
- **多种提示词类型**：
  - `chat`：普通聊天（无验证器）
  - `create_problem`：创建研究问题（有验证器）
  - `query_problems`：查询问题（有验证器）
  - `update_problem`：更新问题（有验证器）

#### 验证器模型系统
- **专用验证器**：每种输出类型对应专门的PydanticV2验证器
- **完整验证**：验证器定义整个XML结构，包括title和params
- **类型安全**：确保输出格式完全符合预期

#### 处理流程简化
```python
# 1. 获取提示词和验证器
prompt, validator = self.prompt_strategy.get_prompt_and_validator(user_content)

# 2. 调用LLM（带可选验证）
result = await self._call_llm_with_retry(prompt, title, validator, rollback_id)

# 3. 处理结果
if isinstance(result, BaseModel):
    # 结构化输出：执行行动
    await self._handle_structured_output(result)
else:
    # 文本输出：无需进一步处理
    logger.info("完成文本回复，无需执行行动")
```

### 3. MockLLMClient 智能化

#### 响应类型自动识别
- **关键词匹配**：根据提示词内容智能选择响应类型
- **模拟真实场景**：不同类型提示词产生对应的输出格式
- **流式XML输出**：支持包含XML的流式响应

#### 多种响应模板
```python
response_templates = {
    "chat": [...],           # 纯文本响应
    "create_problem": [...], # 包含XML的结构化响应
    "query_problems": [...], # 查询类响应
    "update_problem": [...]  # 更新类响应
}
```

## 技术特性

### 1. 统一重试机制
- **范围扩大**：LLM调用、XML解析、验证失败都会触发重试
- **错误分类**：区分可重试错误（网络、超时）和不可重试错误（格式、验证）
- **状态回溯**：重试时可回溯到指定消息状态

### 2. 类型安全的验证
- **PydanticV2集成**：使用现代验证框架确保数据质量
- **结构化输出**：验证器定义完整的输出结构
- **错误详情**：验证失败时提供详细的错误信息

### 3. 灵活的提示词管理
- **策略模式**：提示词选择逻辑与智能体核心逻辑分离
- **随机变化**：同类型提示词有多个变体，增加输出多样性
- **对话计数**：考虑对话轮次进行智能选择

### 4. 模拟真实LLM行为
- **智能响应**：根据输入内容选择合适的响应类型
- **流式输出**：模拟真实的流式生成过程
- **XML混合**：支持文本+XML混合输出的真实场景

## 文件结构

```
core/
├── agent_base.py              # 智能体抽象基类
├── simple_agent.py            # 简单智能体实现
├── simple_agent_validators.py # 智能体专用验证器
├── simple_agent_prompts.py    # 提示词策略管理
├── llm_client.py              # 模拟LLM客户端
├── retry_wrapper.py           # 重试机制包装器
└── ...

tests/
├── test_unit.py               # 单元测试
├── test_integration.py        # 集成测试
└── ...

utils/
├── xml_parser.py              # XML解析和验证工具
└── ...
```

## 使用示例

### 基本使用
```python
# 创建智能体
    agent = SimpleAgent(
        publish_callback=project_manager.publish_patch,
    execute_action_func=data_manager.execute_action
)

# 处理用户消息
await agent.process_user_message(
    "请创建一个关于AI安全的研究问题",
    "用户请求"
)
```

### 自定义验证器
```python
class CustomActionOutput(BaseModel):
    title: str = Field(..., description="行动标题")
    params: CustomParams = Field(..., description="自定义参数")

# 在提示词策略中注册
validator_mapping = {
    PromptType.CUSTOM: CustomActionOutput
}
```

### 扩展提示词类型
```python
# 添加新的提示词类型
class PromptType(Enum):
    CUSTOM_TYPE = "custom_type"

# 添加对应的模板和验证器
prompt_templates[PromptType.CUSTOM_TYPE] = [...]
validator_mapping[PromptType.CUSTOM_TYPE] = CustomValidator
```

## 测试覆盖

### 单元测试
- ✅ 验证器功能测试
- ✅ 提示词策略测试
- ✅ XML解析和验证测试
- ✅ LLM客户端响应测试

### 集成测试
- ✅ 端到端消息流程测试
- ✅ XML解析和行动执行测试
- ✅ 错误重试机制测试

### 快速验证
```bash
# 运行快速验证脚本
python quick_test.py

# 运行特定测试
python -m pytest tests/test_unit.py::TestSimpleAgentValidators -v
```

## 性能优化

### 1. 减少重复解析
- 验证器复用，避免重复编译
- XML解析结果缓存
- 提示词模板预编译

### 2. 智能重试策略
- 指数回退算法
- 错误类型识别
- 最大重试次数限制

### 3. 内存优化
- 流式处理，避免大块内存占用
- 及时清理临时对象
- 适当的对象池化

## 扩展指南

### 添加新的行动类型
1. 在 `simple_agent_validators.py` 中定义验证器
2. 在 `simple_agent_prompts.py` 中添加提示词类型
3. 在 `llm_client.py` 中添加对应的响应模板
4. 编写相应的测试用例

### 集成新的LLM
1. 实现 LLM 客户端接口
2. 保持流式输出的 patch 发布机制
3. 确保错误类型正确分类
4. 适配重试机制

### 自定义验证逻辑
1. 继承 `BaseModel` 创建验证器
2. 使用 `@validator` 装饰器添加自定义验证
3. 在 XML 解析器中注册验证器
4. 测试验证规则的正确性

## 总结

本次重构实现了：
- **架构简化**：统一的调用和重试机制
- **类型安全**：完整的验证器体系
- **模拟真实**：接近真实LLM的行为模式
- **易于扩展**：清晰的模块化设计
- **测试完备**：全面的单元和集成测试

重构后的智能体模块具备了更好的健壮性、可维护性和可扩展性，为后续的功能开发奠定了坚实的基础。
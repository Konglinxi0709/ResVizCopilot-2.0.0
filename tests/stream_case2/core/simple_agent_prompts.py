"""
SimpleAgent的提示词策略
定义不同类型的提示词及其对应的验证器
"""
import random
from typing import Optional, Type, Tuple
from enum import Enum
from pydantic import BaseModel

from .simple_agent_validators import (
    CreateResearchProblemOutput, 
    QueryProblemsOutput, 
    UpdateProblemOutput
)


class PromptType(Enum):
    """提示词类型枚举"""
    CHAT = "chat"  # 普通聊天，无验证器
    CREATE_PROBLEM = "create_problem"  # 创建研究问题，有验证器
    QUERY_PROBLEMS = "query_problems"  # 查询问题，有验证器  
    UPDATE_PROBLEM = "update_problem"  # 更新问题，有验证器


class PromptStrategy:
    """
    提示词策略类
    
    功能：
    1. 根据用户输入判断应该使用哪种提示词类型
    2. 生成对应的提示词文本
    3. 返回对应的验证器类
    """
    
    def __init__(self):
        """初始化提示词策略"""
        self.conversation_count = 0
        
        # 提示词模板映射
        self.prompt_templates = {
            PromptType.CHAT: [
                "你是一个智能助手，请根据用户的问题给出有帮助的回答。\n\n用户问题：{user_input}\n\n请直接回答用户的问题。",
                "作为AI助手，我会根据你的需求提供帮助。\n\n你的问题：{user_input}\n\n让我来为你解答。",
                "我是你的智能助理，很高兴为你服务。\n\n你想了解：{user_input}\n\n我会尽力提供有用的信息。"
            ],
            
            PromptType.CREATE_PROBLEM: [
                """你是一个研究助手，专门帮助用户创建研究问题。根据用户的需求，你需要创建一个新的研究问题。

用户需求：{user_input}

请分析用户的需求，然后使用以下XML格式创建一个研究问题：

<action>
<title>create_research_problem</title>
<params>
<title>研究问题的标题</title>
<significance>详细描述这个研究问题的重要性和意义</significance>
<criteria>描述研究的标准、方法和预期成果</criteria>
</params>
</action>

请确保XML格式正确，并且内容丰富有意义。""",

                """我是研究问题创建专家。基于你的输入，我将为你设计一个完整的研究问题。

你的研究方向：{user_input}

我需要为你创建一个结构化的研究问题，包含标题、研究意义和评估标准：

<action>
<title>create_research_problem</title>
<params>
<title>针对你需求的专业研究问题标题</title>
<significance>阐述该研究的理论价值和实践意义</significance>
<criteria>制定合理的研究标准和成功指标</criteria>
</params>
</action>

让我为你量身定制这个研究问题。"""
            ],
            
            PromptType.QUERY_PROBLEMS: [
                """作为研究管理助手，我帮你查询现有的研究问题。

你的查询需求：{user_input}

我将搜索相关的研究问题：

<action>
<title>query_problems</title>
<params>
<keyword>基于你的需求提取的关键词</keyword>
<limit>10</limit>
</params>
</action>

让我为你找到最相关的研究问题。""",

                """我可以帮你检索研究问题数据库。

搜索请求：{user_input}

执行搜索操作：

<action>
<title>query_problems</title>
<params>
<keyword>从你的请求中识别的搜索关键词</keyword>
<limit>15</limit>
</params>
</action>

正在为你查询匹配的研究问题。"""
            ],
            
            PromptType.UPDATE_PROBLEM: [
                """我是研究问题更新助手，帮你修改现有的研究问题。

修改请求：{user_input}

我将更新指定的研究问题：

<action>
<title>update_problem</title>
<params>
<id>从你的请求中识别的问题ID</id>
<title>更新后的标题</title>
<significance>修订后的研究意义</significance>
<criteria>调整后的研究标准</criteria>
</params>
</action>

正在为你更新研究问题。"""
            ]
        }
        
        # 验证器映射
        self.validator_mapping = {
            PromptType.CHAT: None,
            PromptType.CREATE_PROBLEM: CreateResearchProblemOutput,
            PromptType.QUERY_PROBLEMS: QueryProblemsOutput,
            PromptType.UPDATE_PROBLEM: UpdateProblemOutput
        }
    
    def determine_prompt_type(self, user_input: str) -> PromptType:
        """
        根据用户输入判断提示词类型
        
        Args:
            user_input: 用户输入内容
            
        Returns:
            提示词类型
        """
        user_input_lower = user_input.lower()
        
        # 简单的关键词匹配逻辑
        if any(keyword in user_input_lower for keyword in ["创建", "建立", "新建", "新的", "研究问题", "问题"]):
            return PromptType.CREATE_PROBLEM
        elif any(keyword in user_input_lower for keyword in ["查询", "搜索", "查找", "寻找", "列出"]):
            return PromptType.QUERY_PROBLEMS
        elif any(keyword in user_input_lower for keyword in ["更新", "修改", "编辑", "改变"]):
            return PromptType.UPDATE_PROBLEM
        else:
            # 根据对话轮次随机选择（模拟真实场景）
            if self.conversation_count == 0:
                # 第一轮对话：有40%概率创建问题，60%普通聊天
                return random.choices(
                    [PromptType.CREATE_PROBLEM, PromptType.CHAT],
                    weights=[0.4, 0.6]
                )[0]
            else:
                # 后续对话：更多样化的选择
                return random.choices(
                    [PromptType.CHAT, PromptType.CREATE_PROBLEM, PromptType.QUERY_PROBLEMS],
                    weights=[0.5, 0.3, 0.2]
                )[0]
    
    def get_prompt_and_validator(self, user_input: str) -> Tuple[str, Optional[Type[BaseModel]]]:
        """
        获取提示词和对应的验证器
        
        Args:
            user_input: 用户输入内容
            
        Returns:
            (提示词文本, 验证器类或None)
        """
        prompt_type = self.determine_prompt_type(user_input)
        
        # 随机选择该类型的一个模板
        templates = self.prompt_templates[prompt_type]
        template = random.choice(templates)
        
        # 生成提示词
        prompt = template.format(user_input=user_input)
        
        # 获取验证器
        validator = self.validator_mapping[prompt_type]
        
        self.conversation_count += 1
        
        return prompt, validator
    
    def reset_conversation(self):
        """重置对话计数"""
        self.conversation_count = 0

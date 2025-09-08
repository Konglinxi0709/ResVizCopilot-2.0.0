from .global_prompt import (
    ROLE_AND_RULES, 
    CURRENT_RESEARCH_TREE_FULL_TEXT_EXPLANATION, 
    CURRENT_RESEARCH_PROBLEM_EXPLANATION, 
    EXPERT_SOLUTIONS_OF_ALL_ANCESTOR_PROBLEMS_EXPLANATION, 
    ROOT_PROBLEM_EXPLANATION, 
    OTHER_SOLUTIONS_OF_CURRENT_PROBLEM_EXPLANATION, 
    XML_FORMAT_RULE, 
    CURRENT_SOLUTION_EXPLANATION, 
    EXPERT_SOLUTIONS_OF_ALL_DESCENDANT_PROBLEMS_EXPLANATION,
    MESSAGE_LIST_EXPLANATION,
)
from backend.database.schemas.request_models import (
    ProblemRequest,
    SolutionRequest,
)
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Literal, Optional, Dict, Any
from backend.database.schemas.research_tree import ProblemType


# 验证器模型
class HandleModificationRequestsResponse(BaseModel):
    """修改请求处理响应验证器"""
    decision: Literal["accept", "reply"] = Field(description="决策类型：accept表示同意修改，reply表示回复用户")
    reasoning: str = Field(description="决策理由，不超过100字")
    modification_plan: Optional[str] = Field(default=None, description="修改计划，仅在decision为accept时提供，不超过300字")
    response_to_user: Optional[str] = Field(default=None, description="对用户的回复，仅在decision为reply时提供")
    
    @model_validator(mode='before')
    @classmethod
    def extract_decision_from_xml_structure(cls, data):
        """
        从XML解析后的数据结构中提取正确的字段值
        
        处理XML解析器输出的格式：
        {
            'decision': {
                'reasoning': '...',
                'response_to_user': '...',
                '_attributes': {'type': 'reply'}
            }
        }
        
        转换为验证器期望的格式：
        {
            'decision': 'reply',
            'reasoning': '...',
            'response_to_user': '...'
        }
        """
        if isinstance(data, dict):
            # 检查是否是XML解析后的结构
            if 'decision' in data and isinstance(data['decision'], dict):
                decision_data = data['decision']
                
                # 从属性中提取decision类型
                if '_attributes' in decision_data and 'type' in decision_data['_attributes']:
                    decision_type = decision_data['_attributes']['type']
                    
                    # 构建新的数据结构
                    new_data = {
                        'decision': decision_type,
                        'reasoning': decision_data.get('reasoning', ''),
                        'response_to_user': decision_data.get('response_to_user', ''),
                        'modification_plan': decision_data.get('modification_plan', None)
                    }
                    
                    # 清理空字符串
                    if new_data['reasoning'] == '':
                        new_data['reasoning'] = None
                    if new_data['response_to_user'] == '':
                        new_data['response_to_user'] = None
                    if new_data['modification_plan'] == '':
                        new_data['modification_plan'] = None
                    
                    return new_data
        
        return data
    
    @field_validator('modification_plan')
    @classmethod
    def validate_modification_plan(cls, v, info):
        """验证修改计划字段"""
        decision = info.data.get('decision') if info.data else None
        
        if decision == "accept":
            if not v or len(v.strip()) == 0:
                raise ValueError('当决策为accept时，必须提供修改计划')
            return v.strip()
        else:
            # 当decision为reply时，modification_plan应该为None
            if v is not None and len(v.strip()) > 0:
                raise ValueError('当决策为reply时，不应提供修改计划')
            return None
    
    @field_validator('response_to_user')
    @classmethod
    def validate_response_to_user(cls, v, info):
        """验证对用户回复字段"""
        decision = info.data.get('decision') if info.data else None
        
        if decision == "reply":
            if not v or len(v.strip()) == 0:
                raise ValueError('当决策为reply时，必须提供对用户的回复')
            return v.strip()
        else:
            # 当decision为accept时，response_to_user应该为None
            if v is not None and len(v.strip()) > 0:
                raise ValueError('当决策为accept时，不应提供对用户的回复')
            return None
    
    @field_validator('decision')
    @classmethod
    def validate_decision(cls, v):
        """验证决策字段"""
        if v not in ["accept", "reply"]:
            raise ValueError('决策类型必须是accept或reply')
        return v

    def to_content(self) -> str:
        if self.decision == "accept":
            return f"【做出修改的理由】: {self.reasoning}\n" \
                   f"【修改计划】: {self.modification_plan}\n"
        else:
            return f"【做出回复的理由】: {self.reasoning}\n" \
                   f"【对用户的回复】: {self.response_to_user}\n"


HANDLE_MODIFICATION_REQUESTS_PROMPT = f"""
{ROLE_AND_RULES}
<task>
现在{{supervisor_name}}对你的解决方案提出了疑问或修改要求，你需要理解这些疑问或修改要求，并决定按要求修改还是回复他，大致包含以下几步。
1. 接收信息：
    1. 理解当前的完整研究过程，了解团队的研究目标和已经进行过的思考和求证，并掌握其中得到的所有事实结论
    2. 理解你自己的研究方案，这代表着你之前的工作思路
    3. 理解你和用户间的对话，了解用户修改要求背后的思考
2. 分析用户的要求，是只希望你回答问题，或是希望你修改解决方案中的思路或论述，还是希望你修改实际的方案计划
    0. 当且仅当用户的消息中存在“请修改”三个字，应视为要求修改，否则都视为希望你回复它。如果用户的消息极其像一个明确的修改要求，但不包含这三个字，你应该回复他，告诉他你需要更明确的要求才能修改。
    1. 如果用户希望你回答问题，你需要理解他的问题及背后的考虑，并回复他。除非用户明确要求直接修改，否则我建议你先多次回复用户，将所有细节讨论清楚且用户确认之后再做修改。
    2. 如果用户希望你修改思路或论述等，你需要判断这样修改后表达是否更准确，且是否与方案的其它部分保持思维统一。
        1. 如果修改后表达更准确，且与方案的其它部分保持思维统一，你需要制定修改计划，指导你的下一步修改工作。
        2. 如果修改后表达不准确，或与方案的其它部分不保持思维统一，你需要回复他，确认是否有更好的表达，或者是否要连同其他方案计划等部分一起修改。
    3. 如果用户希望你修改实际的方案计划，你需要分析用户的修改要求是否合理，是否存在问题
        1. 站在你之前的思路上，思考你当时没有考虑这种选择的原因，是因为这种选择确实很好只是你当时没有考虑到，还是因为你考虑到了但认为这种选择本身存在问题
        2. 如果按要求进行修改，是否比当前的解决方案更容易实施或能实现更大的研究价值
</task>
<specifications>
<descion>
<what>
你的决定。accept表示同意修改，reply表示回复用户。
<reasoning>
你的决策理由。不超过100字。
</reasoning>
<if type="accept">
<modification_plan>
为你准备如何修改做一个简要的计划，用来指导你自己之后的修改工作。不超过300字。
你的修改计划必须综合之前对话中用户所有的修改要求，列出修改清单，不要遗漏用户的任何一个没有撤销或否决的意见。
</modification_plan>
</if>
<if type="reply">
<response_to_user>
回复你的负责人，与他进行交流。你可以反驳他的观点，也可以向他提出一些问题来获取更多信息。
</response_to_user>
</if>
</what>
<constraints>
1. 如果对方的要求中明确希望得到你的回复，你必须选择回复他。
2. 如果你选择接受修改，你必须仔细思考确保修改后的方案更好，并制定修改计划。
</constraint>
</specifications>
<output_format>
你需要严格按以下XML格式输出，不要输出任何多余内容
<response>
<decision type="accept" | "reply">
<reasoning>决策理由</reasoning>
<if type="accept">
<modification_plan>修改计划</modification_plan>
</if>
<if type="reply">
<response_to_user>对用户的回复</response_to_user>
</if>
</decision>
</response>
</output_format>
<xml_format_rule>
{XML_FORMAT_RULE}
</xml_format_rule>
<environment_information>
<current_research_tree_full_text>
<content>
{{current_research_tree_full_text}}
</content>
<explanation>
{CURRENT_RESEARCH_TREE_FULL_TEXT_EXPLANATION}
</explanation>
</current_research_tree_full_text>
<current_research_problem>
<content>
{{current_research_problem}}
</content>
<explanation>
{CURRENT_RESEARCH_PROBLEM_EXPLANATION}
</explanation>
</current_research_problem>
<current_solution>
<content>
{{current_solution}}
</content>
<explanation>
{CURRENT_SOLUTION_EXPLANATION}
</explanation>
</current_solution>
<expert_solutions_of_all_ancestor_problems>
<content>
{{expert_solutions_of_all_ancestor_problems}}
</content>
<explanation>
{EXPERT_SOLUTIONS_OF_ALL_ANCESTOR_PROBLEMS_EXPLANATION}
</explanation>
</expert_solutions_of_all_ancestor_problems>
<other_solutions_of_current_problem>
<content>
{{other_solutions_of_current_problem}}
</content>
<explanation>
{OTHER_SOLUTIONS_OF_CURRENT_PROBLEM_EXPLANATION}
</explanation>
</other_solutions_of_current_problem>
<expert_solutions_of_all_descendant_problems>
<content>
{{expert_solutions_of_all_descendant_problems}}
</content>
<explanation>
{EXPERT_SOLUTIONS_OF_ALL_DESCENDANT_PROBLEMS_EXPLANATION}
</explanation>
</expert_solutions_of_all_descendant_problems>
<root_problem>
<content>
{{root_problem}}
</content>
<explanation>
{ROOT_PROBLEM_EXPLANATION}
</explanation>
</root_problem>
<message_list>
<content>
{{message_list}}
</content>
<explanation>
{MESSAGE_LIST_EXPLANATION}
</explanation>
</message_list>
<modification_request>
<content>
{{modification_request}}
</content>
<explanation>
{{supervisor_name}}对你提出的修改要求。
</explanation>
</modification_request>
</environment_information>
"""
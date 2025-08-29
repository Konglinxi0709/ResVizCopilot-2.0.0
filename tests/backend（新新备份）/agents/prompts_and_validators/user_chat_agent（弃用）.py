"""
用户提问智能体提示词和验证器
对应流程图中"用户对某个解决方案提出修改意见"入口
"""
from .global_prompt import ROLE_AND_RULES, CURRENT_RESEARCH_TREE_FULL_TEXT_EXPLANATION, CURRENT_RESEARCH_PROBLEM_EXPLANATION, EXPERT_SOLUTIONS_OF_ALL_ANCESTOR_PROBLEMS_EXPLANATION, ROOT_PROBLEM_EXPLANATION, OTHER_SOLUTIONS_OF_CURRENT_PROBLEM_EXPLANATION

from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# 导入ResearchSubProblem
from .create_solution import ResearchSubProblem


# 验证器模型
class UserFeedbackAnalysis(BaseModel):
    """用户反馈分析模型"""
    feedback_type: Literal["modification_request", "question", "clarification", "other"] = Field(description="反馈类型")
    main_concern: str = Field(description="主要关注点")
    specific_issues: List[str] = Field(description="具体问题列表")
    suggested_improvements: Optional[List[str]] = Field(default=None, description="建议的改进方向")


class SolutionModificationDecision(BaseModel):
    """解决方案修改决策模型"""
    decision: Literal["accept_modification", "reply_clarification", "reject_modification"] = Field(description="决策结果")
    reasoning: str = Field(description="决策理由")
    modification_plan: Optional[str] = Field(default=None, description="修改计划")
    response_to_user: str = Field(description="对用户的回复")


class ModifiedSolution(BaseModel):
    """修改后的解决方案模型"""
    title: str = Field(description="修改后的标题")
    top_level_thoughts: str = Field(description="修改后的顶层思考")
    implementation_plan: List[ResearchSubProblem] = Field(description="修改后的实施方案步骤列表")
    plan_justification: str = Field(description="修改后的方案论证")
    finishing_task: str = Field(description="修改后的收尾任务")
    modification_summary: str = Field(description="修改总结")


# 提示词模板
USER_FEEDBACK_ANALYSIS_PROMPT = f"""
{ROLE_AND_RULES}
<task>
分析用户对当前解决方案的反馈，理解用户的具体需求和关注点。
</task>
<specifications>
<analysis_requirements>
1. 识别反馈类型：修改请求、问题澄清、其他反馈
2. 提取主要关注点：用户最关心的问题是什么
3. 分析具体问题：列出用户提到的所有具体问题
4. 理解改进建议：用户希望如何改进解决方案
</analysis_requirements>
<output_format>
你需要严格按以下XML格式输出，不要输出任何多余内容
<response>
<feedback_type>反馈类型</feedback_type>
<main_concern>主要关注点</main_concern>
<specific_issues>
<issue>具体问题1</issue>
<issue>具体问题2</issue>
...
</specific_issues>
<suggested_improvements>
<improvement>建议改进1</improvement>
<improvement>建议改进2</improvement>
...
</suggested_improvements>
</response>
</output_format>
<environment_information>
<current_research_tree_full_text>
<content>
{{current_research_tree_full_text}}
</content>
<explanation>
{CURRENT_RESEARCH_TREE_FULL_TEXT_EXPLANATION}
</explanation>
</current_research_tree_full_text>
<current_solution>
<content>
{{current_solution}}
</content>
<explanation>
这是你当前负责的解决方案，包含完整的顶层思考、实施方案、方案论证等内容。
</explanation>
</current_solution>
<user_feedback>
<content>
{{user_feedback}}
</content>
<explanation>
用户对当前解决方案的反馈意见，你需要仔细分析并理解。
</explanation>
</user_feedback>
<visible_messages>
<content>
{{visible_messages}}
</content>
<explanation>
你可以看到的其他相关消息，包括用户和智能体的交流历史。
</explanation>
</visible_messages>
</environment_information>
"""


SOLUTION_MODIFICATION_DECISION_PROMPT = f"""
{ROLE_AND_RULES}
<task>
基于用户反馈分析，决定是否修改当前解决方案，并制定相应的行动计划。
</task>
<specifications>
<decision_factors>
1. 用户反馈的合理性：用户提出的问题是否确实存在
2. 修改的必要性：是否需要修改来解决用户关注的问题
3. 修改的可行性：修改是否在技术和管理上可行
4. 对整体研究的影响：修改是否会影响其他相关工作的进展
</decision_factors>
<decision_options>
1. 接受修改：同意用户意见，制定修改计划
2. 回复澄清：需要向用户澄清某些问题，或解释为什么不需要修改
3. 拒绝修改：认为用户意见不合理，拒绝修改
</decision_options>
<output_format>
你需要严格按以下XML格式输出，不要输出任何多余内容
<response>
<decision>决策结果</decision>
<reasoning>决策理由</reasoning>
<modification_plan>修改计划（如果接受修改）</modification_plan>
<response_to_user>对用户的回复</response_to_user>
</response>
</output_format>
<environment_information>
<current_research_tree_full_text>
<content>
{{current_research_tree_full_text}}
</content>
<explanation>
{CURRENT_RESEARCH_TREE_FULL_TEXT_EXPLANATION}
</explanation>
</current_research_tree_full_text>
<current_solution>
<content>
{{current_solution}}
</content>
<explanation>
这是你当前负责的解决方案。
</explanation>
</current_solution>
<user_feedback_analysis>
<content>
{{user_feedback_analysis}}
</content>
<explanation>
对用户反馈的分析结果。
</explanation>
</user_feedback_analysis>
<visible_messages>
<content>
{{visible_messages}}
</content>
<explanation>
你可以看到的其他相关消息。
</explanation>
</visible_messages>
</environment_information>
"""


SOLUTION_MODIFICATION_PROMPT = f"""
{ROLE_AND_RULES}
<task>
根据修改决策和用户反馈，修改当前解决方案。
</task>
<specifications>
<modification_requirements>
1. 保持原有方案的优点和核心思路
2. 针对用户反馈的具体问题进行有针对性的修改
3. 确保修改后的方案仍然满足原有的研究目标和评判标准
4. 在修改过程中保持逻辑的一致性和完整性
</modification_requirements>
<modification_process>
1. 分析需要修改的具体部分
2. 制定修改策略和方法
3. 执行修改，确保各部分之间的协调一致
4. 验证修改后的方案是否解决了用户关注的问题
</modification_process>
<output_format>
你需要严格按以下XML格式输出，不要输出任何多余内容
<response>
<title>修改后的标题</title>
<top_level_thoughts>修改后的顶层思考</top_level_thoughts>
<implementation_plan>修改后的实施方案</implementation_plan>
<plan_justification>修改后的方案论证</plan_justification>
<finishing_task>修改后的收尾任务</finishing_task>
<modification_summary>修改总结</modification_summary>
</response>
</output_format>
<environment_information>
<current_research_tree_full_text>
<content>
{{current_research_tree_full_text}}
</content>
<explanation>
{CURRENT_RESEARCH_TREE_FULL_TEXT_EXPLANATION}
</explanation>
</current_research_tree_full_text>
<original_solution>
<content>
{{original_solution}}
</content>
<explanation>
原始的解决方案内容。
</explanation>
</original_solution>
<modification_decision>
<content>
{{modification_decision}}
</content>
<explanation>
修改决策和具体要求。
</explanation>
</modification_decision>
<user_feedback>
<content>
{{user_feedback}}
</content>
<explanation>
用户的原始反馈意见。
</explanation>
</user_feedback>
<visible_messages>
<content>
{{visible_messages}}
</content>
<explanation>
你可以看到的其他相关消息。
</explanation>
</visible_messages>
</environment_information>
"""

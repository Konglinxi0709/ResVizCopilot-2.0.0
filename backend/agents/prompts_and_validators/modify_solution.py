from .global_prompt import (
    ROLE_AND_RULES, 
    TOP_LEVEL_THOUGHTS_SPECIFICATIONS,
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
    SolutionRequest,
    ProblemRequest,
)
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Dict, Any, Tuple
from enum import Enum
from backend.utils.logger import logger
class ModifyProblemType(str, Enum):
    IMPLEMENTATION = "implementation"
    CONDITIONAL = "conditional"  # 条件问题没有子solution节点
    INHERIT = "inherit" # 继承自原解决方案的某问题节点，要求问题名称必须与原问题节点相同，其它字段无效


class ModifyResearchSubProblem(BaseModel):
    """子研究问题模型"""
    type: ModifyProblemType
    name: Optional[str] = Field(description="问题名称")
    significance: Optional[str] = Field(description="问题意义")
    criteria: Optional[str] = Field(description="评判标准")
    
    @field_validator('type', mode='before')
    @classmethod
    def extract_type_from_attributes(cls, v, info):
        """从_attributes中提取type字段"""
        if isinstance(v, str):
            return v
        
        # 如果type字段不存在，尝试从_attributes中获取
        if info.data and '_attributes' in info.data:
            return info.data['_attributes'].get('type', v)
        return v
    
    @classmethod
    def from_xml_dict(cls, data: Dict[str, Any]) -> "ModifyResearchSubProblem":
        """
        从XML解析后的字典创建ModifyResearchSubProblem实例
        
        Args:
            data: XML解析后的字典
            
        Returns:
            ModifyResearchSubProblem实例
        """
        # 处理XML解析后的结构
        if '_attributes' in data:
            # 从属性中提取type
            problem_type = data['_attributes'].get('type', 'implementation')
            
            # 构建标准格式的数据
            problem_data = {
                'type': problem_type,
                'name': data.get('name', ''),
                'significance': data.get('significance', ''),
                'criteria': data.get('criteria', '')
            }
            
            return cls(**problem_data)
        else:
            # 标准格式，直接使用
            return cls(**data)
    
    def to_request(self, org_problem_map: Dict[str, ProblemRequest]) -> ProblemRequest:
        if self.type == ModifyProblemType.INHERIT:
            return org_problem_map[self.name]
        return ProblemRequest(
            title=self.name,
            significance=self.significance if self.significance else "",
            criteria=self.criteria if self.criteria else "",
            problem_type=self.type
        )

class ModifySolutionResponse(BaseModel):
    """修改解决方案响应模型"""
    name: str = Field(description="整体思路的名称")
    top_level_thoughts: str = Field(description="顶层思考内容")
    research_plan: List[ModifyResearchSubProblem] = Field(default_factory=list, description="子研究问题列表")
    implementation_plan: str = Field(description="实施方案内容")
    plan_justification: str = Field(description="方案论证内容")
    
    @field_validator('research_plan', mode='before')
    @classmethod
    def process_research_plan(cls, v):
        """处理research_plan字段，将XML解析后的结构转换为ModifyResearchSubProblem列表"""
        # 处理三种情况：空标签、包含文本的标签、无标签
        if v is None:
            return []
        
        if isinstance(v, str):
            # 如果是字符串（如"无子研究问题"），返回空列表
            return []
        
        if isinstance(v, dict):
            # 处理XML解析后的结构
            if 'sub_problem' in v:
                problems = v['sub_problem']
                if isinstance(problems, list):
                    # 多个sub_problem标签
                    return [ModifyResearchSubProblem.from_xml_dict(problem) for problem in problems]
                else:
                    # 单个sub_problem标签
                    return [ModifyResearchSubProblem.from_xml_dict(problems)]
            else:
                # 其他情况，尝试直接处理
                return [ModifyResearchSubProblem.from_xml_dict(v)]
        
        if isinstance(v, list):
            # 已经是列表格式，直接返回
            return v
        
        return []

    def to_request(self, org_problem_map) -> Tuple[str, SolutionRequest]:
        logger.info(f"原方案问题标题列表: {org_problem_map}")
        org_problem_titles = list(org_problem_map.keys())
        if len(self.research_plan) == len(org_problem_map):
            flag = True
            for i in range(len(self.research_plan)):
                if self.research_plan[i].type != ModifyProblemType.INHERIT:
                    flag = False
                    break
                if self.research_plan[i].name != org_problem_titles[i]:
                    flag = False
                    break
            if flag: # 更新模式
                return "update", SolutionRequest(
                    title=self.name,
                    top_level_thoughts=self.top_level_thoughts,
                    implementation_plan=self.implementation_plan,
                    plan_justification=self.plan_justification,
                )
        return "create", SolutionRequest(
            title=self.name,
            top_level_thoughts=self.top_level_thoughts,
            implementation_plan=self.implementation_plan,
            plan_justification=self.plan_justification,
            children=[sub_problem.to_request(org_problem_map) for sub_problem in self.research_plan],
        )


    def to_content(self) -> str:
        # 构建实施方案文本
        research_plan_text = ""
        for sub_problem in self.research_plan:
            research_plan_text += f"[问题类型]: {sub_problem.type}\n"
            if sub_problem.type != ModifyProblemType.INHERIT:
                research_plan_text += f"[问题名称]: {sub_problem.name}\n"
                research_plan_text += f"[问题意义]: \n{sub_problem.significance}\n"
                research_plan_text += f"[评判标准]: \n{sub_problem.criteria}\n\n"
            else:
                research_plan_text += f"[继承自问题]: {sub_problem.name}\n"
        
        return f"【解决方案名称】: {self.name}\n\n" \
               f"【顶层思考】: \n{self.top_level_thoughts}\n\n" \
               f"【研究方案】: \n{research_plan_text}\n\n" \
               f"【实施方案】: \n{self.implementation_plan}\n\n" \
               f"【方案论证】: \n{self.plan_justification}"

# 更新创建解决方案
MODIFY_THE_SOLUTION_PROMPT = f"""
{ROLE_AND_RULES}
<task>
现在{{supervisor_name}}对你的解决方案提出了修改要求, 经过你们的讨论，你最终决定对你的解决方案作出修改。
现在，你需要在当前方案的基础上为解决当前问题设计新的方案，大致包括如下几步。
1. 接收信息：
    1. 理解当前的完整研究过程，了解团队的研究目标和已经进行过的思考和求证，并掌握其中得到的所有事实结论
    2. 理解你自己的研究方案，这代表着你之前的工作思路
    3. 理解你和用户间的对话，了解用户修改要求背后的思考
2. 撰写新的解决方案
    1. 按相关解释和要求撰写顶层思考
    2. 按相关解释和要求撰写研究方案（设计子问题列表）
    3. 按相关解释和要求撰写实施方案
    4. 按相关解释和要求撰写方案论证
3. 为你修改后的整体思路起一个一目了然的名字，点明核心洞见和基本方案，且不能与当前研究方案或其它节点的名称相同。
4. 进行全面仔细的检查和完善，确保你撰写的所有内容符合要求，且输出符合XML规范要求。
</task>
<specifications>
<top_level_thoughts>
{TOP_LEVEL_THOUGHTS_SPECIFICATIONS}
</top_level_thoughts>

<research_plan>
<what>
研究方案是由顶层思考指导设计的，在解决当前问题前必须深入研究的几个子研究问题。各个子问题将按顺序分别指派专业对口的专家或专家团队负责执行。
子研究问题分为两种，分别是证明条件问题，解决实施问题。
你需要清晰的写明每个研究问题的研究意义和验收标准，以便他们准确理解你的意图，高质量的完成工作。
是否定义子研究问题，定义多少个，**仅由你根据当前问题的复杂程度和难度决定**，与当前问题在研究树中的位置无关，也与其它专家定义子问题的多少无关。不要因为当前问题是其它专家解决方案的子实施问题，就认为不应该继续定义新的子研究问题。
- 如果面对的问题较复杂，你不应该由自己承担解决当前问题涉及的所有的困难工作，而是充分理解问题的本质，论证和设计研究方案，必须将当前的复杂问题拆解为高价值易实施的小问题，和你的专家团队一起解决。这是最高效的专家团队工作模式。
- 如果面对的问题难度非常小，且足够具体清晰，无需进一步研究和论证便显然可以解决，则你的研究方案应该为空，解决当前问题的所有工作均在实施方案中计划。
    - 选择不定义子研究问题时，必须慎之又慎，仔细规划实施计划，分析任何可能出现困难的环节，只有不存在任何困难时，才能选择不定义子研究问题。

{{current_solution_sub_problem_list}}
以上是你当前解决方案的子研究问题列表。你可以根据自己的需要，继承其中的问题，成为新研究方案的一部分。
<condition>
条件问题是你的实施方案如果能取得成功，必须被证明的一些假设。这一般包括你在顶层思考中产生的洞见是否成立、为问题设置的边界条件是否合理、理论模型的数据测试等。证明条件问题的过程同时也是提升认知、收获启发的过程，因此不要害怕提出条件问题，反而要尽可能全面、完整的提出条件问题。如果方案因条件问题被证伪而失败，要远远好于因实施问题和行动无法解决而失败，因为前者更容易收获新的洞见形成更好的思路和方案。
你的条件问题被其它专家证明或证伪后，将以一份论证/实验报告的形式向你提交。
</condition>
<implementation>
实施问题是需要进一步探索和攻关来解决的子题目。
你的实施问题被其它专家解决或证明无法解决后，将以一份研究报告的形式向你提交，还会包括一个程序仓库，包括解决该问题所编写的代码，以及测试样例。
</implementation>
<inherit>
继承自原解决方案的某问题节点，要求问题名称必须与原问题节点相同，其它字段均无效，即你对选择继承的问题无法做任何修改，其类型、意义、评判标准等均与原问题一致。
如果你继承了某个问题，负责该问题的专家团队已经完成的方案设计和研究工作将被原封不动的保留，否则将被丢弃并重新开始。
在选择继承之前，你必须仔细阅读、分析该问题当前的定义和研究工作，判断它们是否不需要任何修改就可以适配你的新方案。如果有任何不匹配的地方，请不要继承，而是重新设计该问题。
</inherit>
</what>
<constraints>
1. 每个非继承的子研究问题需要包含以下内容
    1. 名称：用简洁易懂的语言清晰的描述这一问题的主要任务，名称应该是问句形式，例如是否...，如何...。
    2. 意义：说明该步骤工作的之于整个研究的价值和必要性
    3. 参考标准：对评判该工作是否成功定义一个明确可执行的标准。对于涉及软件工程的实施问题，除了规定技术指标以外，也需要从软件工程角度规定需要形成一个什么样的代码仓库，定义怎样的接口，使用怎样的测试案例等。
2. 每个子问题的研究都取得成功是当前问题的研究取得成功的必要前提。
3. 在子问题的顺序上，必须先进行各个条件问题的证明，再完成各个实施问题的解决；同时必须保证研究每个问题的所有前置条件都在之前得到解决，以确保方案的可行性。
4. 对于条件问题，必须设计为边界明确的，查找相关文献资料，或者运行一段python代码即可证明或证伪的。复杂的工程验证问题请设计为实施问题。
5. 实施问题之间尽量是边界分明的，如果你自己的两个子问题中A研究问题是B问题更进一步的子问题，则应该由负责研究B问题的下级专家来提出，而不是在你这里提出。
6. 继承问题只有名称字段有效，其它字段均应为空，且名称必须与被继承的原问题节点名称相同。
</constraints>
<format>
<sub_problem type="conditional|implementation|inherit">
<name><!-- 用问句描述条件/实施问题（如"是否..."或"如何..."） --></name>
<if type != "inherit">
<significance>
<!-- 说明本步骤的必要性 -->
</significance>
<criteria>
<!-- 明确可执行的成功评判标准 -->
</criteria>
</if>
</sub_problem>
...
<!-- 可以设计任意0个或多个子研究问题 -->
</format>
</research_plan>
<implementation_plan>
<what>
实施方案是在研究方案中的所有子问题均被下级的专家或专家团队解决或证明之后，你亲自进行的实施工作的计划。
实施工作是当前研究问题解决的最后收尾工作，因此在这一步中你至少需要总结整个研究，撰写一份报告，用来论证当前问题已经得到解决。
除此之外，如果当前研究问题涉及软件工程，你需要完成程序的编写和测试，并对程序的架构、流程、接口、设计思路等撰写一个额外的技术文档。这个过程中可能也涉及汇总整合子问题的专家团队提交的程序。
</what>
<constraints>
1. 实施方案必须写的足够详细，提前考虑到你在执行时所有可能遇到的困难并预想解决方法。
2. 实施方案中的所有工作都必须是显而易见可以成功落实的。如果存在可能需要证明的前置条件或需要进一步讨论研究的实施问题，请务必把它们包含在研究计划中，由下级专家先一步逐一进行研究，从而你可以在实施方案中假设它们都已经被解决或证明。
3. 实施方案中也必须写清楚每一步工作是否成果的验收标准，以便落实。
4. 你在实施工作时的能力范围包括如下，你需要确保在你的能力范围下，该方案的可行性是显而易见的。
    1. 查看代码库的内容
    2. 创建文件
    3. 编辑文件，修改内容
    4. 运行命令行命令，如运行程序文件等
    5. 撰写、提交结果报告
</constraints>
<format>
一篇文章，纯文本格式，排版自由。
</format>
</implementation_plan>
<plan_justification>
<what>
方案论证是从可行性和高效性两个方面对认为当前研究、实施方案最优的理由进行判断。
- 可行性指的是你计划的这些子问题和实施工作实际上解决了哪些本质问题，为什么解决这些问题就解决了当前问题，而不存在没有考虑到的出错情况。最终结论应该是你的解决方案在所有的条件问题得到证明，所有的实施问题得到解决的前提下，按照你对实施方案完成收尾工作后，最终成果一定能实现当前问题的研究价值。
- 高效性指的是你规划的每一步为什么不可缺少，它解决的本质问题为什么是不可绕过的。
</what>
<constraints>
1. 可行性论证是在具体执行前对你方案的深度自查，必须确保方案论证的客观严谨，考虑到所有可能出问题的情况。
2. 高效性论证的价值判断依据应从顶层思考出发
3. 必须不遗漏的论证你研究方案中的每个子问题，以及实施方案中的每一步计划。
</constraints>
<format>
一篇文章，纯文本格式，排版自由。
</format>
</plan_justification>
</specifications>
<output_format>
你需要严格按以下XML格式输出，不要输出任何多余内容
<response>
<name>整体思路的名称</name>
<top_level_thoughts>顶层思考内容</top_level_thoughts>
<research_plan>研究方案内容（如果不设计任何子问题，则保留空的research_plan标签即可）</research_plan>
<implementation_plan>实施方案内容</implementation_plan>
<plan_justification>方案论证内容</plan_justification>
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
<modify_plan>
<content>
{{modify_plan}}
</content>
<explanation>
在与用户讨论之后，你最终决定对当前方案进行修改，并给出了以上的修改计划。
你可以参考你当时的计划，如果你发现该计划有不完善的地方，也可以任意地做出调整。
</explanation>
</modify_plan>
</environment_information>
"""

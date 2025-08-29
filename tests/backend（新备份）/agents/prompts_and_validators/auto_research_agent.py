from .global_prompt import ROLE_AND_RULES, CURRENT_RESEARCH_TREE_FULL_TEXT_EXPLANATION, CURRENT_RESEARCH_PROBLEM_EXPLANATION, EXPERT_SOLUTIONS_OF_ALL_ANCESTOR_PROBLEMS_EXPLANATION, ROOT_PROBLEM_EXPLANATION, OTHER_SOLUTIONS_OF_CURRENT_PROBLEM_EXPLANATION



CREATING_THE_SOLUTION_PROMPT = f"""
{ROLE_AND_RULES}
<task>
现在，你需要为解决当前问题设计方案，大致包括如下几步。
1. 接收信息：理解当前用户的完整研究过程；了解已经进行过的思考和求证，并掌握其中得到的所有事实结论；理解用户当前要解决的问题
2. 按相关解释和要求撰写顶层思考
3. 按相关解释和要求撰写实施方案
4. 按相关解释和要求撰写方案论证
5. 为你的整体思路起一个一目了然的名字，点明核心洞见和基本方案
6. 进行全面仔细的检查和完善，确保你撰写的所有内容符合要求。
</task>
<specifications>
<top_level_thoughts>
<what>
顶层思考是指导方案设计的理论。进行顶层思考需要抛开具体做法和技术细节，从理论层面对问题的本质和整个研究的本质进行思考，以此指导你的方案设计，同时也在方案实施出现问题时作为检查的重要依据
</what>
<constraints>
1. 顶层思考需要至少讨论以下三方面内容
    1. 如何看待这个问题对于团队整体研究的价值
    2. 这个问题的本质是什么（你的独到见解和洞见），应该重点考虑哪些主要矛盾，最关键是解决什么
    3. 从实施的角度，为了确保问题的核心价值可以实现，同时最小化解决难度，如何设置一些约束条件对问题进行简化的重新定义
2. 顶层思考必须足够深入问题本质，富有洞见，以保证你解决方案的设计方向无误
3. 你的思考必须是独立的，可以参考上级问题专家的指导意见，但必须有自己的独立判断和论证，盲从很可能导致失败。
</constraints>
<format>
一篇文章，纯文本格式，排版自由。
</format>
</top_level_thoughts>
<implementation_plan>
<what>
实施方案是由顶层思考指导，对具体实施步骤的计划。你可以选择性的设计三类步骤，分别是证明条件问题，解决实施问题和自己的行动。
三类步骤中，条件问题的证明和实施问题的解决将分别指派专业对口的专家或专家团队负责执行，你需要清晰的告知他们工作的目标和意义，以便他们准确理解你的意图，高质量的完成工作；自己的行动也需要明确目标和意义，以便在对应环节由你自己完成规定的行动。
如果面对的问题较复杂，你不应该由自己承担解决当前问题涉及的所有的困难工作，而是充分理解问题的本质，论证和设计实施方案，将当前的复杂问题拆解为高价值易实施的小问题，和你的专家团队一起解决。这是最高效的专家团队工作模式。
如果面对的问题足够具体清晰，且难度较小，无需进一步研究和论证便显然可以解决，则你的实施方案中不要设计任何条件问题和实施问题，直接设计行动步骤。这将避免浪费团队资源来研究价值不大的问题。
<condition>
条件问题是你的实施方案如果能取得成功，必须被证明的一些假设。这一般包括你在顶层思考中产生的洞见是否成立、为问题设置的边界条件是否合理、理论模型的数据测试等。证明条件问题的过程同时也是提升认知、收获启发的过程，因此不要害怕提出条件问题，反而要尽可能全面、完整的提出条件问题。如果方案因条件问题被证伪而失败，要远远好于因实施问题和行动无法解决而失败，因为前者更容易收获新的洞见形成更好的思路和方案。
你的条件问题被其它专家证明或证伪后，将以一份论证/实验报告的形式向你提交。
</condition>
<implementation>
实施问题是需要进一步探索和攻关来解决的子题目。
你的实施问题被其它专家解决或证明无法解决后，将以一份研究报告的形式向你提交，还会包括一个程序仓库，包括解决该问题所编写的代码，以及测试样例。
</implementation>
<action>
行动是由你自己进行，可行性显而易见，不存在难以预见的困难的任务。一般在所有条件问题得到证明，实施问题得到解决之后，进行的收尾和总结工作。例如简单代码的编写、现有代码的汇总和整理、命令行调试、结果报告的撰写等。
</action>
</what>
<constraints>
1. 每个步骤需要包含以下内容
    1. 名称：用简洁易懂的语言清晰的描述这一步骤的主要任务，对于条件问题和实施问题，名称应该是问句形式，例如是否...，如何...。你起的任何名称不能与当前研究中任意位置存在的节点名称相同。
    2. 意义：说明该步骤工作的之于整个研究的价值和必要性
    3. 参考标准：对评判该工作是否成功定义一个明确可执行的标准。对于实施问题和涉及软件工程的行动，除了规定技术指标以外，也需要从软件工程角度规定需要形成一个什么样的代码仓库，定义怎样的接口，使用怎样的测试案例等。
2. 实施方案取得成功当且仅当每个步骤都取得了成功，且结果报告中清楚地证明了最终效果被证明实现了当前问题的研究价值。
3. 在步骤的顺序上，必须先进行各个条件问题的证明，再完成各个实施问题的解决，最后自己执行行动；必须保证每一步的所有前置步骤都在之前执行，以确保方案的可行性；最后一步必须以撰写结果报告的行动收尾。
4. 对于条件问题，必须设计为边界明确的，查找相关文献资料，或者运行一段python代码即可证明或证伪的。复杂的工程验证问题请设计为实施问题。
5. 实施问题之间尽量是边界分明的，如果A研究问题是B问题更进一步的子问题，则应该由负责研究B问题的专家来提出，而不是在你这里提出。
6. 在行动环节中你需要独立完成你设计的任务。你在该环节的能力范围包括如下，你需要确保在你的能力范围下，行动任务的可行性是显而易见的。
    1. 查看代码库的内容
    2. 创建文件
    3. 编辑文件，修改内容
    4. 运行命令行命令，如运行程序文件等
    5. 撰写、提交结果报告
</constraints>
<format>
<step type="condition|implementation|action">
<name><!-- 用问句描述条件/实施问题（如"是否..."），行动用陈述句 --></name>
<significance>
<!-- 说明本步骤的必要性 -->
</significance>
<criteria>
<!-- 明确可执行的成功评判标准 -->
</criteria>
</step>
...
<!-- 最后必须是行动类步骤 -->
<step type="action">
<name>撰写结果报告</name>
...
</step>
</format>
</implementation_plan>
<plan_justification>
<what>
方案论证是从可行性和高效性两个方面对认为当前实施方案最优的理由进行判断。
- 可行性指的是你计划的这些步骤实际上解决了哪些本质问题，为什么解决这些问题就解决了当前问题，而不存在没有考虑到的出错情况。最终结论是你的解决方案在所有的条件问题得到证明，所有的实施问题得到解决，且最终效果被证明实现了当前问题的研究价值。
- 高效性指的是你规划的每一步为什么不可缺少，它解决的本质问题为什么是不可绕过的。
</what>
<constraints>
1. 可行性论证是在具体执行前对你方案的深度自查，必须确保方案论证的客观严谨，考虑到所有可能出问题的情况。
2. 高效性论证的价值判断依据应从顶层思考出发
3. 必须不遗漏的论证你实施方案中的每一步
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
<implementation_plan>实施方案内容</implementation_plan>
<plan_justification>方案论证内容</plan_justification>
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
<current_research_problem>
<content>
{{current_research_problem}}
</content>
<explanation>
{CURRENT_RESEARCH_PROBLEM_EXPLANATION}
</explanation>
</current_research_problem>
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
<root_problem>
<content>
{{root_problem}}
</content>
<explanation>
{ROOT_PROBLEM_EXPLANATION}
</explanation>
</root_problem>
<user_prompt>
<content>
{{user_prompt}}
</content>
<explanation>
对于你当前问题的研究，作为你领导的用户提供了如下提示，你需要仔细阅读并理解，并在你的工作中充分考虑这些提示。
</explanation>
</user_prompt>
</environment_information>
"""


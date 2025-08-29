"""
自动生成解决方案智能体
对应流程图中"用户为某实施问题开启解决方案自动生成"入口
"""
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from collections import deque

from .agent_base import AgentBase
from .prompts_and_validators.create_solution import (
    CREATING_THE_SOLUTION_PROMPT,
    CreateSolutionResponse,
)
from backend.database.database_manager import DatabaseManager
from backend.database.schemas.request_models import (
    ProblemRequest,
    SolutionRequest,
    SetSelectedSolutionRequest,
)
from backend.utils.logger import logger

test_solution_text = """
<?xml version="1.0" encoding="UTF-8"?>
<response>
<name><![CDATA[基于多尺度特征融合与运动补偿的红外小目标实时检测框架]]></name>
<top_level_thoughts><![CDATA[
### 顶层思考

#### 1. 问题对团队整体研究的价值
周扫红外搜索系统对空中小目标的检测与告警技术是空中防御体系的核心组成部分，其价值在于提供早期预警能力，以应对日益增长的空中威胁（如飞机、导弹、无人机）。对于团队整体研究而言，成功解决此问题将直接提升国防和安全领域的态势感知能力，并为后续的拦截或应对措施争取关键时间。此外，该技术的突破可推动红外成像、实时处理和人工智能算法的交叉创新，形成技术壁垒，增强团队在相关领域的领导力和影响力。

#### 2. 问题的本质与主要矛盾
问题的本质是从周扫红外系统的序列图像中可靠地检测和告警小目标，其核心挑战在于目标信号弱、背景噪声高、以及系统运动引入的畸变。主要矛盾包括：
- **检测灵敏度与误报率的权衡**：小目标在红外图像中往往只占几个像素，信噪比低，容易淹没在背景噪声中；提高检测灵敏度可能导致误报增加，而降低误报率又可能漏检真实目标。
- **实时处理与计算复杂度的矛盾**：周扫系统需要高速处理大量图像数据，以实现实时告警，但高级算法（如深度学习）计算开销大，难以直接部署。
- **环境适应性**：天气条件（如云层、雾霾）和背景变化（如地面热源）会进一步增加检测难度。

最关键的是解决**小目标特征的可靠提取与判别**，这需要结合多尺度分析、运动补偿和机器学习方法，以在低信噪比下实现高精度检测。

#### 3. 约束条件与简化重新定义
为了最小化解决难度，同时确保核心价值（可靠检测和实时告警）可实现，我对问题设置以下约束条件进行简化重新定义：
- **目标类型优先**：首先专注于飞机和导弹的检测，因为它们具有更稳定的红外特征；无人机检测可作为后续扩展。
- **环境假设**：初始阶段假设晴朗天气和相对简单的背景（如天空背景），以减少环境变量干扰。
- **系统参数固定**：使用典型的周扫红外系统参数（如扫描速率、分辨率），避免过度泛化。
- **实时性标准**：告警延迟控制在秒级以内，以满足实战需求，但允许算法在嵌入式平台上优化而非追求极致低延迟。

通过这些约束，问题被简化为：在固定参数和周扫条件下，从红外序列图像中检测特定小目标，并实现可靠告警。这使团队能聚焦核心算法开发，逐步扩展适应性。
]]></top_level_thoughts>
<research_plan>
<sub_problem type="conditional">
<name><![CDATA[红外特征是否足以区分小目标与常见背景噪声？]]></name>
<significance><![CDATA[
此条件问题旨在验证顶层思考中关于红外特征有效性的核心假设。如果红外特征不足以区分小目标，则整个检测方案可能需要重新设计（如融合其他传感器数据）。证明此假设是后续算法开发的基础，避免盲目实施。]]></significance>
<criteria><![CDATA[
成功标准：通过文献综述和模拟数据分析，证明在典型周扫红外系统参数下，小目标（飞机、导弹）的红外特征（如热辐射强度、形状轮廓）与常见背景噪声（云层、地面热源）有显著差异（例如，信噪比差异大于3dB）。提交一份论证报告，包括数据来源、分析方法和统计结论。]]></criteria>
</sub_problem>
<sub_problem type="conditional">
<name><![CDATA[周扫运动是否会导致目标畸变难以补偿？]]></name>
<significance><![CDATA[
周扫系统的运动可能引入图像畸变和目标位移，影响检测性能。此问题验证运动补偿的可行性，确保后续算法能有效处理序列图像。如果运动补偿不可行，可能需要硬件改进或算法调整。]]></significance>
<criteria><![CDATA[
成功标准：通过数学建模和仿真（如使用Python模拟周扫运动），证明在典型扫描速率下，运动引起的畸变可以通过标准图像处理技术（如光流法或积分时间补偿）有效补偿（补偿后目标位置误差小于1像素）。提交一份仿真报告，包括模型、代码和结果分析。]]></criteria>
</sub_problem>
<sub_problem type="implementation">
<name><![CDATA[如何设计一个多尺度特征融合算法用于红外小目标检测？]]></name>
<significance><![CDATA[
小目标检测需要处理多尺度信息，以捕捉细节和上下文。此实施问题旨在开发核心检测算法，结合传统图像处理和深度学习，以提高检测精度。这是解决当前问题的关键技术攻关。]]></significance>
<criteria><![CDATA[
成功标准：算法在模拟数据集上实现检测率大于95%、误报率小于5%；算法输出包括目标位置和置信度；代码仓库包含完整的训练和推理代码（Python/PyTorch）、接口定义（输入为红外图像序列，输出为检测结果）、以及测试样例（至少100组模拟数据）。提交研究报告和技术文档。]]></criteria>
</sub_problem>
<sub_problem type="implementation">
<name><![CDATA[如何实现实时处理管道以满足告警延迟要求？]]></name>
<significance><![CDATA[
实时性是告警系统的关键需求。此实施问题聚焦于优化处理管道，确保算法能在资源受限的嵌入式平台上运行，满足秒级延迟。缺乏实时性将使检测系统无法实用。]]></significance>
<criteria><![CDATA[
成功标准：处理管道在典型硬件（如Jetson AGX）上实现平均处理延迟小于1秒 per frame；代码仓库包含优化后的C++/Python代码、性能测试脚本和部署指南；提交性能报告，包括延迟、吞吐量和资源使用数据。]]></criteria>
</sub_problem>
</research_plan>
<implementation_plan><![CDATA[
### 实施方案

在子研究问题全部解决后（即条件问题被证明、实施问题被解决），我将亲自执行以下收尾工作。假设所有子问题均成功，我将基于下级专家提交的代码和报告进行集成和验证。

#### 1. 系统集成与代码汇总
- **任务**：整合子问题解决方案（多尺度检测算法和实时处理管道） into a unified system.
- **步骤**：
  - 创建主代码仓库，结构化如下：
    - `detection_algorithm/`: 包含多尺度特征融合算法（来自实施问题1）
    - `real_time_pipeline/`: 包含优化后的处理管道（来自实施问题2）
    - `integration/`: 主程序，协调算法和管道，处理输入输出
  - 定义清晰接口：主程序输入为红外图像序列（视频流或图像列表），输出为检测结果（目标坐标、类别、置信度）和告警信号。
  - 编写集成脚本，确保模块间数据流正确。
- **验收标准**：集成系统能完整运行，无编译错误或运行时崩溃。

#### 2. 全面测试与验证
- **任务**：在模拟和真实数据上测试系统性能。
- **步骤**：
  - 使用下级专家提供的测试样例（100组模拟数据）进行初始测试。
  - 收集真实红外数据（如有权限）或生成更复杂的模拟数据（包含各种背景和目标），进行扩展测试。
  - 评估指标：检测率、误报率、告警延迟、系统稳定性。
  - 运行性能测试：在目标硬件上测量处理延迟和资源使用。
- **验收标准**：系统在测试数据上达到检测率>90%、误报率<10%、延迟<1秒（符合实施问题2的标准）。

#### 3. 技术文档撰写
- **任务**：撰写详细技术文档，说明系统架构、算法原理、使用方法和性能结果。
- **步骤**：
  - 编写`README.md`：概述系统、安装和运行指南。
  - 编写`architecture.pdf`：描述系统设计、模块交互和数据流。
  - 编写`algorithm_details.pdf`：解释多尺度特征融合算法的设计和训练过程。
  - 编写`performance_report.pdf`：总结测试结果和性能数据。
- **验收标准**：文档完整、清晰，可供其他专家理解和复用。

#### 4. 最终报告提交
- **任务**：撰写最终研究报告，论证当前问题已解决。
- **步骤**：
  - 总结整个研究过程：从顶层思考到子问题解决，再到集成测试。
  - 引用下级专家的报告和代码，证明条件成立和实施成功。
  - 说明系统如何满足原始问题的价值（可靠检测和实时告警）。
  - 讨论局限性和未来改进方向（如扩展至无人机检测、恶劣天气适应）。
- **验收标准**：报告逻辑严谨，证据充分，结论明确显示问题已解决。

#### 预想困难与解决方法
- **困难**：集成时模块接口不匹配。
  - **解决**：提前与下级专家沟通接口规范，在集成阶段灵活调整代码。
- **困难**：真实数据测试性能下降。
  - **解决**：收集更多数据用于算法微调，或增加后处理滤波以减少误报。
- **困难**：硬件资源不足导致延迟超标。
  - **解决**：进一步优化代码（如量化模型、使用GPU加速），或降低分辨率权衡性能。

所有工作均在我的能力范围内（查看代码、编辑文件、运行命令、撰写报告），且基于子问题成功的前提，可行性高。
]]></implementation_plan>
<plan_justification><![CDATA[
### 方案论证

#### 可行性论证
我的解决方案通过拆解复杂问题为子问题，并逐步解决，确保最终成果能实现当前问题的研究价值（可靠检测和实时告警）。论证如下：
- **条件问题证明确保基础假设成立**：第一个条件问题（红外特征区分性）验证了红外数据足以支持检测，避免了传感器层面的根本缺陷。第二个条件问题（运动补偿可行性）确保了序列图像可处理性。只有两者均被证明，后续算法开发才有意义。
- **实施问题解决核心技术瓶颈**：多尺度特征融合算法直接针对小目标检测的核心挑战，通过融合多层次信息提高检测精度。实时处理管道确保算法能实际部署，满足告警延迟要求。这两个实施问题覆盖了从算法到系统的关键环节。
- **实施方案完成收尾集成**：在子问题解决后，我的集成工作将算法和管道结合，并通过测试验证整体性能。技术文档和报告提供完整论证链。最终，系统在测试数据上达到预期指标，证明问题解决。

整个方案不存在遗漏：条件问题处理了假设验证，实施问题处理了技术攻关，实施方案处理了系统化和验证。所有可能出点的情况（如假设不成立或算法失败）已在子问题阶段暴露和解决，因此最终实施成功率很高。

#### 高效性论证
从顶层思考出发，每个子问题都不可或缺，解决的是本质矛盾：
- **条件问题的高效性**：直接验证顶层思考中的洞见（红外特征有效性和运动补偿可行），避免了盲目开发带来的资源浪费。例如，如果红外特征不足，团队可及时转向多传感器融合，节省时间。
- **实施问题的高效性**：多尺度特征融合算法解决了小目标检测的核心矛盾（灵敏度与误报率），通过先进算法提升性能；实时处理管道解决了实时性与计算复杂度的矛盾，通过优化确保实用性。两者分工明确，边界清晰，避免重复工作。
- **实施方案的高效性**：集成和测试是问题解决的必然步骤，确保系统整体协调。文档和报告提供可追溯的证据，符合科研严谨性。

每个步骤都针对问题本质，没有冗余：条件问题先于实施问题，确保方向正确；实施问题并行但独立，由专业团队执行；实施方案汇总成果。这种结构最小化整体解决难度，最大化团队协作效率。
]]></plan_justification>
</response>
"""

class AutoResearchAgent(AgentBase):
    """
    自动生成解决方案智能体
    
    核心功能：
    1. 为实施问题自动生成解决方案
    2. 支持用户要求注入
    3. 实现BFS遍历生成子问题解决方案
    4. 支持上级问题评审和监督
    """
    
    def __init__(self, 
                 name: str = "auto_research_agent",
                 publish_callback=None,
                 llm_client=None,
                 retry_wrapper=None,    
                 database_manager: DatabaseManager = None,
                 get_visible_messages=None):
        super().__init__(name, publish_callback, llm_client, retry_wrapper, database_manager, get_visible_messages)
        
        # 智能体状态
        self.current_problem_id: Optional[str] = None
        self.current_solution_id: Optional[str] = None
        self.problem_queue: deque = deque()  # (实施问题节点ID, 监督方案节点ID(空代表用户监督), 用户要求)队列, 正常右进左出
        
        logger.info(f"自动研究智能体 {name} 初始化完成")
    
    async def _agent_process(self, user_content: str, other_params: Dict[str, Any]) -> None:
        """
        智能体处理流程核心逻辑
        
        Args:
            user_content: 用户输入内容
            other_params: 其他参数
        """
        try:
            problem_id = other_params.get("problem_id")
            user_requirement = user_content
                
            if not problem_id:
                raise ValueError("未找到问题ID")
            
            # 验证问题节点
            self._validate_problem_node(problem_id)
            
            # 初始化队列
            self._init_problem_queue(problem_id, user_requirement)
            
            # 开始BFS处理
            await self._process_problem_queue()
            
        except Exception as e:
            logger.error(f"自动研究智能体处理失败: {e}")
            await self._publish_error_patch(f"处理失败: {str(e)}")
            raise e
    
    def _validate_problem_node(self, problem_id: str) -> None:
        """
        验证问题节点
        
        Args:
            problem_id: 问题ID
            
        Returns:
            问题节点
            
        Raises:
            ValueError: 节点不存在或类型不正确
        """
        # 查询问题节点详情
        result = self.database_manager.get_problem_detail_query(problem_id)
        if not result["success"]:
            raise ValueError(f"问题节点不存在: {problem_id}")

    
    def _init_problem_queue(self, problem_id: str, user_requirement: Optional[str]) -> None:
        """
        初始化问题队列
        
        Args:
            problem_id: 问题ID
            user_requirement: 用户要求
        """
        # 将用户指定的问题入队，监督节点为空（由用户自己评审）
        self.problem_queue.append((problem_id, None, user_requirement))
        logger.info(f"初始化问题队列，问题ID: {problem_id}")
    
    async def _process_problem_queue(self) -> None:
        """
        处理问题队列的BFS逻辑
        """
        while self.problem_queue:
            # 出队
            problem_id, supervisor_id, user_requirement = self.problem_queue.popleft()
            
            logger.info(f"处理问题: {problem_id}, 监督者: {supervisor_id}")
            
            # 检查问题是否已有选中的解决方案
            solution_id = await self._check_problem_has_solution(problem_id)
            
            if solution_id:
                # 已有解决方案，将子问题入队
                await self._enqueue_sub_problems(solution_id)
            else:
                # 没有解决方案，创建新的解决方案
                await self._create_solution_for_problem(problem_id, supervisor_id, user_requirement)
    
    async def _check_problem_has_solution(self, problem_id: str) -> bool:
        """
        检查问题是否已有选中的解决方案
        
        Args:
            problem_id: 问题ID
            
        Returns:
            是否有选中的解决方案
        """
        try:
            # 查询问题详情
            result = self.database_manager.get_selected_solution_id_query(problem_id)
            if result["success"]:
                # 从结果中检查是否有选中的解决方案
                return result["data"]["selected_solution_id"]
            return None
        except Exception as e:
            logger.error(f"检查问题解决方案失败: {e}")
            raise e
    
    async def _enqueue_sub_problems(self, solution_id: str) -> None:
        """
        将子问题入队
        
        Args:
            problem_id: 问题ID
            supervisor_id: 监督者ID
        """
        
        try:
            result = self.database_manager.get_node_children_ids_query(solution_id, only_implementation=True)
            assert result["success"]
            children_ids = result["data"]["children_ids"]
            for child_id in children_ids:
                self.problem_queue.append((child_id, solution_id, None))
            logger.info(f"将方案 {solution_id} 的子实施问题入队")
        except Exception as e:
            logger.error(f"获取子问题失败: {e}")
            raise e
    
    async def _create_solution_for_problem(self, 
                                         problem_id: str, 
                                         supervisor_id: Optional[str], 
                                         user_requirement: Optional[str]) -> None:
        """
        为问题创建解决方案
        
        Args:
            problem_id: 问题ID
            supervisor_id: 监督者ID
            user_requirement: 用户要求
        """
        try:
            # 获取环境信息
            env_info = await self._get_environment_info(problem_id, user_requirement)
            
            # 调用LLM创建解决方案
            solution_response = await self._call_llm_with_retry(
                prompt=CREATING_THE_SOLUTION_PROMPT.format_map(env_info),
                title="创建解决方案",
                validator=CreateSolutionResponse,
                publisher=problem_id,
                visible_node_ids=[problem_id]
            )
            
            #from backend.utils.xml_parser import XMLParser
            #xml_parser = XMLParser()
            #result = xml_parser.xml_to_dict(test_solution_text)
            #solution_response = xml_parser.validate_with_pydantic(result, CreateSolutionResponse)
            
            solution_request = solution_response.to_request()
            result = await self._execute_action(self.database_manager.create_solution, problem_id, problem_id, solution_request)
            
            # 如果有监督者，进行评审
            #if supervisor_id:
            #    await self._supervisor_review(problem_id, supervisor_id, solution_response)
            #else:
            #    # 用户评审
            #    await self._user_review(problem_id, solution_response)
            # 暂时不考虑用户评审问题

            #遍历子实施问题，右端入队
            result = self.database_manager.get_node_id_by_title_query(solution_request.title)
            assert result["success"]
            solution_id = result["data"]["id"]
            await self._enqueue_sub_problems(solution_id)

        except Exception as e:
            logger.error(f"创建解决方案失败: {e}")
            await self._publish_error_patch(f"创建解决方案失败: {str(e)}")
            raise e
    
    
    #async def _supervisor_review(self, problem_id: str, supervisor_id: str, solution_response: CreateSolutionResponse) -> None:
    #    """
    #    监督者评审
    #    
    #    Args:
    #        problem_id: 问题ID
    #        supervisor_id: 监督者ID
    #        solution_response: 解决方案响应
    #    """
    #    try:
    #        # 获取监督者可见的消息列表
    #        visible_messages = await self.get_visible_messages(supervisor_id, "problem")
    #        
    #        # 构建评审提示词
    #        review_prompt = self._build_review_prompt(problem_id, solution_response, visible_messages)
    #        
    #        # 调用LLM进行评审决策
    #        review_decision = await self._call_llm_with_retry(
    #            prompt=review_prompt,
    #            title="监督者评审决策",
    #            validator=ReviewDecision
    #        )
    #        
    #        # 发布评审结果patch
    #        await self._publish_review_decision_patch(supervisor_id, problem_id, review_decision)
    #        
    #        # 根据评审结果处理
    #        if review_decision.decision == "pass":
    #            # 通过，将子问题入队
    #            await self._enqueue_sub_problems(problem_id, problem_id)
    #        elif review_decision.decision == "modify":
    #            # 要求修改，等待被监督者回应
    #            await self._wait_for_modification_response(problem_id, supervisor_id, review_decision)
    #        else:  # reject
    #            # 拒绝，结束处理
    #            await self._publish_rejection_patch(problem_id, review_decision)
    #            
    #    except Exception as e:
    #        logger.error(f"监督者评审失败: {e}")
    #        await self._publish_error_patch(f"监督者评审失败: {str(e)}")
    #        raise e
    
    #async def _wait_for_modification_response(self, problem_id: str, supervisor_id: str, review_decision: ReviewDecision) -> None:
    #    """
    #    等待被监督者对修改意见的回应
    #    
    #    Args:
    #        problem_id: 问题ID
    #        supervisor_id: 监督者ID
    #        review_decision: 评审决策
    #    """
    #    try:
    #        # 获取被监督者可见的消息列表
    #        visible_messages = await self.get_visible_messages(problem_id, "problem")
    #        
    #        # 构建修改决策提示词
    #        modification_prompt = self._build_modification_decision_prompt(
    #            problem_id, supervisor_id, review_decision, visible_messages
    #        )
    #        
    #        # 调用LLM进行修改决策
    #        modification_decision = await self._call_llm_with_retry(
    #            prompt=modification_prompt,
    #            title="修改意见决策",
    #            validator=ModificationDecision
    #        )
    #        
    #        # 发布修改决策patch
    #        await self._publish_modification_decision_patch(problem_id, modification_decision)
    #        
    #        # 根据决策处理
    #        if modification_decision.decision == "accept":
    #            # 同意修改，执行修改
    #            await self._modify_solution_for_problem(problem_id, review_decision)
    #        elif modification_decision.decision == "reply":
    #            # 回复澄清，重新评审
    #            await self._publish_clarification_reply_patch(problem_id, modification_decision)
    #            # 将问题重新入队，等待监督者重新评审
    #            self.problem_queue.appendleft((problem_id, supervisor_id, None))
    #        else:  # reject
    #            # 拒绝修改，结束处理
    #            await self._publish_modification_rejection_patch(problem_id, modification_decision)
    #            
    #    except Exception as e:
    #        logger.error(f"等待修改回应失败: {e}")
    #        await self._publish_error_patch(f"等待修改回应失败: {str(e)}")
    #        raise e
    
    #async def _modify_solution_for_problem(self, problem_id: str, review_decision: ReviewDecision) -> None:
    #    """
    #    为问题修改解决方案
    #    
    #    Args:
    #        problem_id: 问题ID
    #        review_decision: 评审决策
    #    """
    #    try:
    #        # 获取当前解决方案
    #        current_solution = await self._get_current_solution(problem_id)
    #        if not current_solution:
    #            raise ValueError(f"问题 {problem_id} 没有当前解决方案")
    #        
    #        # 获取可见消息列表
    #        visible_messages = await self.get_visible_messages(problem_id, "problem")
    #        
    #        # 构建修改解决方案提示词
    #        modification_prompt = self._build_solution_modification_prompt(
    #            problem_id, current_solution, review_decision, visible_messages
    #        )
    #        
    #        # 调用LLM修改解决方案
    #        modified_solution = await self._call_llm_with_retry(
    #            prompt=modification_prompt,
    #            title="修改解决方案",
    #            validator=ModifySolutionRequest
    #        )
    #        
    #        # 发布修改结果patch
    #        await self._publish_solution_modified_patch(problem_id, modified_solution)
    #        
    #        # 检查是否为自我修改（监督者成为被监督者）
    #        if await self._is_self_modification(problem_id):
    #            await self._handle_self_modification(problem_id)
    #        else:
    #            # 将子问题入队
    #            await self._enqueue_sub_problems(problem_id, problem_id)
    #            
    #    except Exception as e:
    #        logger.error(f"修改解决方案失败: {e}")
    #        await self._publish_error_patch(f"修改解决方案失败: {str(e)}")
    #        raise e
    
    #async def _handle_self_modification(self, problem_id: str) -> None:
    #    """
    #    处理自我修改情况
    #    
    #    Args:
    #        problem_id: 问题ID
    #    """
    #    try:
    #        # 获取父问题ID
    #        parent_problem_id = await self._get_parent_problem_id(problem_id)
    #        if not parent_problem_id:
    #            return
    #        
    #        # 队列顶部所有A的子实施问题的节点出队
    #        # 队列底部所有A的孙实施问题节点出队
    #        self._remove_descendant_problems_from_queue(problem_id)
    #        
    #        # 反向遍历A的所有子实施问题q: (q, A)，依次从顶部入队
    #        await self._enqueue_descendant_problems_reversed(parent_problem_id, problem_id)
    #        
    #        logger.info(f"处理自我修改，问题 {problem_id} 成为监督者")
    #        
    #    except Exception as e:
    #        logger.error(f"处理自我修改失败: {e}")
    #        raise e
    
    #def _remove_descendant_problems_from_queue(self, problem_id: str) -> None:
    #    """
    #    从队列中移除指定问题的所有后代问题
    #    
    #    Args:
    #        problem_id: 问题ID
    #    """
    #    # 获取所有后代问题ID
    #    descendant_ids = set()
    #    self._collect_descendant_ids(problem_id, descendant_ids)
    #    
    #    # 从队列中移除
    #    new_queue = deque()
    #    for item in self.problem_queue:
    #        item_problem_id = item[0]
    #        if item_problem_id not in descendant_ids:
    #            new_queue.append(item)
    #    
    #    self.problem_queue = new_queue
    #    logger.info(f"从队列中移除问题 {problem_id} 的 {len(descendant_ids)} 个后代问题")
    
    #def _collect_descendant_ids(self, problem_id: str, descendant_ids: set) -> None:
    #    """
    #    收集指定问题的所有后代问题ID
    #    
    #    Args:
    #        problem_id: 问题ID
    #        descendant_ids: 后代ID集合
    #    """
    #    if not self.query_database_func:
    #        return
    #    
    #    try:
    #        # 查询问题的子问题
    #        # 这里需要实现递归查询子问题的逻辑
    #        # 暂时跳过
    #        pass
    #    except Exception as e:
    #        logger.error(f"收集后代问题ID失败: {e}")
    #        raise e
    
    async def _enqueue_descendant_problems_reversed(self, parent_problem_id: str, supervisor_id: str) -> None:
        """
        反向遍历所有子实施问题，依次从顶部入队
        
        Args:
            parent_problem_id: 父问题ID
            supervisor_id: 监督者ID
        """
        if not self.query_database_func:
            return
        
        try:
            # 获取所有子实施问题
            # 这里需要实现获取子问题的逻辑
            # 暂时跳过
            logger.info(f"将问题 {parent_problem_id} 的子问题反向入队")
        except Exception as e:
            logger.error(f"获取子问题失败: {e}")
            raise e
    
    async def _is_self_modification(self, problem_id: str) -> bool:
        """
        检查是否为自我修改（监督者成为被监督者）
        
        Args:
            problem_id: 问题ID
            
        Returns:
            是否为自我修改
        """
        # 这里需要检查问题是否成为其父问题的监督者
        # 暂时返回False
        return False
    
    async def _get_parent_problem_id(self, problem_id: str) -> Optional[str]:
        """
        获取问题的父问题ID
        
        Args:
            problem_id: 问题ID
            
        Returns:
            父问题ID，如果不存在返回None
        """
        if not self.query_database_func:
            return None
        
        try:
            # 这里需要实现查找父问题的逻辑
            # 暂时返回None
            return None
        except Exception as e:
            logger.error(f"获取父问题ID失败: {e}")
            raise e
    
    async def _get_current_solution(self, problem_id: str) -> Optional[Dict[str, Any]]:
        """
        获取问题的当前解决方案
        
        Args:
            problem_id: 问题ID
            
        Returns:
            解决方案信息，如果不存在返回None
        """
        if not self.query_database_func:
            return None
        
        try:
            # 这里需要实现获取当前解决方案的逻辑
            # 暂时返回None
            return None
        except Exception as e:
            logger.error(f"获取当前解决方案失败: {e}")
            raise e
    
    
    #async def _publish_review_decision_patch(self, supervisor_id: str, problem_id: str, review_decision: ReviewDecision) -> None:
    #    """
    #    发布评审决策patch
    #    
    #    Args:
    #        supervisor_id: 监督者ID
    #        problem_id: 问题ID
    #        review_decision: 评审决策
    #    """
    #    patch = self._create_patch(
    #        title=f"监督者 {supervisor_id} 评审决策",
    #        content_delta=f"评审结果: {review_decision.decision}\n"
    #                     f"评审意见: {review_decision.feedback}\n"
    #                     f"修改建议: {review_decision.modification_suggestions or '无'}",
    #        finished=True
    #    )
    #    
    #    await self.publish_callback(patch)
    
    #async def _publish_modification_decision_patch(self, problem_id: str, modification_decision: ModificationDecision) -> None:
    #    """
    #    发布修改决策patch
    #    
    #    Args:
    #        problem_id: 问题ID
    #        modification_decision: 修改决策
    #    """
    #    patch = self._create_patch(
    #        title=f"问题 {problem_id} 修改决策",
    #        content_delta=f"决策结果: {modification_decision.decision}\n"
    #                     f"回复内容: {modification_decision.response}",
    #        finished=True
    #    )
    #    
    #    await self.publish_callback(patch)
    
    #async def _publish_solution_modified_patch(self, problem_id: str, modified_solution: ModifySolutionRequest) -> None:
    #    """
    #    发布解决方案修改patch
    #    
    #    Args:
    #        problem_id: 问题ID
    #        modified_solution: 修改后的解决方案
    #    """
    #    patch = self._create_patch(
    #        title=f"问题 {problem_id} 解决方案已修改",
    #        content_delta=f"修改后的标题: {modified_solution.title or '保持不变'}\n"
    #                     f"修改后的顶层思考: {modified_solution.top_level_thoughts or '保持不变'}\n"
    #                     f"修改后的实施方案: {len(modified_solution.implementation_plan)} 个步骤\n"
    #                     f"修改后的方案论证: {modified_solution.plan_justification or '保持不变'}\n"
    #                     f"修改后的收尾任务: {modified_solution.finishing_task or '保持不变'}",
    #        finished=True
    #    )
    #    
    #    await self.publish_callback(patch)
    
    #async def _publish_rejection_patch(self, problem_id: str, review_decision: ReviewDecision) -> None:
    #    """
    #    发布拒绝patch
    #    
    #    Args:
    #        problem_id: 问题ID
    #        review_decision: 评审决策
    #    """
    #    patch = self._create_patch(
    #        title=f"问题 {problem_id} 解决方案被拒绝",
    #        content_delta=f"拒绝原因: {review_decision.feedback}",
    #        finished=True
    #    )
    #    
    #    await self.publish_callback(patch)
    #
    #async def _publish_clarification_reply_patch(self, problem_id: str, modification_decision: ModificationDecision) -> None:
    #    """
    #    发布澄清回复patch
    #    
    #    Args:
    #        problem_id: 问题ID
    #        modification_decision: 修改决策
    #    """
    #    patch = self._create_patch(
    #        title=f"问题 {problem_id} 澄清回复",
    #        content_delta=f"回复内容: {modification_decision.response}",
    #        finished=True
    #    )
    #    
    #    await self.publish_callback(patch)
    #
    #async def _publish_modification_rejection_patch(self, problem_id: str, modification_decision: ModificationDecision) -> None:
    #    """
    #    发布修改拒绝patch
    #    
    #    Args:
    #        problem_id: 问题ID
    #        modification_decision: 修改决策
    #    """
    #    patch = self._create_patch(
    #        title=f"问题 {problem_id} 修改被拒绝",
    #        content_delta=f"拒绝原因: {modification_decision.response}",
    #        finished=True
    #    )
    #    
    #    await self.publish_callback(patch)
        
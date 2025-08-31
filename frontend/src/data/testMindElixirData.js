/**
 * Mind-elixir测试数据 - 现代化设计
 * 
 * 基于真实的研究树数据结构设计，展示问题-解决方案的层级关系
 * 采用现代化配色方案和简洁的视觉风格
 */

import { ResearchTreeTransformer } from '@/services/ResearchTreeTransformer.js'

// 后端数据格式的测试数据
export const mockBackendSnapshotData = {
  id: 'snapshot-2024-01-01-001',
  created_at: '2024-01-01T10:00:00Z',
  roots: [
    {
      id: '9f6a4b02-6798-421f-ae43-c1d291723279',
      type: 'problem',
      title: '周扫红外搜索系统对空中小目标（飞机、导弹、无人机）的检测与告警技术',
      problem_type: 'implementation',
      significance: '提升国防安全能力，增强对空中威胁的早期预警',
      criteria: '检测率>95%，误报率<5%，响应时间<100ms',
      selected_solution_id: 'e4448bcf-0e96-4538-9800-6411c2f339c8',
      created_at: '2024-01-01T09:00:00Z',
      children: [
        {
          id: 'e4448bcf-0e96-4538-9800-6411c2f339c8',
          type: 'solution',
          title: '基于多阶段处理与深度学习融合的周扫红外小目标检测框架',
          top_level_thoughts: '采用预处理+深度学习+后处理的多阶段架构',
          finishing_task: '构建完整的检测告警系统',
          plan_justification: '结合传统图像处理和现代深度学习优势',
          state: 'in_progress',
          created_at: '2024-01-01T09:15:00Z',
          children: [
            {
              id: '30e3a69a-cf22-438f-a95f-64b94fcf4fa4',
              type: 'problem',
              title: '当前红外传感器在典型操作条件下对小目标（1-10像素）的信噪比是否满足检测要求？',
              problem_type: 'conditional',
              significance: '验证硬件基础是否支持算法需求',
              criteria: '信噪比>3dB',
              created_at: '2024-01-01T09:30:00Z',
              children: []
            },
            {
              id: '8b2a1c3d-4e5f-6789-abcd-ef1234567890',
              type: 'problem',
              title: '现有弱小目标检测算法在模拟红外数据上的表现是否达到基础指标？',
              problem_type: 'conditional',
              significance: '评估现有技术基础',
              criteria: '检测率>85%作为起始点',
              created_at: '2024-01-01T09:45:00Z',
              children: []
            },
            {
              id: '1a2b3c4d-5e6f-7890-abcd-ef1234567890',
              type: 'problem',
              title: '如何设计一个实时预处理模块来抑制红外图像中的背景杂波和噪声？',
              problem_type: 'implementation',
              significance: '提高后续检测算法的输入质量',
              criteria: '处理时间<10ms，噪声抑制率>80%',
              selected_solution_id: 'solution-1-1',
              created_at: '2024-01-01T10:00:00Z',
              children: [
                {
                  id: 'solution-1-1',
                  type: 'solution',
                  title: '基于时空滤波的背景抑制方案',
                  top_level_thoughts: '利用连续帧间的时间相关性和空间邻域信息',
                  finishing_task: '实现实时背景建模和前景提取',
                  plan_justification: '计算复杂度低，适合实时处理',
                  state: 'completed',
                  final_report: '已实现，处理时间6ms，噪声抑制率85%',
                  created_at: '2024-01-01T10:15:00Z',
                  children: []
                },
                {
                  id: 'solution-1-2', 
                  type: 'solution',
                  title: '基于机器学习的自适应背景建模',
                  top_level_thoughts: '使用在线学习算法适应环境变化',
                  finishing_task: '构建自适应背景更新机制',
                  plan_justification: '更强的环境适应性',
                  state: 'in_progress',
                  created_at: '2024-01-01T10:30:00Z',
                  children: []
                }
              ]
            },
            {
              id: '2b3c4d5e-6f78-9012-3456-789abcdef012',
              type: 'problem',
              title: '如何构建一个基于深度学习的小目标检测模型，兼顾高检测率和低误报？',
              problem_type: 'implementation',
              significance: '核心检测算法实现',
              criteria: '检测率>95%，误报率<5%',
              created_at: '2024-01-01T10:45:00Z',
              children: [
                {
                  id: 'solution-2-1',
                  type: 'solution',
                  title: '改进的YOLO小目标检测网络',
                  top_level_thoughts: '针对小目标优化网络结构和损失函数',
                  finishing_task: '训练并部署检测模型',
                  plan_justification: '成熟的检测框架，便于优化',
                  state: 'failed',
                  final_report: '小目标检测效果不理想，需要重新设计网络结构',
                  created_at: '2024-01-01T11:00:00Z',
                  children: []
                }
              ]
            },
            {
              id: '3c4d5e6f-7890-1234-5678-9abcdef01234',
              type: 'problem',
              title: '如何实现一个后处理模块来减少误报并生成告警？',
              problem_type: 'implementation',
              significance: '提高系统实用性，减少误报干扰',
              criteria: '误报率降低50%以上',
              created_at: '2024-01-01T11:15:00Z',
              children: []
            }
          ]
        },
        {
          id: 'alternative-solution-1',
          type: 'solution',
          title: '传统图像处理与机器学习混合方案',
          top_level_thoughts: '结合传统特征提取和浅层机器学习',
          finishing_task: '构建混合检测系统',
          plan_justification: '计算资源需求较低',
          state: 'deprecated',
          final_report: '性能不如深度学习方案，已废弃',
          created_at: '2024-01-01T09:10:00Z',
          children: []
        }
      ]
    }
  ]
}

// 使用转换器生成的现代化Mind-elixir数据
const transformer = new ResearchTreeTransformer()

export const testMindElixirData = transformer.transformToMindElixir(mockBackendSnapshotData, {
  selectedSolutionIds: transformer.extractSelectedSolutionIds(mockBackendSnapshotData)
})

/**
 * 快照查看模式的测试数据
 */
export const testSnapshotMindElixirData = transformer.transformToMindElixir(mockBackendSnapshotData, {
  isSnapshotView: true,
  selectedSolutionIds: transformer.extractSelectedSolutionIds(mockBackendSnapshotData)
})

/**
 * 智能体操作中的测试数据
 */
export const testAgentOperatingData = transformer.transformToMindElixir(mockBackendSnapshotData, {
  agentOperatingNodeId: '1a2b3c4d-5e6f-7890-abcd-ef1234567890',
  selectedSolutionIds: transformer.extractSelectedSolutionIds(mockBackendSnapshotData)
})

// 简化的测试数据导出（向后兼容）
export { testMindElixirData as simpleMindElixirData }
export { testSnapshotMindElixirData as styledMindElixirData }

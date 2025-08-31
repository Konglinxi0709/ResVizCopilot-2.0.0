/**
 * Mind-elixir测试数据
 * 
 * 基于真实的研究树数据结构设计，展示问题-解决方案的层级关系
 * 包含多种节点类型和状态，用于验证Mind-elixir渲染功能
 */
export const testMindElixirData = {
  nodeData: {
    id: 'root',
    topic: '科研智能体研究树',
    children: [
      {
        id: '9f6a4b02-6798-421f-ae43-c1d291723279',
        topic: '周扫红外搜索系统对空中小目标（飞机、导弹、无人机）的检测与告警技术',
        style: {
          background: '#e6f7ff',
          color: '#1890ff',
          borderColor: '#409eff',
          borderWidth: '2px'
        },
        tags: ['实施问题', '根问题'],
        icons: ['🎯'],
        children: [
          {
            id: 'e4448bcf-0e96-4538-9800-6411c2f339c8',
            topic: '基于多阶段处理与深度学习融合的周扫红外小目标检测框架',
            style: {
              background: '#f9f0ff',
              color: '#722ed1',
              borderColor: '#722ed1',
              borderWidth: '3px' // 选中方案加粗边框
            },
            tags: ['解决方案', '已选中'],
            icons: ['⭐', '🔄'],
            children: [
              {
                id: '30e3a69a-cf22-438f-a95f-64b94fcf4fa4',
                topic: '当前红外传感器在典型操作条件下对小目标（1-10像素）的信噪比是否满足检测要求？',
                style: {
                  background: '#fff1f0',
                  color: '#ff4d4f',
                  borderColor: '#ff4d4f'
                },
                tags: ['条件问题'],
                icons: ['❓'],
                children: []
              },
              {
                id: '8b2a1c3d-4e5f-6789-abcd-ef1234567890',
                topic: '现有弱小目标检测算法在模拟红外数据上的表现是否达到基础指标？',
                style: {
                  background: '#fff1f0',
                  color: '#ff4d4f',
                  borderColor: '#ff4d4f'
                },
                tags: ['条件问题'],
                icons: ['❓'],
                children: []
              },
              {
                id: '1a2b3c4d-5e6f-7890-abcd-ef1234567890',
                topic: '如何设计一个实时预处理模块来抑制红外图像中的背景杂波和噪声？',
                style: {
                  background: '#e6f7ff',
                  color: '#1890ff',
                  borderColor: '#1890ff'
                },
                tags: ['实施问题'],
                icons: ['🛠️'],
                children: [
                  {
                    id: 'solution-1-1',
                    topic: '基于时空滤波的背景抑制方案',
                    style: {
                      background: '#f6ffed',
                      color: '#52c41a',
                      borderColor: '#52c41a'
                    },
                    tags: ['解决方案', '成功'],
                    icons: ['✅'],
                    children: []
                  },
                  {
                    id: 'solution-1-2',
                    topic: '基于机器学习的自适应背景建模',
                    style: {
                      background: '#fff7e6',
                      color: '#fa8c16',
                      borderColor: '#fa8c16'
                    },
                    tags: ['解决方案', '进行中'],
                    icons: ['🔄'],
                    children: []
                  }
                ]
              },
              {
                id: '2b3c4d5e-6f78-9012-3456-789abcdef012',
                topic: '如何构建一个基于深度学习的小目标检测模型，兼顾高检测率和低误报？',
                style: {
                  background: '#e6f7ff',
                  color: '#1890ff',
                  borderColor: '#1890ff'
                },
                tags: ['实施问题'],
                icons: ['🛠️'],
                children: [
                  {
                    id: 'solution-2-1',
                    topic: '改进的YOLO小目标检测网络',
                    style: {
                      background: '#fff2e8',
                      color: '#fa541c',
                      borderColor: '#fa541c'
                    },
                    tags: ['解决方案', '失败'],
                    icons: ['❌'],
                    children: []
                  }
                ]
              },
              {
                id: '3c4d5e6f-7890-1234-5678-9abcdef01234',
                topic: '如何实现一个后处理模块来减少误报并生成告警？',
                style: {
                  background: '#e6f7ff',
                  color: '#1890ff',
                  borderColor: '#1890ff'
                },
                tags: ['实施问题'],
                icons: ['🛠️'],
                children: []
              }
            ]
          },
          {
            id: 'alternative-solution-1',
            topic: '传统图像处理与机器学习混合方案',
            style: {
              background: '#f0f0f0',
              color: '#8c8c8c',
              borderColor: '#d9d9d9',
              opacity: '0.7'
            },
            tags: ['解决方案', '已弃用'],
            icons: ['📋'],
            children: []
          }
        ]
      }
    ]
  },
  theme: {
    name: 'ResearchTree',
    palette: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399'],
    cssVar: {
      '--main-color': '#444446',
      '--main-bgcolor': '#ffffff',
      '--color': '#777777',
      '--bgcolor': '#f6f6f6'
    }
  }
}

/**
 * 快照查看模式的测试数据（降低透明度的版本）
 */
export const testSnapshotMindElixirData = {
  nodeData: {
    ...testMindElixirData.nodeData,
    // 递归应用快照样式
    children: testMindElixirData.nodeData.children.map(child => ({
      ...child,
      style: {
        ...child.style,
        opacity: '0.8'
      },
      icons: [...(child.icons || []), '📸']
    }))
  },
  theme: {
    name: 'Snapshot',
    palette: ['#bdc3c7', '#95a5a6', '#7f8c8d', '#34495e', '#2c3e50'],
    cssVar: {
      '--main-color': '#666666',
      '--main-bgcolor': '#f5f5f5',
      '--color': '#999999',
      '--bgcolor': '#fafafa'
    }
  }
}

/**
 * 智能体操作中的测试数据
 */
export const testAgentOperatingData = {
  ...testMindElixirData,
  agentOperatingNodeId: '1a2b3c4d-5e6f-7890-abcd-ef1234567890' // 正在操作的节点
}

/**
 * 简化的Mind-elixir测试数据
 * 用于验证基础渲染功能
 */

// 使用MindElixir的标准方法创建简单数据
export const simpleMindElixirData = {
  nodeData: {
    id: 'root',
    topic: '研究树根节点',
    children: [
      {
        id: 'problem-1',
        topic: '研究问题1: 红外目标检测',
        children: [
          {
            id: 'solution-1',
            topic: '解决方案1: 深度学习方法',
            children: []
          },
          {
            id: 'solution-2', 
            topic: '解决方案2: 传统图像处理',
            children: []
          }
        ]
      },
      {
        id: 'problem-2',
        topic: '研究问题2: 实时处理优化',
        children: [
          {
            id: 'solution-3',
            topic: '解决方案3: 硬件加速',
            children: []
          }
        ]
      }
    ]
  }
}

// 带样式的测试数据
export const styledMindElixirData = {
  nodeData: {
    id: 'root',
    topic: '科研智能体研究树',
    children: [
      {
        id: 'problem-main',
        topic: '周扫红外搜索系统对空中小目标检测技术',
        style: {
          background: '#e6f7ff',
          color: '#1890ff'
        },
        tags: ['实施问题'],
        children: [
          {
            id: 'solution-main',
            topic: '基于深度学习的检测框架',
            style: {
              background: '#f9f0ff',
              color: '#722ed1'
            },
            tags: ['解决方案', '已选中'],
            children: [
              {
                id: 'sub-problem-1',
                topic: '传感器信噪比验证',
                style: {
                  background: '#fff1f0',
                  color: '#ff4d4f'
                },
                tags: ['条件问题'],
                children: []
              },
              {
                id: 'sub-problem-2',
                topic: '预处理模块设计',
                style: {
                  background: '#e6f7ff',
                  color: '#1890ff'
                },
                tags: ['实施问题'],
                children: []
              }
            ]
          }
        ]
      }
    ]
  }
}

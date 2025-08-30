<template>
  <div class="mind-map-container">
    <div ref="mapEl" id="map"></div>
    <div class="export-btn" @click="download">
      <el-icon><Camera /></el-icon>
    </div>
    <div v-if="showConfirmDialog" class="confirm-dialog">
      <div class="confirm-content">
        <p>{{ confirmMessage }}</p>
        <div class="button-group">
          <button class="confirm-btn" @click="confirmSelection">{{ confirmButtonText }}</button>
          <button class="cancel-btn" @click="cancelSelection">{{ cancelButtonText }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import initialMindMapData from '@/scripts/mindInitData'
import MindElixir from 'mind-elixir'
import { Camera } from '@element-plus/icons-vue'
import { domToPng } from '@ssshooter/modern-screenshot'

export default {
  name: 'MindMap',
  emits: ['update-focus-problem'],
  components: { // 注册Camera组件
    Camera
  },
  data() {
    return {
      mind: null,
      currentFocusProblem: null,
      showConfirmDialog: false,
      selectedNode: null,
      operationTimeout: null,
      isUnselecting: false,
      confirmMessage: '',
      confirmButtonText: '',
      cancelButtonText: ''
    }
  },
  async mounted() {
    await this.loadMindMapDataFromServer()
  },
  beforeUnmount() {
    if (this.mind) {
      this.mind.destroy()
    }
  },
  methods: {
    async download() {
      try {
        const dataUrl = await domToPng(this.$refs.mapEl, {
          onCloneNode: node => {
            const n = node
            // 重置样式确保截图正常
            n.style.position = ''
            n.style.top = ''
            n.style.left = ''
            n.style.bottom = ''
            n.style.right = ''
            return n
          },
          padding: 100,  // 增加边距
          quality: 1,     // 最高质量
        })
        
        const link = document.createElement('a')
        link.download = 'mindmap-screenshot.png'
        link.href = dataUrl
        link.click()
      } catch (error) {
        console.error('导出截图失败:', error)
        this.$message.error(this.$t('mindTree.errors.exportFailed'))
      }
    },
    async loadMindMapDataFromServer() {
      try {
        const response = await axios.get('/api/research/mind_map')
        if (response.data.success && response.data.mind_map_data) {
          this.initializeMindMap(response.data.mind_map_data)
        } else {
          this.initializeMindMap(initialMindMapData)
        }
      } catch (error) {
        console.error('加载思维导图数据失败:', error)
        this.initializeMindMap(initialMindMapData)
      }
    },

    initializeMindMap(data) {
      this.mind = new MindElixir({
        el: this.$refs.mapEl,
        before: {
          //禁用这两个功能，与问题树的功能需求不符
          copyNode() {
            return false
          },
          copyNodes() {
            return false
          }
        }
      })

      const operationNames = [
        'insertSibling', 'insertParent', 'addChild', 'moveUpNode', 'moveDownNode',
        'removeNode', 'removeNodes', 'moveNodeIn', 'moveNodeBefore', 'moveNodeAfter',
        'finishEdit'
      ]

      this.mind.bus.addListener('operation', (operation) => {
        if (operationNames.includes(operation.name)) {
          console.log('操作:', operation.name)
          
          // 防抖处理，避免频繁更新
          if (this.operationTimeout) {
            clearTimeout(this.operationTimeout)
          }
          
          this.operationTimeout = setTimeout(() => {
            this.syncToServer()
          }, 3000)
        }
      })

      // 添加节点选择监听
      this.mind.bus.addListener('selectNode', (nodeObj, clickEvent) => {
        if (clickEvent && nodeObj.id !== 'me-root') {
          this.selectedNode = nodeObj
          
          // 判断是否是当前焦点问题
          if (this.currentFocusProblem === nodeObj.id) {
            // 如果已经是焦点问题，询问是否取消选中
            this.isUnselecting = true
            this.confirmMessage = this.$t('mindTree.confirm.unselect')
            this.confirmButtonText = this.$t('mindTree.confirm.yesUnselect')
            this.cancelButtonText = this.$t('mindTree.confirm.noKeepSelected')
          } else {
            // 如果不是焦点问题，询问是否设为焦点问题
            this.isUnselecting = false
            this.confirmMessage = this.$t('mindTree.confirm.select')
            this.confirmButtonText = this.$t('mindTree.confirm.yes')
            this.cancelButtonText = this.$t('mindTree.confirm.no')
          }
          
          this.showConfirmDialog = true
        }
      })

      this.mind.bus.addListener('unselectNode', () => {
        this.showConfirmDialog = false
        this.selectedNode = null
      })

      // 确保根节点有id
      if (!data.nodeData.id) {
        data.nodeData.id = 'me-root'
      }
      
      // 处理数据中的节点，查找当前关注问题节点并清除其他节点的特殊样式
      let foundFocusNode = false;
      
      // 递归处理节点
      const processNode = (node) => {
        if (node.icons && node.icons.includes('💡') && !foundFocusNode) {
          // 找到第一个标记为关注节点的节点
          this.currentFocusProblem = node.id;
          foundFocusNode = true;
        } else if (node.id !== 'me-root') {
          // 清除非根节点的style和icons
          delete node.style;
          delete node.icons;
        }
        
        // 递归处理子节点
        if (node.children && node.children.length > 0) {
          node.children.forEach(child => processNode(child));
        }
      };
      
      // 开始处理
      processNode(data.nodeData);
      
      console.log('初始化数据:', data)
      console.log('初始化时发现选中的问题节点:', this.currentFocusProblem)
      
      this.mind.init(data)
      
      // 如果找到了关注节点，将其同步到后端并通知父组件
      if (foundFocusNode && this.currentFocusProblem) {
        this.updateFocusProblem(this.currentFocusProblem)
      }
    },

    async syncToServer() {
      try {
        const mindMapData = this.mind.getData()
        
        // 检查当前关注问题是否仍然存在
        const isCurrentFocusProblemExists = this.checkFocusProblemExists()
        
        // 如果当前关注问题已被删除，清空关注问题指针
        if (this.currentFocusProblem && !isCurrentFocusProblemExists) {
          this.currentFocusProblem = null
        }
        
        const response = await axios.post('/api/research/state/update', {
          mind_map_data: mindMapData,
          current_focus: {
            current_focus_problem: this.currentFocusProblem || ""
          }
        })
        console.log('同步思维导图数据到服务器成功:', response.data)
        
        // 通知父组件当前焦点问题的变化
        this.$emit('update-focus-problem', this.currentFocusProblem)
      } catch (error) {
        console.error('同步思维导图数据到服务器失败:', error)
      }
    },
    
    // 检查当前关注问题节点是否仍然存在于思维导图中
      checkFocusProblemExists() {
      if (!this.currentFocusProblem) return false;

      try {
        const node = this.mind.findEle(this.currentFocusProblem);
        return !!node;
      } catch (error) {
        // 检查错误信息是否为节点未找到的情况
        if (error.message.includes('not found')) {
          return false;
        }
        // 其他错误重新抛出
        throw error;
      }
    },
    
    // 更新关注问题的统一方法
    async updateFocusProblem(problemId) {
      try {
        await axios.post('/api/research/state/focus', {
          problemId: problemId || ""
        })
        
        // 通知父组件更新焦点问题
        this.$emit('update-focus-problem', problemId)
      } catch (error) {
        console.error('更新聚焦问题失败:', error)
      }
    },

    async confirmSelection() {
      if (!this.selectedNode) return

      if (this.isUnselecting) {
        // 取消选中当前焦点问题
        this.clearFocusStyle()
        this.currentFocusProblem = null
        
        // 更新服务器端的当前聚焦问题
        this.updateFocusProblem(null)
      } else {
        // 设置新的焦点问题
      // 清除之前节点的样式
        this.clearFocusStyle()

        // 设置新节点样式
        this.currentFocusProblem = this.selectedNode.id
        const currentNode = this.mind.currentNode
        if (currentNode) {
          this.applyFocusStyle(currentNode)
        }
        
        // 更新服务器端的当前聚焦问题
        this.updateFocusProblem(this.currentFocusProblem)
      }

      this.showConfirmDialog = false
    },

    clearFocusStyle() {
      if (this.currentFocusProblem) {
        const prevNode = this.mind.findEle(this.currentFocusProblem)
        if (prevNode) {
          this.mind.reshapeNode(prevNode, {
            style: {
              background: undefined,
              fontWeight: undefined
            },
            icons: []
          })
        }
      }
    },

    applyFocusStyle(node) {
      this.mind.reshapeNode(node, {
          style: {
            background: '#e0e0e0',
            fontWeight: 'bold'
          },
          icons: ['💡']
        })
    },

    cancelSelection() {
      this.showConfirmDialog = false
      this.selectedNode = null
    },

    // 处理来自AI的添加节点命令
    handleAddNodeCommand(nodeData) {
      // 查找父节点
      let parentNode = null
      if (nodeData.rootId) {
        parentNode = this.mind.findEle(nodeData.rootId)
      } else {
        // 如果没有指定父节点，使用根节点
        parentNode = this.mind.findEle('me-root')
      }
      
      if (!parentNode) {
        console.error('未找到父节点:', nodeData.rootId)
        return
      }
      
      // 创建新节点
      const newNode = {
        topic: nodeData.viewName,
        tags: nodeData.poser === 'ai' ? ['AI'] : [],
        id: Math.random().toString(36).substring(2) + Date.now().toString(36)
      }
      
      // 添加到思维导图
      const addedNode = this.mind.addChild(parentNode, newNode)
      
      // 同步到服务器
      this.syncToServer()
      
      return addedNode
    },

    // 新增方法：将AI节点转为用户节点
    convertAINodeToUserNode(nodeId) {
      if (!nodeId || !this.mind) return false;
      
      try {
        const node = this.mind.findEle(nodeId);
        if (!node) {
          console.error('未找到节点:', nodeId);
          return false;
        }
        
        // 删除tags属性（AI标签）
        this.mind.reshapeNode(node, { tags: [] });
        
        // 同步到服务器
        this.syncToServer();
        
        console.log('成功将节点从AI转换为用户节点:', nodeId);
        return true;
      } catch (error) {
        console.error('转换节点失败:', error);
        return false;
      }
    }
  }
}
</script>

<style scoped>
.mind-map-container {
  width: 100%;
  height: 100%;
  position: relative;
}

#map {
  height: 100%;
  width: 100%;
}

.export-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 500;
  background: white;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2);
  cursor: pointer;
  transition: all 0.3s;
}

.export-btn:hover {
  background: #f5f5f5;
  transform: scale(1.05);
  box-shadow: 0 4px 8px rgba(0,0,0,0.25);
}


.confirm-dialog {
  position: absolute;
  top: 20%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.confirm-content {
  text-align: center;
}

.confirm-content p {
  margin-bottom: 15px;
  color: #2c3e50;
}

.button-group {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 15px;
}

.confirm-btn, .cancel-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.confirm-btn {
  background-color: #27ae60;
  color: white;
}

.confirm-btn:hover {
  background-color: #219a52;
}

.cancel-btn {
  background-color: #e74c3c;
  color: white;
}

.cancel-btn:hover {
  background-color: #c0392b;
}

/* 深度选择器处理第三方库样式 */
::v-deep #map * {
  box-sizing: border-box;
}
</style>
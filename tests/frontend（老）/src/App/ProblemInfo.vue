<template>
  <div class="problem-info-container">
    <el-empty v-if="!currentProblemId" :description="$t('problemInfo.empty')"></el-empty>
    
    <div v-else class="problem-info" :class="{ 'edit-mode': editMode }">
      <!-- 问题标题和操作按钮 -->
      <div class="problem-header">
        <h2>{{ currentProblem.viewName }}</h2>
        <div class="problem-actions">
          <el-button v-if="!editMode" type="primary" size="small" @click="enterEditMode">
            <el-icon><Edit /></el-icon>{{ $t('problemInfo.edit') }}
          </el-button>
          <template v-else>
            <el-button @click="cancelEdit" size="small">{{ $t('problemInfo.cancel') }}</el-button>
            <el-button type="primary" @click="saveProblemInfo" size="small">{{ $t('problemInfo.save') }}</el-button>
          </template>
        </div>
      </div>

      <!-- 问题描述 -->
      <div class="info-section">
        <h3>{{ $t('problemInfo.description.title') }}</h3>
        <div v-if="!editMode" class="content-display">
          <MarkdownRenderer :content="currentProblem.description || $t('problemInfo.notSet')" />
        </div>
        <div v-else class="edit-section">
          <el-input
            v-model="editingProblem.description"
            type="textarea"
            :rows="10"
            :placeholder="$t('problemInfo.description.placeholder')"
            class="edit-input"
          ></el-input>
          <div class="ai-assist">
            <el-input 
              v-model="aiRequirements.description" 
              :placeholder="$t('problemInfo.aiSuggestions')" 
              class="ai-input"
            ></el-input>
            <el-button 
              type="primary" 
              size="small" 
              @click="generateDescription"
              :loading="aiLoading.description"
            >{{ $t('problemInfo.aiGenerate') }}</el-button>
          </div>
        </div>
      </div>

      <!-- 本质剖析 -->
      <div class="info-section">
        <h3>{{ $t('problemInfo.essence.title') }}</h3>
        <div v-if="!editMode" class="content-display">
          <div class="sub-section">
            <h4>{{ $t('problemInfo.essence.researchPurpose') }}</h4>
            <MarkdownRenderer :content="currentProblem.essenceAnalysis?.researchPurpose || $t('problemInfo.notSet')" />
          </div>
          <div class="sub-section">
            <h4>{{ $t('problemInfo.essence.difficulties') }}</h4>
            <MarkdownRenderer :content="currentProblem.essenceAnalysis?.difficulties || $t('problemInfo.notSet')" />
          </div>
        </div>
        <div v-else class="edit-section">
          <div class="sub-edit">
            <div class="sub-label">{{ $t('problemInfo.essence.researchPurpose') }}：</div>
            <el-input
              v-model="editingProblem.essenceAnalysis.researchPurpose"
              type="textarea"
              :rows="10"
              :placeholder="$t('problemInfo.essence.researchPurposePlaceholder')"
              class="edit-input"
            ></el-input>
          </div>
          <div class="sub-edit">
            <div class="sub-label">{{ $t('problemInfo.essence.difficulties') }}：</div>
            <el-input
              v-model="editingProblem.essenceAnalysis.difficulties"
              type="textarea"
              :rows="10"
              :placeholder="$t('problemInfo.essence.difficultiesPlaceholder')"
              class="edit-input"
            ></el-input>
          </div>
          <div class="ai-assist">
            <el-input 
              v-model="aiRequirements.essenceAnalysis" 
              :placeholder="$t('problemInfo.aiSuggestions')" 
              class="ai-input"
            ></el-input>
            <el-button 
              type="primary" 
              size="small" 
              @click="generateEssenceAnalysis"
              :loading="aiLoading.essenceAnalysis"
            >{{ $t('problemInfo.aiGenerate') }}</el-button>
          </div>
        </div>
      </div>

      <!-- 反思与建议 -->
      <el-collapse class="reflection-section">
        <el-collapse-item :title="$t('problemInfo.reflection.title')" name="reflection">
          <div v-if="!editMode" class="content-display">
            <div class="sub-section">
              <h4>{{ $t('problemInfo.reflection.suggestions') }}</h4>
              <MarkdownRenderer :content="currentProblem.reflectionAndSuggestions?.subproblemsReflection || $t('problemInfo.notSet')" />
            </div>
            <div v-if="isRootProblem" class="sub-section">
              <h4>{{ $t('problemInfo.reflection.elevation') }}</h4>
              <MarkdownRenderer :content="currentProblem.reflectionAndSuggestions?.elevationDirection || $t('problemInfo.notSet')" />
            </div>
          </div>
          <div v-else class="edit-section">
            <div class="sub-edit">
              <div class="sub-label">{{ $t('problemInfo.reflection.suggestions') }}：</div>
              <el-input
                v-model="editingProblem.reflectionAndSuggestions.subproblemsReflection"
                type="textarea"
                :rows="10"
                :placeholder="$t('problemInfo.reflection.suggestionsPlaceholder')"
                class="edit-input"
              ></el-input>
            </div>
            <div v-if="isRootProblem" class="sub-edit">
              <div class="sub-label">{{ $t('problemInfo.reflection.elevation') }}：</div>
              <el-input
                v-model="editingProblem.reflectionAndSuggestions.elevationDirection"
                type="textarea"
                :rows="10"
                :placeholder="$t('problemInfo.reflection.elevationPlaceholder')"
                class="edit-input"
              ></el-input>
            </div>
            <div class="ai-assist">
              <el-input 
                v-model="aiRequirements.reflection" 
                :placeholder="$t('problemInfo.aiSuggestions')" 
                class="ai-input"
              ></el-input>
              <el-button 
                type="primary" 
                size="small" 
                @click="generateReflection"
                :loading="aiLoading.reflection"
              >{{ $t('problemInfo.aiGenerate') }}</el-button>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script>
import { Edit } from '@element-plus/icons-vue'
import axios from 'axios'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'

export default {
  name: 'ProblemInfo',
  components: {
    Edit,
    MarkdownRenderer
  },
  props: {
    currentProblemId: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      currentProblem: {
        viewName: '',
        description: '',
        essenceAnalysis: {
          researchPurpose: '',
          difficulties: ''
        },
        reflectionAndSuggestions: {
          subproblemsReflection: '',
          elevationDirection: ''
        }
      },
      editMode: false,
      isRootProblem: false,
      editingProblem: {
        id: '',
        description: '',
        essenceAnalysis: {
          researchPurpose: '',
          difficulties: ''
        },
        reflectionAndSuggestions: {
          subproblemsReflection: '',
          elevationDirection: ''
        }
      },
      aiRequirements: {
        description: '',
        essenceAnalysis: '',
        reflection: ''
      },
      aiLoading: {
        description: false,
        essenceAnalysis: false,
        reflection: false
      }
    }
  },
  watch: {
    currentProblemId: {
      immediate: true,
      handler(newId) {
        if (newId) {
          this.fetchProblemInfo(newId)
          this.editMode = false
        } else {
          this.resetProblemData()
        }
      }
    }
  },
  methods: {
    resetProblemData() {
      this.currentProblem = {
        viewName: '',
        description: '',
        essenceAnalysis: {
          researchPurpose: '',
          difficulties: ''
        },
        reflectionAndSuggestions: {
          subproblemsReflection: '',
          elevationDirection: ''
        }
      }
    },
    async fetchProblemInfo(problemId) {
      if (!problemId) return
      
      try {
        const res = await axios.get(`/api/research/problem/${problemId}`)
        if (res.data && res.data.success) {
          const problem = res.data.problem
          
          // 检查是否为根节点
          this.isRootProblem = !problem.parentId
          
          this.currentProblem = {
            viewName: problem.viewName || '',
            description: problem.description || '',
            essenceAnalysis: problem.essenceAnalysis || {
              researchPurpose: '',
              difficulties: ''
            },
            reflectionAndSuggestions: problem.reflectionAndSuggestions || {
              subproblemsReflection: '',
              elevationDirection: ''
            }
          }
        }
      } catch (error) {
        console.error(`获取问题信息失败: ${error.response?.data?.detail || error.message}`)
      }
    },
    enterEditMode() {
      this.editingProblem = {
        id: this.currentProblemId,
        description: this.currentProblem.description,
        essenceAnalysis: {
          researchPurpose: this.currentProblem.essenceAnalysis?.researchPurpose || '',
          difficulties: this.currentProblem.essenceAnalysis?.difficulties || ''
        },
        reflectionAndSuggestions: {
          subproblemsReflection: this.currentProblem.reflectionAndSuggestions?.subproblemsReflection || '',
          elevationDirection: this.currentProblem.reflectionAndSuggestions?.elevationDirection || ''
        }
      }
      this.aiRequirements = {
        description: '',
        essenceAnalysis: '',
        reflection: ''
      }
      this.editMode = true
    },
    cancelEdit() {
      this.editMode = false
    },
    async saveProblemInfo() {
      try {
        const response = await axios.post('/api/research/problem/update', {
          id: this.currentProblemId,
          description: this.editingProblem.description,
          essenceAnalysis: this.editingProblem.essenceAnalysis,
          reflectionAndSuggestions: this.editingProblem.reflectionAndSuggestions
        })
        
        if (response.data.success) {
          this.currentProblem = {
            ...this.currentProblem,
            description: this.editingProblem.description,
            essenceAnalysis: this.editingProblem.essenceAnalysis,
            reflectionAndSuggestions: this.editingProblem.reflectionAndSuggestions
          }
          this.$message.success('问题信息更新成功')
          this.editMode = false
          
          // 通知MindTree组件将节点从AI改为用户
          if (this.$root.$refs.mindTree) {
            this.$root.$refs.mindTree.convertAINodeToUserNode(this.currentProblemId)
          }
        } else {
          this.$message.error(response.data.error || '更新失败')
        }
      } catch (error) {
        this.$message.error(`更新失败: ${error.response?.data?.detail || error.message}`)
      }
    },
    async generateDescription() {
      if (!this.currentProblemId) return
      
      this.aiLoading.description = true
      try {
        const response = await axios.post(`/api/research/problem/${this.currentProblemId}/ai_update_description`, {
          requirement: this.aiRequirements.description
        })
        
        if (response.data.success) {
          this.editingProblem.description = response.data.description
          this.$message.success('AI生成描述成功')
        } else {
          this.$message.error(response.data.error || 'AI生成描述失败')
        }
      } catch (error) {
        this.$message.error(`AI生成描述失败: ${error.response?.data?.detail || error.message}`)
      } finally {
        this.aiLoading.description = false
      }
    },
    async generateEssenceAnalysis() {
      if (!this.currentProblemId) return
      
      this.aiLoading.essenceAnalysis = true
      try {
        const response = await axios.post(`/api/research/problem/${this.currentProblemId}/ai_update_essence_analysis`, {
          requirement: this.aiRequirements.essenceAnalysis
        })
        
        if (response.data.success) {
          this.editingProblem.essenceAnalysis = response.data.essenceAnalysis
          this.$message.success('AI生成本质剖析成功')
        } else {
          this.$message.error(response.data.error || 'AI生成本质剖析失败')
        }
      } catch (error) {
        this.$message.error(`AI生成本质剖析失败: ${error.response?.data?.detail || error.message}`)
      } finally {
        this.aiLoading.essenceAnalysis = false
      }
    },
    async generateReflection() {
      if (!this.currentProblemId) return
      
      this.aiLoading.reflection = true
      try {
        const response = await axios.post(`/api/research/problem/${this.currentProblemId}/ai_update_reflection`, {
          requirement: this.aiRequirements.reflection
        })
        
        if (response.data.success) {
          this.editingProblem.reflectionAndSuggestions = {
            ...this.editingProblem.reflectionAndSuggestions,
            ...response.data.reflectionAndSuggestions
          }
          this.$message.success('AI生成反思建议成功')
        } else {
          this.$message.error(response.data.error || 'AI生成反思建议失败')
        }
      } catch (error) {
        this.$message.error(`AI生成反思建议失败: ${error.response?.data?.detail || error.message}`)
      } finally {
        this.aiLoading.reflection = false
      }
    }
  }
}
</script>

<style scoped>
.problem-info-container {
  height: 100%;
  overflow-y: auto;
  padding: 16px;
}

.problem-info {
  background: #ffffff;
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s;
}

.edit-mode {
  background: #f5f7fa;
}

.problem-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e8e8e8;
}

.problem-header h2 {
  margin: 0;
  color: #303133;
  font-size: 24px;
}

.problem-actions {
  display: flex;
  gap: 8px;
}

.info-section {
  margin-bottom: 32px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.info-section h3 {
  color: #409EFF;
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 18px;
  border-bottom: 2px solid #409EFF;
  padding-bottom: 8px;
}

.sub-section {
  margin-bottom: 20px;
}

.sub-section h4 {
  color: #606266;
  margin-bottom: 12px;
  font-size: 16px;
}

.content-display {
  padding: 12px;
  background: #ffffff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.edit-section {
  margin-top: 16px;
}

.sub-edit {
  margin-bottom: 16px;
}

.sub-label {
  font-weight: 600;
  margin-bottom: 8px;
  color: #606266;
}

.edit-input {
  margin-bottom: 12px;
}

.ai-assist {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.ai-input {
  flex: 1;
}

.reflection-section {
  margin-top: 32px;
  border: none;
  background: #f0f2f5;
  border-radius: 6px;
}

:deep(.el-collapse-item__header) {
  font-size: 18px;
  color: #409EFF;
  background: transparent;
  border-bottom: none;
  padding: 16px;
}

:deep(.el-collapse-item__content) {
  padding: 16px;
  background: #ffffff;
  border-radius: 0 0 6px 6px;
}
</style> 
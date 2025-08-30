<template>
  <div class="user-profile-container">
    <!-- 标题栏 -->
    <div class="header">
      <span class="title">{{ $t('userProfile.title') }}</span>
      <div class="header-actions">
        <el-tooltip :content="$t('userProfile.aiUpdate')" placement="top">
          <el-button 
            type="primary" 
            size="small"
            :disabled="isUpdating"
            class="ai-button"
            @click="requestAiUpdate"
          >
            <el-icon><MagicStick /></el-icon>
          </el-button>
        </el-tooltip>
        <el-icon 
          class="action-icon"
          @click.stop="toggleProfile"
        >
          <ArrowDown v-if="showProfile"/>
          <ArrowUp v-else/>
        </el-icon>
      </div>
    </div>

    <el-collapse-transition>
      <div 
        v-show="showProfile" 
        class="content-wrapper"
      >
        <div v-if="!isEditing" class="display-mode">
          <div class="action-buttons">
            <el-button type="primary" size="small" @click="startEditing">
              <el-icon><Edit /></el-icon>
            </el-button>
          </div>
          <div class="profile-content">
            <MarkdownRenderer :content="userProfile || $t('userProfile.noProfile')" />
          </div>
        </div>
        <div v-else class="edit-mode">
          <div class="action-buttons">
            <el-button type="success" size="small" @click="saveProfile">
              {{ $t('userProfile.save') }}
            </el-button>
            <el-button size="small" @click="cancelEditing">
              {{ $t('userProfile.cancel') }}
            </el-button>
          </div>
          <el-input
            v-model="editingProfile"
            type="textarea"
            :rows="10"
            :placeholder="$t('userProfile.placeholder')"
            class="profile-editor"
          ></el-input>
        </div>
      </div>
    </el-collapse-transition>
  </div>
</template>

<script>
import { ArrowUp, ArrowDown, Edit, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import axios from 'axios'

export default {
  name: 'UserProfile',
  components: {
    ArrowUp,
    ArrowDown,
    Edit,
    MagicStick,
    MarkdownRenderer
  },
  data() {
    return {
      showProfile: true,
      isEditing: false,
      isUpdating: false,
      userProfile: '',
      editingProfile: '',
    }
  },
  mounted() {
    this.fetchUserProfile()
  },
  methods: {
    async fetchUserProfile() {
      try {
        const res = await axios.get('/api/research/user_profile')
        if (res.data.success) {
          this.userProfile = res.data.userProfile
        }
      } catch (error) {
        ElMessage.error(this.$t('userProfile.errors.fetchFailed') + (error.response?.data?.detail || error.message))
      }
    },
    toggleProfile() {
      this.showProfile = !this.showProfile
    },
    startEditing() {
      this.editingProfile = this.userProfile
      this.isEditing = true
    },
    cancelEditing() {
      this.isEditing = false
      this.editingProfile = ''
    },
    async saveProfile() {
      try {
        const res = await axios.post('/api/research/user_profile/update', {
          userProfile: this.editingProfile
        })
        
        if (res.data.success) {
          this.userProfile = res.data.userProfile
          this.isEditing = false
          ElMessage.success(this.$t('userProfile.messages.updateSuccess'))
        }
      } catch (error) {
        ElMessage.error(this.$t('userProfile.errors.updateFailed') + (error.response?.data?.detail || error.message))
      }
    },
    async requestAiUpdate() {
      this.isUpdating = true
      
      try {
        const res = await axios.post('/api/research/user_profile/ai_update')
        
        if (res.data.success) {
          this.userProfile = res.data.userProfile
          ElMessage.success(this.$t('userProfile.messages.aiUpdateSuccess'))
        }
      } catch (error) {
        ElMessage.error(this.$t('userProfile.errors.aiUpdateFailed') + (error.response?.data?.detail || error.message))
      } finally {
        this.isUpdating = false
      }
    }
  }
}
</script>

<style scoped>
.user-profile-container {
  width: 100%;
  margin-bottom: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.content-wrapper {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-top: 10px;
  padding: 16px;
  max-height: 70vh;
  overflow-y: auto;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
  gap: 8px;
}

.profile-content {
  background-color: #fff;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.profile-editor {
  margin-top: 10px;
}

.ai-button {
  background-color: #8e44ad;
  border-color: #8e44ad;
}

.ai-button:hover {
  background-color: #9b59b6;
  border-color: #9b59b6;
}

.action-icon {
  cursor: pointer;
  font-size: 20px;
  color: #606266;
}

.action-icon:hover {
  color: #409eff;
}
</style> 
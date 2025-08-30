<template>
  <div class="app-container">
    <AppHeader />
    <div class="main-container">
      <!-- 左侧组 -->
      <div class="group-container left-group">
        <el-tabs type="border-card" class="group-tabs">
          <el-tab-pane :lazy="true">
            <template #label>
              <span class="custom-tabs-label">
                <el-icon><Guide /></el-icon>
                <span>{{ $t('app.tabs.problemTree') }}</span>
              </span>
            </template>
            <div class="original-left">
              <div class="mind-tree-container">
                <MindTree 
                  ref="mindTree" 
                  @update-focus-problem="handleFocusProblemChange" 
                />
              </div>
              <UserProfile 
                ref="userProfile"
              />
            </div>
          </el-tab-pane>
          <el-tab-pane :lazy="false">
            <template #label>
              <span class="custom-tabs-label">
                <el-icon><Reading /></el-icon>
                <span>{{ $t('app.tabs.literatureVisualization') }}</span>
              </span>
            </template>
            <div class="original-middle">
              <ChartList 
                :active-category="activeCategory"
                :chart-loading="chartLoading" 
              />
              <PaperList
                :active-category="activeCategory"
              />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 折叠/展开按钮 -->
      <div 
        class="collapse-toggle" 
        :class="{ collapsed: isRightCollapsed }" 
        @click="toggleRightSidebar"
        @mouseover="isHovering = true"
        @mouseleave="isHovering = false"
      >
        <el-icon v-if="isRightCollapsed" class="arrow-icon"><ArrowLeft /></el-icon>
        <el-icon v-else class="arrow-icon"><ArrowRight /></el-icon>
      </div>

      <!-- 右侧组 -->
      <div v-show="!isRightCollapsed" class="group-container right-group">
        <el-tabs type="border-card" class="group-tabs">
          <el-tab-pane :lazy="true">
            <template #label>
              <span class="custom-tabs-label">
                <el-icon><ChatDotSquare /></el-icon>
                <span>{{ $t('app.tabs.aiGuide') }}</span>
              </span>
            </template>
            <div class="original-left2">
              <ChatBox 
                ref="chatBox"
                :current-focus-problem="currentFocusProblem"
                @handle-command="handleChatCommand"
              />
            </div>
          </el-tab-pane>
          <el-tab-pane :lazy="true">
            <template #label>
              <span class="custom-tabs-label">
                <el-icon><Search /></el-icon>
                <span>{{ $t('app.tabs.intelligentSearch') }}</span>
              </span>
            </template>
            <div class="original-right">
              <CategoryList 
                ref="categoryList" 
                :current-problem-id="currentFocusProblem"
                @update-active-category="updateActiveCategory" 
              />
            </div>
          </el-tab-pane>
          <el-tab-pane :lazy="true">
            <template #label>
              <span class="custom-tabs-label">
                <el-icon><Opportunity /></el-icon>
                <span>{{ $t('app.tabs.thinkingAwareness') }}</span>
              </span>
            </template>
            <div class="original-right">
              <ProblemInfo 
                ref="problemInfo"
                :current-problem-id="currentFocusProblem"
              />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script>
import { Guide, Reading, ChatDotSquare, Search, ArrowLeft, ArrowRight, Opportunity } from '@element-plus/icons-vue'
import ChatBox from "@/App/ChatBox.vue";
import AppHeader from "@/App/AppHeader.vue";
import ChartList from "@/App/ChartList.vue";
import CategoryList from "@/App/CategoryList.vue";
import PaperList from "@/App/PaperList.vue";
import MindTree from "@/App/MindTree.vue";
import UserProfile from "@/App/UserProfile.vue";
import ProblemInfo from "@/App/ProblemInfo.vue";

export default {
  components: {
    AppHeader,
    ChatBox,
    ChartList,
    CategoryList,
    PaperList,
    MindTree,
    UserProfile,
    ProblemInfo,
    Guide,
    Reading,
    ChatDotSquare,
    Search,
    ArrowLeft,
    ArrowRight,
    Opportunity
  },
  data() {
    return {
      activeCategory: null,
      currentFocusProblem: null,
      chartLoading: false,
      isRightCollapsed: false,
      isHovering: false
    };
  },
  methods: {
    toggleRightSidebar() {
      this.isRightCollapsed = !this.isRightCollapsed;
    },
    updateActiveCategory(activeCategory) {
      this.activeCategory = activeCategory;
    },
    handleChatCommand(command, args) {
      if (command === 'update_categories') {
        if (this.$refs.categoryList) {
          this.$refs.categoryList.refreshProblemData(this.currentFocusProblem);
        } else {
          console.log('CategoryList组件未渲染，无法刷新问题数据');
        }
      } else if (command === 'add_node') {
        if (this.$refs.mindTree && args && args.length > 0) {
          for (let nodeData of args) {
            console.log('正在添加节点：', nodeData)
            this.$refs.mindTree.handleAddNodeCommand(nodeData);
          }
        }
      } else if (command === 'update_user_profile') {
        if (this.$refs.userProfile) {
          this.$refs.userProfile.userProfile = args;
        } else {
          console.log('UserProfile组件未渲染，无法更新用户画像');
        }
      }
    },
    handleFocusProblemChange(problemId) {
      // 不管ID是否相同，都强制刷新问题信息
      this.currentFocusProblem = problemId;
      
      // 更新范畴列表为当前问题的范畴
      if (this.$refs.categoryList) {
        // 强制刷新问题信息，即使ID相同
        this.$refs.categoryList.refreshProblemData(problemId);
      }
      
      // 更新问题信息
      if (this.$refs.problemInfo) {
        this.$refs.problemInfo.fetchProblemInfo(problemId);
      }
    }
  },
};
</script>

<style>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.main-container {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
  gap: 0;
}

.group-container {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.left-group {
  flex: 2;
  min-width: 0;
}

.right-group {
  flex: 1;
  min-width: 0;
}

.group-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.group-tabs > .el-tabs__content {
  flex: 1;
  overflow: hidden;
  padding: 0 !important;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.group-tabs .el-tab-pane {
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

/* 保持原有容器样式 */
.original-left,
.original-middle,
.original-left2,
.original-right {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  padding: 10px;
  border: 10px solid #f7f7f7;
  background-color: #f9f9f9;
}

.mind-tree-container {
  flex: 1;
  min-height: 0;
  height: 100%;
}

.original-left,
.original-middle {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  min-height: 0;
}

.custom-tabs-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.el-tabs__item {
  padding: 0 16px !important;
}

/* 折叠/展开按钮 */
.collapse-toggle {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 80px;
  background-color: #909399;
  border-radius: 4px 0 0 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.collapse-toggle:hover {
  background-color: #a6a9ad;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* 展开状态：按钮右侧与右侧组左侧对齐 */
.collapse-toggle:not(.collapsed) {
  right: 33.3333%;
}

/* 折叠状态：按钮右侧与页面右侧对齐 */
.collapse-toggle.collapsed {
  right: 0;
}

.collapse-toggle span {
  font-size: 16px;
  color: #606266;
}


.arrow-icon {
  color: #ffffff;
  font-size: 16px;
  transition: transform 0.3s ease;
}

.collapse-toggle:hover .arrow-icon {
  transform: scale(1.2);
}
</style>

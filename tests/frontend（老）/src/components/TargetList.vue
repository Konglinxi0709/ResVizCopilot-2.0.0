<template>
  <div 
    class="target-list"
    :class="{ 'edit-mode': editMode }"
  >
    <!-- 模式选择区域 -->
    <div class="target-list-title">
      {{$t('targetList.title')}}:
    </div>
    <div class="mode-section">
      <template v-if="editMode">
        <el-radio-group v-model="tempCalculateMode">
          <el-radio-button :label="CALCULATE_MODE.MAX">{{$t("targetList.MAX")}}</el-radio-button>
          <el-radio-button :label="CALCULATE_MODE.MIN">{{$t("targetList.MIN")}}</el-radio-button>
          <el-radio-button :label="CALCULATE_MODE.AVG">{{$t("targetList.AVG")}}</el-radio-button>
        </el-radio-group>
      </template>
      <div v-else class="mode-display">
        {{$t("targetList.calculateMode")}}: {{ calculateModeLabel }}
      </div>
    </div>

    <!-- Target列表 -->
    <div class="target-items">
      <div 
        v-for="target in currentTargets" 
        :key="target.id"
        class="target-item"
      >
        <!-- 普通模式显示 -->
        <template v-if="!editMode">
          <div class="content">{{ target.content }}</div>
          <div 
            v-if="calculateMode === CALCULATE_MODE.AVG"
            class="weight"
          >
            {{$t("targetList.weight")}}: {{ target.weight.toFixed(2) }}
          </div>
        </template>

        <!-- 编辑模式显示 -->
        <template v-else>
          <el-input
            v-model="target.content"
            :placeholder="$t('targetList.weight')"
            class="edit-content"
          />
          <el-input-number
            v-if="tempCalculateMode === CALCULATE_MODE.AVG"
            v-model="target.weight"
            :precision="2"
            :step="0.1"
            :max="1"
            :min="-1"
            class="edit-weight"
          />
          <el-tooltip :content="$t('targetList.delete')" placement="top">
            <el-button
              size="small"
              circle
              @click.stop="deleteTarget(target.id)"
              icon="Delete"
              type="danger"
              plain
            />
          </el-tooltip>
        </template>
      </div>
    </div>

    <!-- 添加按钮 -->
    <div v-if="editMode" class="add-section">
      <el-button type="primary" @click="addTarget">{{ $t('targetList.addTarget') }}</el-button>
    </div>

    <!-- 操作按钮 -->
    <div class="action-section">
      <el-button v-if="!editMode" type="primary" @click="enterEditMode">
        {{ $t('targetList.edit') }}
      </el-button>
      <template v-else>
        <el-button @click="cancelEdit">{{ $t('targetList.cancel') }}</el-button>
        <el-button type="primary" @click="submitEdit">{{ $t('targetList.submit') }}</el-button>
      </template>
    </div>
  </div>
</template>

<script scope>
export default {
  name: 'TargetList',
  props: {
    targetList: {
      type: Object,
      required: true
    },
  },
  data() {
    return {
      tempTargets: [],
      tempCalculateMode: 'max',
      editMode: false,
      CALCULATE_MODE: {
        MAX: 'max',
        MIN: 'min',
        AVG: 'avg'
      }
    }
  },
  computed: {
    currentTargets() {
      return this.editMode ? this.tempTargets : this.targetList.targets
    },
    calculateModeLabel() {
      return {
        [this.CALCULATE_MODE.MAX]: this.$t("targetList.MAX"),
        [this.CALCULATE_MODE.MIN]: this.$t("targetList.MIN"),
        [this.CALCULATE_MODE.AVG]: this.$t("targetList.AVG")
      }[this.tempCalculateMode]
    }
  },
  methods: {
    enterEditMode() {
      this.tempTargets = this.targetList.targets.map((item, index) => {
        return {
          ...item,
          id: index
        };
      });
      this.tempCalculateMode = this.targetList.sim_mode
      this.editMode = true
    },
    cancelEdit() {
      this.editMode = false
    },
    submitEdit() {
      const payload = this.submitData()
      this.$emit('submit-target-list', payload)
      this.editMode = false
    },
    addTarget() {
      this.tempTargets.push({
        id: Date.now(),
        content: '',
        weight: 1.0
      })
    },
    deleteTarget(id) {
      this.tempTargets = this.tempTargets.filter(t => t.id !== id)
    },
    submitData() {
      const payload = {
        sim_mode: this.tempCalculateMode,
        targets: this.tempTargets.map(t => ({
          content: t.content,
          weight: t.weight
        }))
      }
      return payload
    }
  }
}
</script>

<style scoped>
.target-list {
  max-width: 800px;
  margin: 10px auto;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #eee;
}
.edit-mode {
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
  border: 0px;
}
.target-list-title {
  font-size: 15px;
  font-weight: bold;
}

.mode-section {
  margin-bottom: 20px;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.mode-display {
  color: #666;
  font-size: 14px;
}

.target-items {
  margin: 15px 0;
}

.target-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  margin: 8px 0;
  border-radius: 4px;
  transition: background 0.3s;
}

.target-item:hover {
  background: #f5f7fa;
}

.content {
  flex: 1;
  color: #303133;
}

.weight {
  color: #909399;
  font-size: 0.9em;
  min-width: 80px;
}

.edit-content {
  flex: 1;
}

.edit-weight {
  width: 120px;
}

.add-section {
  margin-top: 15px;
}

.action-section {
  margin-top: 20px;
  text-align: right;
}
</style>
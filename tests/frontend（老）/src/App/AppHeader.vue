<template>
  <el-header class="header">
    <div class="left-section">
      <!-- img alt="校徽" src="../assets/logo.png" class="logo_cuc" -->
      <span class="title">{{ $t('app.title') }}</span>
      <!-- 版本选择 -->
      <el-select
        v-model="selectedVersion"
        filterable
        :placeholder="$t('app.version.select')"
        style="width: 240px; margin-left: 20px;"
      >
        <el-option
          v-for="ver in versions"
          :key="ver.id"
          :label="`${ver.timestamp} ${ver.name}`"
          :value="ver.id"
        />
      </el-select>
      <el-button
        type="primary"
        :disabled="!selectedVersion"
        @click="loadVersion"
        size="small"
        style="margin-left: 8px;"
      >{{ $t('app.version.load') }}</el-button>
      <el-button
        type="primary"
        @click="createNewResearch"
        size="small"
        style="margin-left: 8px;"
      >{{ $t('app.version.new') }}</el-button>
      <el-button
        type="primary"
        :disabled="!currentFile.loaded"
        @click="saveCurrentVersion"
        size="small"
        style="margin-left: 8px;"
      >{{ $t('app.version.save') }}</el-button>
      <el-button
        type="primary"
        @click="promptSave"
        size="small"
        style="margin-left: 8px;"
      >{{ $t('app.version.saveAs') }}</el-button>
      <!-- 当前文件信息 -->
      <div class="current-file-info">
        <span class="file-name" :class="{'placeholder': !currentFile.loaded}">
          {{ currentFile.loaded ? currentFile.name : $t('app.version.newArchive') }}
        </span>
        <span class="save-time" :class="{'unsaved': !currentFile.last_save_time}">
          {{ currentFile.last_save_time ? $t('app.version.lastSaved') + formatTime(currentFile.last_save_time) : $t('app.version.unsaved') }}
        </span>
      </div>
    </div>
    <div class="right-section">
      <input type="file" ref="fileInput" webkitdirectory directory multiple @change="handleFiles" style="display: none;"/>
      <el-select v-model="currentLocale" style="margin-right: 10px; width: 100px;">
        <el-option label="中文" value="zh" />
        <el-option label="English" value="en" />
      </el-select>
      <el-button @click="refreshPage" class="refresh-button">{{ $t('app.buttons.refresh') }}</el-button>
      <!-- <div v-if="templatesNum > 0">已加载模板个数: {{ templatesNum }}</div> -->
    </div>
  </el-header>
</template>

<script>
import {idbKeyval} from "@/agents/db";
import axios from 'axios'
import { useI18n } from 'vue-i18n'

export default {
  name: 'AppHeader',
  setup() {
    const i18n = useI18n()
    return { i18n }
  },
  data() {
    return {
      templatesNum: 0,
      versions: [],
      selectedVersion: '',
      saveName: '',
      currentLocale: 'zh',
      currentFile: {
        loaded: false,
        filename: null,
        timestamp: null,
        name: null,
        last_save_time: null
      }
    };
  },
  watch: {
    currentLocale(val) {
      this.i18n.locale.value = val
    }
  },
  async created() {
    try {
      const templates = await idbKeyval.get('templates');
      this.templatesNum = templates ? templates.length : 0;
    } catch (error) {
      console.error('Error loading templates:', error);
      this.templatesNum = 0;
    }
    await this.fetchVersions();
    await this.fetchCurrentFileInfo();
  },
  methods: {
    formatTime(timeStr) {
      // 格式化时间戳为更友好的格式
      if (!timeStr) return '';
      const parts = timeStr.split('_');
      if (parts.length === 2) {
        const date = parts[0];
        const time = parts[1];
        return `${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)} ${time.slice(0, 2)}:${time.slice(2, 4)}:${time.slice(4, 6)}`;
      }
      return timeStr;
    },
    importTemplate() {
      this.$refs.fileInput.click(); // 触发隐藏的文件输入框
    },
    async handleFiles(event) {
      if (event){
        return;
      }
    },
    uploadJson() {
      console.log('上传JSON');
    },
    async fetchVersions() {
      const res = await axios.get('/api/persistence/versions');
      this.versions = res.data;
    },
    async fetchCurrentFileInfo() {
      try {
        const res = await axios.get('/api/persistence/current');
        this.currentFile = res.data;
        console.log("获取当前文件信息:", this.currentFile);
      } catch (e) {
        console.error('获取当前文件信息失败:', e);
      }
    },
    async loadVersion() {
      try {
        await axios.post('/api/persistence/load', { 
          version_id: this.selectedVersion,
          auto_save: true
        });
        this.$message.success(this.$t('app.messages.loadSuccess'));
        window.location.reload();
      } catch (e) {
        this.$message.error(this.$t('app.messages.loadFailed') + (e.response?.data?.detail || e.message));
      }
    },
    async createNewResearch() {
      try {
        await axios.post('/api/persistence/new');
        this.$message.success(this.$t('app.messages.createSuccess'));
        window.location.reload();
      } catch (e) {
        this.$message.error(this.$t('app.messages.createFailed') + (e.response?.data?.detail || e.message));
      }
    },
    promptSave() {
      this.$prompt(this.$t('app.messages.saveAsPrompt'), this.$t('app.messages.saveAsTitle'), {
        inputValue: this.currentFile.loaded ? this.currentFile.name : '',
        inputPlaceholder: this.$t('app.messages.saveAsPlaceholder'),
        confirmButtonText: this.$t('app.messages.confirm'),
        cancelButtonText: this.$t('app.messages.cancel')
      }).then(({ value }) => {
        const name = value.trim() || this.$t('app.messages.unnamed');
        this.saveVersion(name);
      }).catch(()=>{});
    },
    async saveVersion(name) {
      try {
        const res = await axios.post('/api/persistence/save', { name });
        this.$message.success(this.$t('app.messages.saveAsSuccess') + res.data.version);
        await this.fetchVersions();
        await this.fetchCurrentFileInfo();
      } catch (e) {
        this.$message.error(this.$t('app.messages.saveFailed') + (e.response?.data?.detail || e.message));
      }
    },
    async saveCurrentVersion() {
      try {
        const res = await axios.post('/api/persistence/save_current');
        this.$message.success(this.$t('app.messages.saveSuccess') + res.data.version);
        await this.fetchVersions();
        await this.fetchCurrentFileInfo();
      } catch (e) {
        this.$message.error(this.$t('app.messages.saveFailed') + (e.response?.data?.detail || e.message));
      }
    },
    refreshPage() {
      window.location.reload();
    }
  }
}
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background-color: #f0f0f0;
  border-bottom: 1px solid #ccc;
}

.left-section {
  margin-left: 5px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.logo_cuc {
  width: 40px;
  height: 40px;
  margin-right: 10px;
}

.title {
  font-size: 22px;
  font-weight: bold;
  letter-spacing: 1px; /* 增加字间距 */
}

.right-section {
  display: flex;
  align-items: center;
}

.upload-button {
  margin-right: 10px;
}

.refresh-button {
  margin-right: 20px;
}

.current-file-info {
  margin-left: 16px;
  display: flex;
  flex-direction: column;
  font-size: 13px;
}

.file-name {
  font-weight: bold;
}

.file-name.placeholder {
  color: #aaa;
  font-style: italic;
}

.save-time {
  font-size: 12px;
  color: #666;
}

.save-time.unsaved {
  color: #f56c6c;
  font-weight: bold;
}
</style>

import {createApp} from 'vue'
import App from './App/App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
import './style.css'
import {idbKeyval} from './agents/db';
import sourceData from './agents/data/source.json';
import templates from './agents/data/template.json';
import dataDescription from './agents/data/description.json';
import visualVocabulary from './agents/data/visualVocabulary.json';
import visualExamples from './agents/data/examples.json';
import i18n from './i18n'

async function clearDatabase() {
  await idbKeyval.clear();
  console.log('IndexedDB 数据库已清空');
  
  // 初始化数据存储
  await Promise.all([
    idbKeyval.set('sourceData', sourceData),
    idbKeyval.set('dataDescription', dataDescription),
    idbKeyval.set('visualVocabulary', visualVocabulary),
    idbKeyval.set('visualExamples', visualExamples),
    idbKeyval.set('templates', templates),
    idbKeyval.set('initGrid', true)
  ]);
}


clearDatabase().then(() => {
  const app = createApp(App)
    .use(ElementPlus)
    .use(i18n)

  // 注册图标组件
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
  }

  app.mount('#app');
});
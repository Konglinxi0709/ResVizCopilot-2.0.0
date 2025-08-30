import { createI18n } from 'vue-i18n'

const messages = {
  en: {
    app: {
      title: 'ResVizCopilot',
      version: {
        select: 'Select Version',
        load: 'Load',
        new: 'New',
        save: 'Save',
        saveAs: 'Save As',
        newArchive: 'New Archive',
        lastSaved: 'Last Saved: ',
        unsaved: 'Unsaved'
      },
      tabs: {
        problemTree: 'Problem Tree',
        literatureVisualization: 'Literature Visualization',
        aiGuide: 'AI Guide',
        intelligentSearch: 'Intelligent Search',
        thinkingAwareness: 'Thinking Awareness'
      },
      buttons: {
        refresh: 'Refresh Interface'
      },
      messages: {
        loadSuccess: "Loaded successfully, the page will refresh",
        loadFailed: "Load failed: ",
        createSuccess: "New research created, the page will refresh",
        createFailed: "Creation failed: ",
        saveAsPrompt: "Enter save name",
        saveAsTitle: "Save as new version",
        saveAsPlaceholder: "Name (leave blank for Untitled)",
        confirm: "Confirm",
        cancel: "Cancel",
        unnamed: "Untitled",
        saveAsSuccess: "Save as successful: ",
        saveSuccess: "Save successful: ",
        saveFailed: "Save failed: "
      }
    },
    chatInput: {
      placeholder: 'Type your question here...',
      uploadIcon: 'Upload Icon'
    },
    chatMessage: {
      avatar: 'Avatar',
      processing: 'Processing {role}'
    },
    chatBox: {
      selectMode: 'Select work mode',
      currentProblem: 'Current problem',
      autoCreateCategory: 'Automatically create literature search categories (this will take a long time)',
      presetQuestions: {
        question1: 'I want to implement an AI research assistant system based on large language models to help researchers organize ideas, inspire thinking, and retrieve literature at various stages of scientific exploration',
        question2: 'I want to utilize large language models to implement a tool that automatically programs and performs visual bibliometric analysis in a literature field',
        question3: 'I want to use image enhancement to improve the detection capability of aerial targets in complex backgrounds',
        question4: 'I want to use AI technology to analyze badminton matches, summarize the playing strategies of high-level athletes, and generate shot path analysis and tactical guidance'
      },
      modes: {
        'newProblem': 'New problem mode',
        'exploration': 'Exploration guide mode',
        'chat': 'Normal chat mode'
      }
    },
    mindTree: {
      errors: {
        exportFailed: 'Failed to export screenshot, please try again'
      },
      confirm: {
        select: 'Do you want to select this node as the current focus problem?',
        unselect: 'Do you want to unselect this node as the current focus problem?',
        yes: 'Yes',
        no: 'No',
        yesUnselect: 'Yes, unselect',
        noKeepSelected: 'No, keep selected'
      }
    },
    userProfile: {
      title: "User Profile",
      aiUpdate: "AI Update",
      noProfile: "No profile available",
      save: "Save",
      cancel: "Cancel",
      placeholder: "Enter user profile",
      errors: {
        fetchFailed: "Failed to fetch user profile: ",
        updateFailed: "Failed to update user profile: ",
        aiUpdateFailed: "Failed to update user profile with AI: "
      },
      messages: {
        updateSuccess: "User profile updated successfully",
        aiUpdateSuccess: "User profile updated by AI successfully"
      }
    },
    problemInfo: {
      empty: 'Please select a problem from the research problem tree first',
      edit: 'Edit Problem',
      cancel: 'Cancel',
      save: 'Save',
      notSet: 'Not set',
      aiSuggestions: 'Enter modification suggestions (optional)',
      aiGenerate: 'AI Generate',
      description: {
        title: 'Problem Description',
        placeholder: 'Please enter problem description'
      },
      essence: {
        title: 'Essence Analysis',
        researchPurpose: 'Research Purpose',
        difficulties: 'Key Points',
        researchPurposePlaceholder: 'Please enter research purpose',
        difficultiesPlaceholder: 'Please enter key points'
      },
      reflection: {
        title: 'Reflection',
        suggestions: 'Reflection and Suggestions',
        elevation: 'Thinking Expansion and Elevation',
        suggestionsPlaceholder: 'Please enter reflection and suggestions',
        elevationPlaceholder: 'Please enter thinking expansion and elevation'
      }
    },
    paperList: {
      title: 'Paper Overview',
      showInvalid: 'Show Invalid Papers',
      hideInvalid: 'Hide Invalid Papers',
      analyzing: 'Analyzing...',
      noAnalysis: 'No Value Analysis',
      loadMore: 'Load More',
      loading: 'Loading...',
      noMore: 'No More Data',
      columns: {
        order: 'Order',
        literature: 'Literature Info',
        abstract: 'Abstract',
        aiAnalysis: 'AI Value Analysis',
        aiUsability: 'AI Usability',
        similarity: 'Similarity Score',
        publication: 'Publication',
        citations: 'Citations / FWCI',
        number: 'No.'
      }
    },
    categoryList: {
      currentProblem: 'Current Problem: {name}',
      createCategory: 'Create Category',
      selectProblem: 'Please select a problem from the research problem tree first',
      noCategories: 'No categories under this problem. Please add a new category or let AI assistant help create one',
      creating: 'Creating category, please wait...',
      placeholder: 'Enter retrieval requirements',
      messages: {
        createSuccess: 'Category created successfully',
        createFailed: 'Failed to create category',
        createError: 'Failed to create category: {error}'
      }
    },
    categoryItem: {
        download: "Download Data",
        copyId: "Copy Identifier",
        rename: "Rename",
        delete: "Delete",
        searchExpression: "Search Expression",
        save: "Save",
        cancel: "Cancel",
        noExpression: "No search expression set",
        expressionPlaceholder: "Enter search expression",
        aiModify: "AI Modify Search Expression",
        modify: "Modify",
        designReason: "Design Reason",
        metadata: "Category Metadata",
        modifyPlaceholder: "Enter modification request",
        nodeId: "Node ID",
        documentCnt: "Total Documents",
        downloadProgress: "Download Progress",
        modifying: "Modifying, please wait...",
        messages: {
            copySuccess: "Identifier copied",
            copyFailed: "Copy failed, please copy manually",
            copySuccessUnsecure: "Identifier copied (current server unauthenticated)",
            emptyExpression: "Search expression cannot be empty",
            expressionUpdateSuccess: "Search expression updated successfully",
            expressionUpdateFailed: "Update failed",
            emptyModifyRequirement: "Please enter modification request",
            modifySuccess: "AI modification successful, please review and save",
            modifyFailed: "AI modification failed",
        }
    },
    targetList: {
        title: "Literature Relevance Ranking",
        calculateMode: "Current Similarity Calculation Mode",
        MAX: "Maximum",
        MIN: "Minimum",
        AVG: "Average",
        weight: "Weight",
        placeholder: "Enter target content",
        delete: "Delete",
        addTarget: "Add Target",
        edit: "Edit",
        cancel: "Cancel",
        submit: "Submit",
    }
  },
  zh: {
    app: {
      title: 'AI可视化科研探索向导',
      version: {
        select: '选择版本',
        load: '加载',
        new: '新建',
        save: '保存',
        saveAs: '另存为',
        newArchive: '新存档',
        lastSaved: '最后保存: ',
        unsaved: '未保存'
      },
      tabs: {
        problemTree: '问题树',
        literatureVisualization: '文献可视化阅读',
        aiGuide: 'AI向导',
        intelligentSearch: '智能检索',
        thinkingAwareness: '思维意识'
      },
      buttons: {
        refresh: '刷新界面'
      },
      messages: {
        loadSuccess: '加载成功，页面将刷新',
        loadFailed: '加载失败: ',
        createSuccess: '已创建新的研究，页面将刷新',
        createFailed: '创建失败: ',
        saveAsPrompt: '请输入保存名称',
        saveAsTitle: '另存为新版本',
        saveAsPlaceholder: '名称(留空为未命名)',
        confirm: '确定',
        cancel: '取消',
        unnamed: '未命名',
        saveAsSuccess: '另存为成功: ',
        saveSuccess: '保存成功: ',
        saveFailed: '保存失败: ',
      }
    },
    chatInput: {
      placeholder: '输入您的问题...',
      uploadIcon: '上传图标'
    },
    chatMessage: {
      avatar: '头像',
      processing: '正在进行{role}'
    },
    chatBox: {
      selectMode: '选择工作模式',
      currentProblem: '当前问题',
      autoCreateCategory: '自动创建文献检索范畴（会耗费较长时间）',
      presetQuestions: {
        question1: '我想基于大语言模型实现一个AI科研向导系统，帮助研究人员在科研探索的各个阶段梳理思路、启发思考以及检索文献资料',
        question2: '我想利用大语言模型实现一个自动进行编程，对一个文献领域进行可视化计量分析的工具',
        question3: '我想用图像增强提高复杂背景下空中目标的检测能力',
        question4: '我想利用AI技术进行羽毛球比赛分析，总结高水平运动员的打法策略，生成球路分析和战术指导'
      },
      modes: {
        'newProblem': '新问题模式',
        'exploration': '探索向导模式',
        'chat': '普通聊天模式',
      }
    },
    mindTree: {
      errors: {
        exportFailed: '导出截图失败，请重试'
      },
      confirm: {
        select: '是否选中该节点作为当前聚焦问题？',
        unselect: '是否取消选中该节点作为当前聚焦问题？',
        yes: '是',
        no: '否',
        yesUnselect: '是，取消选中',
        noKeepSelected: '否，保持选中'
      }
    },
    userProfile: {
        title: '用户画像',
        aiUpdate: 'AI更新',
        noProfile: '暂无用户画像',
        save: '保存',
        cancel: '取消',
        placeholder: '请输入用户画像',
        errors: {
            fetchFailed: '获取用户画像失败: ',
            updateFailed: '更新用户画像失败: ',
            aiUpdateFailed: 'AI更新用户画像失败: ',

        },
        messages: {
            updateSuccess: '用户画像更新成功',
            aiUpdateSuccess: 'AI更新用户画像成功'
        }
    },
    problemInfo: {
      empty: '请先在研究问题树中选择一个问题',
      edit: '编辑问题',
      cancel: '取消',
      save: '保存',
      notSet: '未设置',
      aiSuggestions: '输入修改建议（可选）',
      aiGenerate: 'AI生成',
      description: {
        title: '问题描述',
        placeholder: '请输入问题描述'
      },
      essence: {
        title: '本质剖析',
        researchPurpose: '研究目的',
        difficulties: '重点',
        researchPurposePlaceholder: '请输入研究目的',
        difficultiesPlaceholder: '请输入重点'
      },
      reflection: {
        title: '反思',
        suggestions: '反思与建议',
        elevation: '思维拓展与升华',
        suggestionsPlaceholder: '请输入反思与建议',
        elevationPlaceholder: '请输入思维拓展与升华'
      }
    },
    paperList: {
      title: '文章速览',
      showInvalid: '显示不可用文章',
      hideInvalid: '隐藏不可用文章',
      analyzing: '分析中...',
      noAnalysis: '无价值分析',
      loadMore: '加载更多',
      loading: '加载中...',
      noMore: '没有更多数据了',
      columns: {
        order: '排序',
        literature: '文献信息',
        abstract: '摘要',
        aiAnalysis: 'AI价值分析',
        aiUsability: 'AI可用性判断',
        similarity: '相似度分数',
        publication: '出版物',
        citations: '引用次数 / 同类文章排位(FWCI)',
        number: '编号'
      }
    },
    categoryList: {
      currentProblem: '当前问题: {name}',
      createCategory: '新建范畴',
      selectProblem: '请先在研究问题树中选择一个问题',
      noCategories: '该问题下暂无范畴，请添加新范畴或让AI助手帮助创建范畴',
      creating: '创建范畴中，请稍等...',
      placeholder: '输入检索要求',
      messages: {
        createSuccess: '范畴创建成功',
        createFailed: '创建范畴失败',
        createError: '创建范畴失败: {error}'
      }
    },
    categoryItem: {
        download: "下载数据",
        copyId: "复制标识符",
        rename: "重命名",
        delete: "删除",
        searchExpression: "检索表达式",
        save: "保存",
        cancel: "取消",
        noExpression: "未设置检索表达式",
        expressionPlaceholder: "请输入检索表达式",
        aiModify: "AI修改检索表达式",
        modify: "修改",
        designReason: "设计理由",
        metadata: "范畴元数据",
        modifyPlaceholder: "输入修改要求",
        nodeId: "节点ID",
        documentCnt: "文章总数",
        downloadProgress: "下载进度",
        modifying: "正在修改中，请稍后...",
        messages: {
            copySuccess: "标识符已复制",
            copyFailed: "复制失败，请手动复制",
            copySuccessUnsecure: "标识符已复制(当前服务器未认证)",
            emptyExpression: "检索表达式不能为空",
            expressionUpdateSuccess: "检索表达式更新成功",
            expressionUpdateFailed: "更新失败",
            emptyModifyRequirement: "请输入修改要求",
            modifySuccess: "AI修改成功，请查看并保存",
            modifyFailed: "AI修改失败",
        }
    },
    targetList: {
        title: "文献相关性排序",
        calculateMode: "当前相似度计算模式",
        MAX: "最大值",
        MIN: "最小值",
        AVG: "平均值",
        weight: "权重",
        placeholder: "请输入目标内容",
        delete: "删除",
        addTarget: "添加目标",
        edit: "编辑",
        cancel: "取消",
        submit: "完成",
    }
  }
}

const i18n = createI18n({
  legacy: false,
  locale: 'zh',
  fallbackLocale: 'en',
  messages
})

export default i18n 
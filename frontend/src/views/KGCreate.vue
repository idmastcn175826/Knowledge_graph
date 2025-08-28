<template>
  <div class="kg-create-container">
    <el-card>
      <div slot="header">
        <h2>创建知识图谱</h2>
        <p>上传文件并选择算法，构建您的专属知识图谱</p>
      </div>
      
      <el-steps :active="activeStep" finish-status="success" class="steps">
        <el-step title="选择文件"></el-step>
        <el-step title="选择算法"></el-step>
        <el-step title="模型配置"></el-step>
        <el-step title="开始构建"></el-step>
      </el-steps>
      
      <div class="step-content">
        <!-- 步骤1: 选择文件 -->
        <div v-if="activeStep === 0" class="step-file-selection">
          <el-upload
            class="upload-files"
            action=""
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            :limit="10"
            multiple
            accept=".txt,.pdf,.doc,.docx,.xls,.xlsx"
          >
            <el-button size="default" type="primary">
              <el-icon><upload-filled /></el-icon> 选择文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持上传 txt, pdf, doc, docx, xls, xlsx 格式文件，最多10个
              </div>
            </template>
          </el-upload>
          
          <div v-if="fileList.length > 0" class="selected-files">
            <h3>已选择文件:</h3>
            <el-table :data="fileList" border>
              <el-table-column prop="name" label="文件名" width="300"></el-table-column>
              <el-table-column prop="size" label="大小" width="100">
                <template #default="scope">
                  {{ formatFileSize(scope.row.size) }}
                </template>
              </el-table-column>
              <el-table-column prop="raw.type" label="类型" width="100"></el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="scope">
                  <el-button 
                    icon="Delete" 
                    type="text" 
                    @click="handleRemoveFile(scope.$index)"
                    size="small"
                  ></el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
        
        <!-- 步骤2: 选择算法 -->
        <div v-if="activeStep === 1" class="step-algorithm-selection">
          <el-form :model="algorithmForm" label-width="150px">
            <el-form-item label="数据预处理算法:">
              <el-select 
                v-model="algorithmForm.preprocess" 
                placeholder="请选择预处理算法"
              >
                <el-option label="SimHash去重" value="simhash"></el-option>
                <el-option label="MinHash去重" value="minhash"></el-option>
              </el-select>
            </el-form-item>
            
            <el-form-item label="实体抽取算法:">
              <el-select 
                v-model="algorithmForm.entity_extraction" 
                placeholder="请选择实体抽取算法"
              >
                <el-option label="BERT模型" value="bert"></el-option>
                <el-option label="CRF模型" value="crf"></el-option>
                <el-option label="Qwen模型" value="qwen"></el-option>
              </el-select>
            </el-form-item>
            
            <el-form-item label="关系抽取算法:">
              <el-select 
                v-model="algorithmForm.relation_extraction" 
                placeholder="请选择关系抽取算法"
              >
                <el-option label="BiLSTM+Attention" value="bilstm"></el-option>
                <el-option label="Qwen模型" value="qwen"></el-option>
              </el-select>
            </el-form-item>
            
            <el-form-item label="知识补全算法:">
              <el-select 
                v-model="algorithmForm.knowledge_completion" 
                placeholder="请选择知识补全算法"
              >
                <el-option label="TransE" value="transe"></el-option>
                <el-option label="TransH" value="transh"></el-option>
                <el-option label="RotatE" value="rotate"></el-option>
              </el-select>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 步骤3: 模型配置 -->
        <div v-if="activeStep === 2" class="step-model-configuration">
          <el-form :model="modelForm" label-width="150px">
            <el-form-item label="知识图谱名称:">
              <el-input 
                v-model="modelForm.kg_name" 
                placeholder="请输入知识图谱名称"
                maxlength="50"
              ></el-input>
            </el-form-item>
            
            <el-form-item label="Qwen API Key:">
              <el-input 
                v-model="modelForm.api_key" 
                placeholder="请输入Qwen API Key，不输入则使用默认"
                type="password"
                show-password
              ></el-input>
              <el-tooltip effect="dark" content="您可以在Qwen控制台获取API Key" placement="top">
                <el-icon class="info-icon"><question-filled /></el-icon>
              </el-tooltip>
            </el-form-item>
            
            <el-form-item label="模型版本:">
              <el-select 
                v-model="modelForm.model_version" 
                placeholder="请选择模型版本"
              >
                <el-option label="Qwen-7B" value="qwen-7b"></el-option>
                <el-option label="Qwen-14B" value="qwen-14b"></el-option>
                <el-option label="Qwen-Plus" value="qwen-plus"></el-option>
              </el-select>
            </el-form-item>
            
            <el-form-item label="构建选项:">
              <el-checkbox v-model="modelForm.enable_completion">启用知识补全</el-checkbox>
              <el-checkbox v-model="modelForm.enable_visualization">自动生成可视化</el-checkbox>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 步骤4: 构建进度 -->
        <div v-if="activeStep === 3" class="step-building-progress">
          <div v-if="!isBuilding && !buildSuccess && !buildFailed" class="build-prepare">
            <h3>构建参数确认</h3>
            <el-descriptions column="1" border>
              <el-descriptions-item label="知识图谱名称">{{ modelForm.kg_name }}</el-descriptions-item>
              <el-descriptions-item label="文件数量">{{ fileList.length }} 个</el-descriptions-item>
              <el-descriptions-item label="实体抽取算法">{{ getAlgorithmName('entity_extraction', algorithmForm.entity_extraction) }}</el-descriptions-item>
              <el-descriptions-item label="关系抽取算法">{{ getAlgorithmName('relation_extraction', algorithmForm.relation_extraction) }}</el-descriptions-item>
              <el-descriptions-item label="使用模型">{{ modelForm.model_version }}</el-descriptions-item>
            </el-descriptions>
            
            <el-button 
              type="primary" 
              size="large"
              @click="startBuilding"
              :loading="isPreparing"
            >
              开始构建知识图谱
            </el-button>
          </div>
          
          <div v-if="isBuilding" class="building-in-progress">
            <el-progress 
              :percentage="buildProgress" 
              :stroke-width="8"
              status="active"
            ></el-progress>
            <p class="progress-text">
              正在构建知识图谱... {{ buildProgress }}%
            </p>
            <p class="progress-stage">{{ currentStage }}</p>
            
            <el-button 
              type="warning" 
              @click="cancelBuilding"
              v-if="!isCanceling"
            >
              取消构建
            </el-button>
            <el-button 
              loading
              v-if="isCanceling"
            >
              取消中...
            </el-button>
          </div>
          
          <div v-if="buildSuccess" class="build-success">
            <el Result
              icon="SuccessFilled"
              title="知识图谱构建成功"
              sub-title="您的知识图谱已成功创建，可以开始查询和对话了"
            >
              <template #extra>
                <el-button type="primary" @click="gotoKGView">
                  查看知识图谱
                </el-button>
                <el-button @click="gotoQAChat">
                  开始对话
                </el-button>
              </template>
            </el Result>
          </div>
          
          <div v-if="buildFailed" class="build-failed">
            <el Result
              icon="ErrorFilled"
              title="知识图谱构建失败"
              :sub-title="errorMessage || '构建过程中发生错误，请稍后重试'"
            >
              <template #extra>
                <el-button type="primary" @click="restartBuilding">
                  重新构建
                </el-button>
                <el-button @click="goBack">
                  返回
                </el-button>
              </template>
            </el Result>
          </div>
        </div>
      </div>
      
      <div class="step-actions">
        <el-button 
          @click="prevStep"
          v-if="activeStep > 0 && !(activeStep === 3 && (isBuilding || buildSuccess || buildFailed))"
        >
          上一步
        </el-button>
        <el-button 
          type="primary" 
          @click="nextStep"
          v-if="activeStep < 3 && canProceed"
        >
          下一步
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { 
  UploadFilled, 
  Delete, 
  QuestionFilled,
  SuccessFilled,
  ErrorFilled
} from '@element-plus/icons-vue';
import { uploadFiles, createKG, getKGProgress } from '@/services/kgService';

const router = useRouter();

// 步骤控制
const activeStep = ref(0);
const fileList = ref([]);
const uploadProgress = ref(0);

// 表单数据
const algorithmForm = ref({
  preprocess: 'simhash',
  entity_extraction: 'bert',
  relation_extraction: 'qwen',
  knowledge_completion: 'transe'
});

const modelForm = ref({
  kg_name: '',
  api_key: '',
  model_version: 'qwen-plus',
  enable_completion: true,
  enable_visualization: true
});

// 构建状态
const isBuilding = ref(false);
const isPreparing = ref(false);
const isCanceling = ref(false);
const buildProgress = ref(0);
const currentStage = ref('准备中...');
const buildSuccess = ref(false);
const buildFailed = ref(false);
const errorMessage = ref('');
const taskId = ref('');
const progressInterval = ref(null);

// 算法名称映射
const algorithmNames = {
  preprocess: {
    'simhash': 'SimHash去重',
    'minhash': 'MinHash去重'
  },
  entity_extraction: {
    'bert': 'BERT模型',
    'crf': 'CRF模型',
    'qwen': 'Qwen模型'
  },
  relation_extraction: {
    'bilstm': 'BiLSTM+Attention',
    'qwen': 'Qwen模型'
  },
  knowledge_completion: {
    'transe': 'TransE',
    'transh': 'TransH',
    'rotate': 'RotatE'
  }
};

// 处理文件选择
const handleFileChange = (file, fileList) => {
  // 过滤重复文件
  const uniqueFiles = [];
  const fileNames = new Set();
  
  fileList.forEach(f => {
    if (!fileNames.has(f.name)) {
      fileNames.add(f.name);
      uniqueFiles.push(f);
    }
  });
  
  fileList.value = uniqueFiles;
};

// 移除文件
const handleRemoveFile = (index) => {
  fileList.value.splice(index, 1);
};

// 格式化文件大小
const formatFileSize = (size) => {
  if (size < 1024) {
    return `${size} B`;
  } else if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  } else {
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }
};

// 检查是否可以进入下一步
const canProceed = computed(() => {
  if (activeStep.value === 0) {
    return fileList.value.length > 0;
  } else if (activeStep.value === 1) {
    return true; // 算法都有默认值
  } else if (activeStep.value === 2) {
    return modelForm.value.kg_name.trim() !== '';
  }
  return false;
});

// 上一步
const prevStep = () => {
  if (activeStep.value > 0) {
    activeStep.value--;
  }
};

// 下一步
const nextStep = () => {
  if (activeStep.value < 3) {
    activeStep.value++;
  }
};

// 获取算法名称
const getAlgorithmName = (type, value) => {
  return algorithmNames[type]?.[value] || value;
};

// 开始构建
const startBuilding = async () => {
  try {
    isPreparing.value = true;
    
    // 1. 上传文件
    const fileIds = [];
    for (const file of fileList.value) {
      const result = await uploadFiles(file.raw);
      fileIds.push(result.file_id);
    }
    
    // 2. 创建知识图谱任务
    const response = await createKG({
      file_ids: fileIds,
      algorithms: algorithmForm.value,
      model_api_key: modelForm.value.api_key || null,
      kg_name: modelForm.value.kg_name
    });
    
    taskId.value = response.task_id;
    isBuilding.value = true;
    isPreparing.value = false;
    
    // 3. 轮询获取进度
    checkProgress();
    progressInterval.value = setInterval(checkProgress, 3000);
    
  } catch (error) {
    console.error('构建知识图谱失败:', error);
    isPreparing.value = false;
    buildFailed.value = true;
    errorMessage.value = error.message || '构建知识图谱失败，请重试';
  }
};

// 检查进度
const checkProgress = async () => {
  try {
    const response = await getKGProgress(taskId.value);
    
    buildProgress.value = response.progress;
    
    // 更新当前阶段
    updateCurrentStage(buildProgress.value);
    
    if (response.status === 'completed') {
      clearInterval(progressInterval.value);
      isBuilding.value = false;
      buildSuccess.value = true;
    } else if (response.status === 'failed') {
      clearInterval(progressInterval.value);
      isBuilding.value = false;
      buildFailed.value = true;
      errorMessage.value = response.message || '构建失败';
    }
  } catch (error) {
    console.error('获取进度失败:', error);
  }
};

// 更新当前阶段
const updateCurrentStage = (progress) => {
  if (progress < 5) {
    currentStage.value = '准备中...';
  } else if (progress < 15) {
    currentStage.value = '正在解析文件...';
  } else if (progress < 25) {
    currentStage.value = '正在预处理数据...';
  } else if (progress < 40) {
    currentStage.value = '正在抽取实体...';
  } else if (progress < 55) {
    currentStage.value = '正在抽取关系...';
  } else if (progress < 60) {
    currentStage.value = '正在进行实体对齐...';
  } else if (progress < 90) {
    currentStage.value = '正在补全知识并存储到数据库...';
  } else if (progress < 100) {
    currentStage.value = '正在完成最后的处理...';
  } else {
    currentStage.value = '构建完成!';
  }
};

// 取消构建
const cancelBuilding = async () => {
  isCanceling.value = true;
  // 实际应用中应该调用API取消任务
  setTimeout(() => {
    clearInterval(progressInterval.value);
    isBuilding.value = false;
    isCanceling.value = false;
    buildFailed.value = true;
    errorMessage.value = '已取消构建';
  }, 1000);
};

// 重新构建
const restartBuilding = () => {
  buildSuccess.value = false;
  buildFailed.value = false;
  buildProgress.value = 0;
  taskId.value = '';
};

// 返回
const goBack = () => {
  buildSuccess.value = false;
  buildFailed.value = false;
  buildProgress.value = 0;
  taskId.value = '';
  activeStep.value = 0;
};

// 前往图谱查看
const gotoKGView = () => {
  router.push({
    path: '/kg/view',
    query: { taskId: taskId.value }
  });
};

// 前往问答对话
const gotoQAChat = () => {
  router.push({
    path: '/qa/chat',
    query: { kgId: taskId.value }
  });
};

// 组件卸载时清理
onMounted(() => {
  return () => {
    if (progressInterval.value) {
      clearInterval(progressInterval.value);
    }
  };
});
</script>

<style scoped>
.kg-create-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 20px;
}

.steps {
  margin: 30px 0;
}

.step-content {
  margin: 40px 0;
  min-height: 300px;
}

.step-file-selection,
.step-algorithm-selection,
.step-model-configuration,
.step-building-progress {
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.upload-files {
  margin-bottom: 30px;
}

.selected-files {
  margin-top: 20px;
}

.step-actions {
  margin-top: 30px;
  text-align: right;
}

.building-in-progress {
  text-align: center;
  padding: 40px 0;
}

.progress-text {
  margin: 20px 0;
  font-size: 16px;
}

.progress-stage {
  color: #666;
  margin-top: 10px;
}

.info-icon {
  margin-left: 10px;
  color: #666;
}

.build-prepare {
  padding: 20px;
}

.build-success, .build-failed {
  margin-top: 40px;
}
</style>

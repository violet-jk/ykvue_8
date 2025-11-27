<template>
  <div class="h-[90vh] flex flex-col bg-background text-slate-600 antialiased font-sans overflow-hidden">
    <!-- 顶部导航 -->
    <nav class="bg-surface sticky top-0 z-50 border-b border-slate-200 px-6 py-4 shadow-sm backdrop-blur-md bg-white/90">
      <div class="max-w-8xl mx-auto flex justify-between items-center">
        <!-- 左侧区域：Logo 和标题 -->
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-blue-600 text-white rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/30">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
            </svg>
          </div>
          <div>
            <h1 class="text-xl font-bold text-slate-800 tracking-tight">历史数据分析</h1>
            <p class="text-xs text-slate-500 font-medium">电解槽多维度数据图表</p>
          </div>
        </div>

        <!-- 右侧区域：操作按钮 -->
        <div class="flex items-center gap-3">
          <button class="bg-slate-100 border border-slate-200 text-slate-600 hover:bg-slate-200 px-4 py-2 rounded-lg text-sm font-medium shadow-sm transition-all active:scale-95 flex items-center gap-2" @click="showInstructions">
            <span>📖</span>
            <span>使用说明</span>
          </button>

          <button class="bg-white border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-200 px-4 py-2 rounded-lg text-sm font-medium shadow-sm transition-all active:scale-95" @click="goHome">
            返回首页
          </button>
        </div>
      </div>
    </nav>

    <!-- 主要内容区域 -->
    <main class="flex-1 p-6 max-w-8xl mx-auto w-full overflow-y-auto">
      <!-- 图表类型选择器 -->
      <el-card style="margin-bottom: 20px;">
      <div style="display: flex; gap: 16px; align-items: center; flex-wrap: wrap;">
        <div v-if="chartDataLoaded">
          <el-radio-group v-model="selectedChartType" @change="handleChartTypeChange" size="large">
            <el-radio-button label="voltage">小室电压</el-radio-button>
            <el-radio-button label="avg_voltage">小室电压平均值</el-radio-button>
            <el-radio-button label="voltage_range">小室极差</el-radio-button>
            <el-radio-button label="pump_pressure">泵后压力</el-radio-button>
            <el-radio-button label="specific_gravity">碱液比重</el-radio-button>
            <el-radio-button label="hydrogen_flow_meter">氢气流量</el-radio-button>
            <el-radio-button label="inlet_outlet_pressure">电解槽进出槽压力</el-radio-button>
            <el-radio-button label="pressure_difference">电解槽进出口压差</el-radio-button>
            <el-radio-button label="oxygen_hydrogen_outlet_pressure">电解槽氢氧侧出槽压力</el-radio-button>
            <el-radio-button label="oxygen_hydrogen_outlet_temp">电解槽氢氧侧出槽温度</el-radio-button>
            <el-radio-button label="oxygen_hydrogen_cross">氧中氢/氢中氧</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div style="display: flex; gap: 16px; align-items: center; flex-wrap: wrap;margin-top: 10px">
        <div style="flex: 1; min-width: 100px;max-width: 200px;">
          <div style="margin-bottom: 4px; font-size: 14px; color: #606266;">设备名称 (Machine Name)</div>
          <el-select
              v-model="selectedMachineName"
              placeholder="请选择设备名称"
              filterable
              clearable
              style="width: 100%"
              :loading="deviceListLoading"
              @change="handleMachineNameChange"
          >
            <el-option
                v-for="name in machineNameList"
                :key="name"
                :label="name"
                :value="name"
            />
          </el-select>
        </div>
        <div style="flex: 1; min-width: 100px;max-width: 300px;">
          <div style="margin-bottom: 4px; font-size: 14px; color: #606266;">设备型号 (Machine Model)</div>
          <div style="display: flex; gap: 8px; align-items: center;">
            <el-select
                v-model="selectedMachineModel"
                placeholder="请选择设备型号"
                filterable
                clearable
                style="flex: 1;"
                :loading="deviceListLoading"
                :disabled="!selectedMachineName"
                @change="handleMachineModelChange"
            >
              <el-option
                  v-for="model in machineModelList"
                  :key="model"
                  :label="model"
                  :value="model"
              />
            </el-select>
            <el-button
                type="warning"
                plain
                :disabled="!selectedMachineName || !selectedMachineModel"
                @click="handleUpdateMachineModel"
                style="white-space: nowrap;"
            >
              修改设备型号
            </el-button>
          </div>
        </div>
        <el-divider v-if="chartDataLoaded" direction="vertical" style="height: 50px; margin: 0 8px;"/>
        <div v-if="chartDataLoaded" style="display: flex; gap: 16px; align-items: center;">
          <div>
            <div style="margin-bottom: 4px; font-size: 14px; color: #606266;">Y轴最小值 (Y Min)</div>
            <el-input-number
                v-model="yAxisMin"
                :step="yAxisStep"
                :min="0"
                placeholder="0"
                style="width: 150px"
                @change="handleYAxisChange"
                :precision="yAxisPrecision"
            />
          </div>
          <div>
            <div style="margin-bottom: 4px; font-size: 14px; color: #606266;">Y轴最大值 (Y Max)</div>
            <el-input-number
                v-model="yAxisMax"
                :step="yAxisStep"
                :min="0"
                placeholder="自适应"
                style="width: 150px"
                @change="handleYAxisChange"
                :precision="yAxisPrecision"
            />
          </div>
          <div style="padding-top: 24px;">
            <el-button @click="autoFitYAxis" type="primary">自动适配</el-button>
          </div>
        </div>
        <el-divider direction="vertical" style="height: 50px; margin: 0 8px;"/>
        <div style="display: flex; gap: 8px; padding-top: 24px;">
          <el-button
              type="primary"
              plain
              @click="showEditRawDataDialog"
              :disabled="!chartDataLoaded"
              circle
              title="修改原始数据"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width: 16px; height: 16px;">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
          </el-button>
          <el-button
              v-if="showRefreshButton"
              type="success"
              @click="refreshPage"
          >
            刷新页面
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 图表显示区域 -->
    <el-card v-if="chartDataLoaded">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div style="font-size: 16px; font-weight: 500;">
            {{
              selectedChartType === 'voltage' ? '小室电压' :
                  selectedChartType === 'voltage_range' ? '小室极差' :
                      selectedChartType === 'avg_voltage' ? '小室电压平均值' :
                          selectedChartType === 'pump_pressure' ? '泵后压力' :
                              selectedChartType === 'specific_gravity' ? '碱液比重' :
                                  selectedChartType === 'hydrogen_flow_meter' ? '氢气流量' :
                                      selectedChartType === 'inlet_outlet_pressure' ? '电解槽进出槽压力' :
                                          selectedChartType === 'oxygen_hydrogen_outlet_pressure' ? '电解槽氢氧侧出槽压力' :
                                              selectedChartType === 'oxygen_hydrogen_outlet_temp' ? '电解槽氢氧侧出槽温度' :
                                                  selectedChartType === 'oxygen_hydrogen_cross' ? '氧中氢/氢中氧' :
                                                      '电解槽进出口压差'
            }}
          </div>
          <div v-if="currentChartInfo" style="font-size: 14px; color: #666;">
            {{ currentChartInfo }}
          </div>
        </div>
      </template>

      <ChartSkeleton v-if="loading"/>
      <div
          v-show="!loading"
          ref="chartContainer"
          style="width: 100%; height: 600px;"
      ></div>

      <template #footer>
        <div style="text-align: center; color: #666; font-size: 12px;">
          渲染模式: Boost 高性能模式 |
          设备: {{ selectedDeviceName }} |
          数据点: {{ totalDataPoints }}
        </div>
      </template>
    </el-card>

    <!-- 首次加载骨架图 -->
    <el-card v-if="!chartDataLoaded && loading">
      <template #header>
        <div style="font-size: 16px; font-weight: 500;">加载中...</div>
      </template>
      <ChartSkeleton/>
    </el-card>

    <!-- 空状态提示 -->
    <el-empty v-if="!chartDataLoaded && !loading" description="请选择设备名称和型号" :image-size="200"/>

    <!-- 修改原始数据对话框 -->
    <el-dialog
        v-model="editRawDataDialogVisible"
        title="修改原始数据"
        :width="editRawDataStep === 1 ? '30%' : '80%'"
        :close-on-click-modal="false"
    >
      <!-- 第一步：选择时间点 -->
      <div v-if="editRawDataStep === 1" style="padding: 20px;">
        <h3 style="margin-bottom: 16px;">步骤 1: 选择时间点</h3>
        <div style="margin-bottom: 20px;">
          <div style="margin-bottom: 8px; font-weight: 500;">选择时间点：</div>
          <el-select-v2
              v-model="selectedXValue"
              placeholder="请选择时间点（支持搜索）"
              filterable
              remote
              :remote-method="handleRemoteSearch"
              :options="displayedXValueOptions"
              style="width: 100%"
              @change="handleXValueChange"
              @visible-change="handleSelectVisibleChange"
          >
            <template #footer>
              <div
                  v-if="displayedXValueOptions.length < allXValueOptions.length && searchQuery === ''"
                  @click="loadMoreOptions"
                  class="load-more-trigger"
              >
                点击加载更多 (已加载 {{ displayedXValueOptions.length }} / {{ allXValueOptions.length }})
              </div>
            </template>
          </el-select-v2>
        </div>
        <div style="text-align: right;">
          <el-button @click="editRawDataDialogVisible = false">取消</el-button>
          <el-button
              type="primary"
              @click="loadRawData"
              :disabled="selectedXValue === null"
              :loading="loadingRawData"
          >
            下一步
          </el-button>
        </div>
      </div>

      <!-- 第二步：编辑数据 -->
      <div v-if="editRawDataStep === 2" style="padding: 20px;">
        <h3 style="margin-bottom: 16px;">步骤 2: 编辑数据</h3>

        <el-table
            :data="rawDataTableData"
            border
            stripe
            style="width: 100%"
            max-height="500"
        >
          <el-table-column prop="cell" label="Cell" width="100" fixed/>
          <el-table-column
              v-for="(id, index) in rawDataIds"
              :key="id"
              width="180px"
              :class-name="deletedIdIndices.has(index) ? 'deleted-column' : ''"
          >
            <template #header>
              <div style="display: flex; align-items: center; justify-content: space-between; gap: 4px;">
                <span :style="deletedIdIndices.has(index) ? 'text-decoration: line-through; color: #999;' : ''">
                  ID: {{ id }}
                </span>
                <div style="display: flex; gap: 4px;">
                  <el-tooltip content="一键修改该列所有值" placement="top">
                    <el-button
                        type="primary"
                        icon="Edit"
                        size="small"
                        circle
                        @click="batchEditColumn(index)"
                        :disabled="deletedIdIndices.has(index)"
                    />
                  </el-tooltip>
                  <el-tooltip :content="deletedIdIndices.has(index) ? '恢复该列' : '删除该列'" placement="top">
                    <el-button
                        :type="deletedIdIndices.has(index) ? 'success' : 'danger'"
                        :icon="deletedIdIndices.has(index) ? 'RefreshLeft' : 'Delete'"
                        size="small"
                        circle
                        @click="toggleDeleteId(index)"
                    />
                  </el-tooltip>
                </div>
              </div>
            </template>
            <template #default="scope">
              <el-input-number
                  v-model="scope.row.values[index]"
                  :precision="0"
                  :step="10"
                  style="width: 100%"
                  :disabled="deletedIdIndices.has(index)"
                  :class="deletedIdIndices.has(index) ? 'deleted-input' : ''"
              />
            </template>
          </el-table-column>
        </el-table>

        <div style="text-align: right; margin-top: 20px;">
          <el-button @click="editRawDataStep = 1">返回</el-button>
          <el-button type="primary" @click="saveRawData" :loading="savingRawData">确认更新</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 使用说明对话框 -->
    <el-dialog
        v-model="instructionsDialogVisible"
        title="使用说明"
        width="600px"
        :close-on-click-modal="false"
    >
      <div style="line-height: 1.8; padding: 0 20px;">
        <h4 style="margin: 16px 0 12px 0; color: #409EFF; font-size: 16px;">📊 图表说明</h4>
        <p style="margin: 8px 0; font-weight: 600; color: #303133;">📈 简要说明:</p>
        <ul style="margin: 4px 0 16px 20px; color: #606266;">
          <li style="margin: 4px 0;">可自定义Y轴范围或自动适配</li>
          <li style="margin: 4px 0;">自动过滤小室电压小于1680的时间点</li>
          <li style="margin: 4px 0;">所有图表的时间点对齐</li>
          <li style="margin: 4px 0;">所有数据均为平均值(每小时),向下取整</li>
          <li style="margin: 4px 0;">X轴扩充为最大时间的1.2倍</li>
          <li style="margin: 4px 0;">修改原始数据目前仅支持修改小室电压</li>
        </ul>
        <p style="margin: 8px 0; font-weight: 600; color: #303133;">💡 操作提示:</p>
        <ul style="margin: 4px 0 16px 20px; color: #606266;">
          <li style="margin: 4px 0;">支持X轴缩放,鼠标选中区域就可以放大图表</li>
          <li style="margin: 4px 0;">按住Shift+拖拽:平移图表</li>
        </ul>
      </div>
      <template #footer>
        <div style="text-align: right;">
          <el-button type="primary" @click="instructionsDialogVisible = false">知道了</el-button>
        </div>
      </template>
    </el-dialog>
  </main>
  </div>
</template>

<script lang="ts" setup>
import {ref, onMounted, computed, onBeforeUnmount, nextTick} from 'vue';
import {useRouter} from 'vue-router';
import {ElMessage, ElMessageBox} from 'element-plus';
import Highcharts from 'highcharts';
import 'highcharts/modules/boost';
import ChartSkeleton from './ChartSkeleton.vue';

const router = useRouter();

// 返回首页
const goHome = () => {
  router.push('/home');
};

// 使用说明对话框
const instructionsDialogVisible = ref(false);

const showInstructions = () => {
  instructionsDialogVisible.value = true;
};

// 接口定义
interface DeviceInfo {
  machine_name: string;
  machine_model: string;
}

interface VoltageData {
  [cellName: string]: {
    x: number[];
    y: number[];
    t?: string[];
    id?: number[][];
  };
}

interface SingleSeriesData {
  x: number[];
  y: number[];
  t?: string[];
}

interface DualSeriesData {
  [key: string]: {
    x: number[];
    y: number[];
    t?: string[];
  };
}

interface AllDeviceData {
  voltage: VoltageData;
  avg_voltage: SingleSeriesData;
  voltage_range: SingleSeriesData;
  pump_pressure: SingleSeriesData;
  specific_gravity: SingleSeriesData;
  hydrogen_flow_meter: SingleSeriesData;
  inlet_outlet_pressure: DualSeriesData;
  oxygen_hydrogen_outlet_pressure: DualSeriesData;
  oxygen_hydrogen_outlet_temp: DualSeriesData;
  oxygen_hydrogen_cross: DualSeriesData;
  pressure_difference: SingleSeriesData;
}

// 响应式变量
const deviceList = ref<DeviceInfo[]>([]);
const deviceListLoading = ref(false);
const selectedMachineName = ref('');
const selectedMachineModel = ref('');
const selectedChartType = ref<keyof AllDeviceData>('voltage');
const loading = ref(false);
const chartDataLoaded = ref(false);
const allData = ref<AllDeviceData | null>(null);
const chartContainer = ref<HTMLElement | null>(null);
let chartInstance: Highcharts.Chart | null = null;

// Y轴设置
const yAxisMin = ref(0);
const yAxisMax = ref<number | undefined>(undefined);
const yAxisStep = ref(10);

// 修改原始数据相关变量
const editRawDataDialogVisible = ref(false);
const editRawDataStep = ref(1);
const xValueOptions = ref<Array<{ x: number, t: string }>>([]);
const allXValueOptions = ref<Array<{ x: number, t: string, label: string, value: number }>>([]);
const displayedXValueOptions = ref<Array<{ x: number, t: string, label: string, value: number }>>([]);
const currentPage = ref(1);
const pageSize = 50;
const searchQuery = ref('');
const selectedXValue = ref<number | null>(null);
const selectedTValue = ref<string | null>(null);
const loadingRawData = ref(false);
const savingRawData = ref(false);
const rawDataIds = ref<number[]>([]);
const rawDataTableData = ref<Array<{ cell: string, values: number[] }>>([]);
const cellNames = ref<string[]>([]);
const showRefreshButton = ref(false);
const deletedIdIndices = ref<Set<number>>(new Set()); // 存储要删除的ID索引

// 计算属性
const yAxisPrecision = computed(() => {
  switch (selectedChartType.value) {
    case 'voltage':
    case 'voltage_range':
    case 'avg_voltage':
      return 0;
    case 'pump_pressure':
    case 'inlet_outlet_pressure':
    case 'oxygen_hydrogen_outlet_pressure':
    case 'pressure_difference':
      return 2;
    case 'specific_gravity':
      return 3;
    case 'oxygen_hydrogen_outlet_temp':
      return 1;
    case 'oxygen_hydrogen_cross':
      return 2;
    case 'hydrogen_flow_meter':
      return 2;
    default:
      return 2;
  }
});

const machineNameList = computed(() => {
  const names = new Set<string>();
  deviceList.value.forEach(device => {
    if (device.machine_name) {
      names.add(device.machine_name);
    }
  });
  return Array.from(names).sort((a, b) => {
    const numA = parseInt(a.split('#')[0].trim()) || 0;
    const numB = parseInt(b.split('#')[0].trim()) || 0;
    return numA - numB;
  });
});

const machineModelList = computed(() => {
  if (!selectedMachineName.value) {
    return [];
  }
  const models = new Set<string>();
  deviceList.value.forEach(device => {
    if (device.machine_name === selectedMachineName.value && device.machine_model) {
      models.add(device.machine_model);
    }
  });
  return Array.from(models).sort((a, b) => b.localeCompare(a));
});

const selectedDeviceName = computed(() => {
  if (!selectedMachineName.value || !selectedMachineModel.value) return '';
  return `${selectedMachineName.value} - ${selectedMachineModel.value}`;
});

const currentChartInfo = computed(() => {
  if (!allData.value) return '';
  const data = allData.value[selectedChartType.value];
  if (!data) return '';

  if (selectedChartType.value === 'voltage') {
    const cellCount = Object.keys(data as VoltageData).length;
    return `${cellCount} 条曲线`;
  } else if (['inlet_outlet_pressure', 'oxygen_hydrogen_outlet_pressure', 'oxygen_hydrogen_outlet_temp', 'oxygen_hydrogen_cross'].includes(selectedChartType.value)) {
    return '2 条曲线';
  } else {
    return '1 条曲线';
  }
});

const totalDataPoints = computed(() => {
  if (!allData.value) return 0;
  const data = allData.value[selectedChartType.value];
  if (!data) return 0;

  if (selectedChartType.value === 'voltage') {
    return Object.values(data as VoltageData).reduce((sum, cell) => {
      if (cell.x && cell.y) {
        return sum + Math.min(cell.x.length, cell.y.length);
      }
      return sum;
    }, 0);
  } else if (['inlet_outlet_pressure', 'oxygen_hydrogen_outlet_pressure', 'oxygen_hydrogen_outlet_temp', 'oxygen_hydrogen_cross'].includes(selectedChartType.value)) {
    const dualData = data as DualSeriesData;
    let total = 0;
    Object.values(dualData).forEach((series) => {
      if (series.x && series.y) {
        total += Math.min(series.x.length, series.y.length);
      }
    });
    return total;
  } else {
    const singleData = data as SingleSeriesData;
    if (singleData.x && singleData.y) {
      return Math.min(singleData.x.length, singleData.y.length);
    }
    return 0;
  }
});

// API调用函数
const loadDeviceList = async () => {
  deviceListLoading.value = true;
  try {
    const response = await fetch('/api/get/device_list');
    const result = await response.json();
    if (result.status === 'success') {
      deviceList.value = result.data;
    } else {
      ElMessage.error('加载设备列表失败');
    }
  } catch (error) {
    console.error('Error loading device list:', error);
    ElMessage.error('加载设备列表失败');
  } finally {
    deviceListLoading.value = false;
  }
};

// 优化版:只调用一个API获取所有数据
const loadAllChartData = async () => {
  if (!selectedMachineName.value || !selectedMachineModel.value) {
    ElMessage.warning('请先选择设备名称和型号');
    return;
  }

  loading.value = true;
  try {
    const url = `/api/get/one_device/all_data?machine_name=${encodeURIComponent(selectedMachineName.value)}&machine_model=${encodeURIComponent(selectedMachineModel.value)}`;
    const response = await fetch(url);
    const result = await response.json();

    if (result.status === 'success') {
      allData.value = result.data as AllDeviceData;
      chartDataLoaded.value = true;

      // 提取第一组 voltage 数据的 x, t, id, cell 供修改原始数据使用
      const voltageData = result.data.voltage;
      if (voltageData && Object.keys(voltageData).length > 0) {
        // 获取第一个 cell 的数据（所有 cell 的 x, t, id 都是一样的）
        const firstCellKey = Object.keys(voltageData)[0];
        const firstCellData = voltageData[firstCellKey];

        if (firstCellData.x && firstCellData.t && firstCellData.id) {
          // 保存原始 x 和 t 的映射关系
          xValueOptions.value = firstCellData.x.map((x: number, index: number) => ({
            x: x,
            t: firstCellData.t![index]
          }));

          // 转换为 el-select-v2 需要的格式
          allXValueOptions.value = firstCellData.x.map((x: number, index: number) => ({
            x: x,
            t: firstCellData.t![index],
            label: `小时数: ${x} (时间: ${firstCellData.t![index]})`,
            value: x
          }));
        }

        // 保存所有 cell 名称
        cellNames.value = Object.keys(voltageData);
      }

      nextTick(() => {
        renderChart();
      });

      ElMessage.success('数据加载成功');
    } else {
      ElMessage.error(`加载数据失败: ${result.detail || '未知错误'}`);
    }
  } catch (error) {
    console.error('Error loading chart data:', error);
    ElMessage.error('加载数据失败');
  } finally {
    loading.value = false;
  }
};

// 事件处理函数
const handleMachineNameChange = () => {
  if (selectedMachineName.value) {
    localStorage.setItem('cached_machine_name_optimized', selectedMachineName.value);
  } else {
    localStorage.removeItem('cached_machine_name_optimized');
  }

  selectedMachineModel.value = '';
  localStorage.removeItem('cached_machine_model_optimized');

  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  chartDataLoaded.value = false;
  allData.value = null;
  selectedChartType.value = 'voltage';
  yAxisMin.value = 0;
  yAxisMax.value = undefined;
  yAxisStep.value = 10;
  showRefreshButton.value = false;
};

const handleMachineModelChange = async () => {
  if (selectedMachineModel.value) {
    localStorage.setItem('cached_machine_model_optimized', selectedMachineModel.value);
  } else {
    localStorage.removeItem('cached_machine_model_optimized');
  }

  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  chartDataLoaded.value = false;
  allData.value = null;
  selectedChartType.value = 'voltage';
  yAxisMin.value = 0;
  yAxisMax.value = undefined;
  yAxisStep.value = 10;
  showRefreshButton.value = false;

  if (!selectedMachineModel.value) {
    return;
  }

  await nextTick();
  loadAllChartData();
};

const handleChartTypeChange = () => {
  yAxisMin.value = 0;
  yAxisMax.value = undefined;
  yAxisStep.value = 10;
  renderChart();
};

const calculateCurrentChartAutoMaxValue = () => {
  if (!allData.value) return 0;
  const data = allData.value[selectedChartType.value];
  if (!data) return 0;

  let globalMax = 0;

  if (selectedChartType.value === 'voltage') {
    Object.values(data as VoltageData).forEach(cellData => {
      if (cellData.y && cellData.y.length > 0) {
        const validValues = cellData.y.filter(v => v !== null && v !== undefined);
        if (validValues.length > 0) {
          const max = Math.max(...validValues);
          if (max > globalMax) {
            globalMax = max;
          }
        }
      }
    });
  } else if (['inlet_outlet_pressure', 'oxygen_hydrogen_outlet_pressure', 'oxygen_hydrogen_outlet_temp', 'oxygen_hydrogen_cross'].includes(selectedChartType.value)) {
    const dualData = data as DualSeriesData;
    Object.values(dualData).forEach((series) => {
      if (series.y && series.y.length > 0) {
        const validValues = series.y.filter(v => v !== null && v !== undefined);
        if (validValues.length > 0) {
          const max = Math.max(...validValues);
          if (max > globalMax) {
            globalMax = max;
          }
        }
      }
    });
  } else {
    const singleData = data as SingleSeriesData;
    if (singleData.y && singleData.y.length > 0) {
      const validValues = singleData.y.filter(v => v !== null && v !== undefined);
      if (validValues.length > 0) {
        globalMax = Math.max(...validValues);
      }
    }
  }

  return globalMax;
};

const autoFitYAxis = () => {
  const maxValue = calculateCurrentChartAutoMaxValue();
  yAxisMin.value = 0;
  yAxisMax.value = maxValue * 1.1;
  yAxisStep.value = Math.ceil(maxValue * 0.05);

  if (chartInstance && chartInstance.yAxis && chartInstance.yAxis[0]) {
    chartInstance.yAxis[0].update({
      min: 0,
      max: maxValue * 1.1
    }, true);
  }
};

const handleYAxisChange = () => {
  if (chartInstance && chartInstance.yAxis && chartInstance.yAxis[0]) {
    chartInstance.yAxis[0].update({
      min: yAxisMin.value,
      max: yAxisMax.value || undefined
    }, true);
  }
};

// 修改设备型号
const handleUpdateMachineModel = async () => {
  if (!selectedMachineName.value || !selectedMachineModel.value) {
    ElMessage.warning('请先选择设备名称和型号');
    return;
  }

  // 第一步：输入新的设备型号
  ElMessageBox.prompt('请输入新的设备型号', '修改设备型号', {
    confirmButtonText: '下一步',
    cancelButtonText: '取消',
    inputPattern: /^.+$/,
    inputErrorMessage: '设备型号不能为空',
    inputPlaceholder: '请输入新的设备型号'
  }).then(({value: newModel}) => {
    if (!newModel || newModel.trim() === '') {
      ElMessage.warning('设备型号不能为空');
      return;
    }

    const trimmedNewModel = newModel.trim();

    // 第二步：二次确认
    ElMessageBox.confirm(
        `<div style="line-height: 1.8;">
          <p style="margin-bottom: 12px;"><strong>请确认以下修改信息：</strong></p>
          <p>设备名称：<span style="color: #409EFF; font-weight: 500;">${selectedMachineName.value}</span></p>
          <p>原设备型号：<span style="color: #E6A23C; font-weight: 500;">${selectedMachineModel.value}</span></p>
          <p>新设备型号：<span style="color: #67C23A; font-weight: 500;">${trimmedNewModel}</span></p>
          <p style="margin-top: 12px; padding: 8px; background-color: #FEF0F0; border-left: 4px solid #F56C6C; color: #F56C6C;">
            <strong>⚠️ 警告：</strong>此操作将修改数据库中的所有相关数据，一旦修改无法撤回！
          </p>
        </div>`,
        '确认修改设备型号',
        {
          confirmButtonText: '确定修改',
          cancelButtonText: '取消',
          type: 'warning',
          dangerouslyUseHTMLString: true,
          confirmButtonClass: 'el-button--danger'
        }
    ).then(async () => {
      // 执行修改
      await updateMachineModelInDatabase(selectedMachineName.value, selectedMachineModel.value, trimmedNewModel);
    }).catch(() => {
      ElMessage.info('已取消修改');
    });
  }).catch(() => {
    ElMessage.info('已取消修改');
  });
};

// 修改原始数据相关函数
const showEditRawDataDialog = () => {
  editRawDataDialogVisible.value = true;
  editRawDataStep.value = 1;
  selectedXValue.value = null;
  selectedTValue.value = null;
  rawDataTableData.value = [];
  searchQuery.value = '';
  currentPage.value = 1;
  deletedIdIndices.value = new Set(); // 清空删除标记
  // 初始化时不加载任何数据，等待下拉框打开时加载
  displayedXValueOptions.value = [];
};

// 下拉框打开/关闭时的处理
const handleSelectVisibleChange = (visible: boolean) => {
  if (visible) {
    // 打开时加载前50条数据
    searchQuery.value = '';
    currentPage.value = 1;
    loadMoreOptions();
  }
};

// 加载更多选项（模拟分页）
const loadMoreOptions = () => {
  const startIndex = (currentPage.value - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const newOptions = allXValueOptions.value.slice(startIndex, endIndex);

  if (currentPage.value === 1) {
    displayedXValueOptions.value = newOptions;
  } else {
    displayedXValueOptions.value = [...displayedXValueOptions.value, ...newOptions];
  }

  currentPage.value++;
};

// 远程搜索方法（前端模拟）
const handleRemoteSearch = (query: string) => {
  searchQuery.value = query;

  if (query === '') {
    // 清空搜索时，重新加载前50条
    currentPage.value = 1;
    displayedXValueOptions.value = allXValueOptions.value.slice(0, pageSize);
    currentPage.value = 2;
  } else {
    // 搜索时，只过滤 x 值（小时数）
    const filtered = allXValueOptions.value.filter(option => {
      return option.x.toString().includes(query);
    });
    displayedXValueOptions.value = filtered;
  }
};

const handleXValueChange = (x: number) => {
  // X 值改变时，同步更新 T 值（用于后端查询）
  const item = xValueOptions.value.find(opt => opt.x === x);
  if (item) {
    selectedTValue.value = item.t;
  }
};

// 切换ID列的删除状态
const toggleDeleteId = (index: number) => {
  if (deletedIdIndices.value.has(index)) {
    deletedIdIndices.value.delete(index);
  } else {
    deletedIdIndices.value.add(index);
  }
  // 触发响应式更新
  deletedIdIndices.value = new Set(deletedIdIndices.value);
};

// 一键修改列的所有值
const batchEditColumn = (index: number) => {
  ElMessageBox.prompt('请输入要修改的值（将应用到该列所有单元格）', '一键修改', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputPattern: /^-?\d+$/,
    inputErrorMessage: '请输入有效的整数',
    inputPlaceholder: '请输入数值'
  }).then(({value}) => {
    if (value === null || value === '') {
      ElMessage.warning('输入值不能为空');
      return;
    }

    const newValue = parseInt(value);
    if (isNaN(newValue)) {
      ElMessage.error('请输入有效的数值');
      return;
    }

    // 更新该列的所有值
    rawDataTableData.value.forEach(row => {
      row.values[index] = newValue;
    });

    ElMessage.success(`已将 ID ${rawDataIds.value[index]} 列的所有值修改为 ${newValue}`);
  }).catch(() => {
    // 用户取消操作
  });
};


const loadRawData = async () => {
  if (selectedXValue.value === null || !allData.value) return;

  loadingRawData.value = true;
  try {
    // 从 voltage 数据中获取对应 x 值的 id 列表
    const voltageData = allData.value.voltage;
    const firstCellKey = Object.keys(voltageData)[0];
    const firstCellData = voltageData[firstCellKey];

    const xIndex = firstCellData.x.findIndex((x: number) => x === selectedXValue.value);
    if (xIndex === -1) {
      ElMessage.error('未找到对应的数据');
      loadingRawData.value = false;
      return;
    }

    const ids = firstCellData.id![xIndex];

    // 调用后端接口查询数据
    const response = await fetch('/api/get/raw_data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ids: ids,
        cells: cellNames.value
      })
    });

    const result = await response.json();

    if (result.status === 'success') {
      rawDataIds.value = ids;
      // 构建表格数据
      rawDataTableData.value = result.data.map((item: any) => ({
        cell: item.cell,
        values: item.values
      }));
      editRawDataStep.value = 2;
    } else {
      ElMessage.error(`加载数据失败: ${result.detail || '未知错误'}`);
    }
  } catch (error) {
    console.error('Error loading raw data:', error);
    ElMessage.error('加载数据失败');
  } finally {
    loadingRawData.value = false;
  }
};

const saveRawData = async () => {
  savingRawData.value = true;
  try {
    // 构建更新数据和删除数据
    const updates: Array<{ id: number, cell: string, value: number }> = [];
    const deletes: number[] = [];

    // 收集要删除的ID
    deletedIdIndices.value.forEach(index => {
      deletes.push(rawDataIds.value[index]);
    });

    // 构建更新数据（排除被标记删除的列）
    rawDataTableData.value.forEach((row) => {
      row.values.forEach((value, index) => {
        if (!deletedIdIndices.value.has(index)) {
          updates.push({
            id: rawDataIds.value[index],
            cell: row.cell,
            value: value
          });
        }
      });
    });

    const response = await fetch('/api/get/update_raw_data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        updates: updates,
        deletes: deletes
      })
    });

    const result = await response.json();

    if (result.status === 'success') {
      const messages = [];
      if (result.updated_count > 0) {
        messages.push(`更新 ${result.updated_count} 条数据`);
      }
      if (result.deleted_count > 0) {
        messages.push(`删除 ${result.deleted_count} 条数据`);
      }
      ElMessage.success(`操作成功！${messages.join('，')}`);
      editRawDataDialogVisible.value = false;
      showRefreshButton.value = true;
    } else {
      ElMessage.error(`更新失败: ${result.detail || '未知错误'}`);
    }
  } catch (error) {
    console.error('Error saving raw data:', error);
    ElMessage.error('更新失败');
  } finally {
    savingRawData.value = false;
  }
};

const refreshPage = () => {
  window.location.reload();
};

// 调用后端API更新设备型号
const updateMachineModelInDatabase = async (machineName: string, oldModel: string, newModel: string) => {
  const loading = ElMessage({
    message: '正在更新数据库...',
    type: 'info',
    duration: 0
  });

  try {
    const response = await fetch('/api/get/update/machine_model', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        machine_name: machineName,
        old_machine_model: oldModel,
        new_machine_model: newModel
      })
    });

    const result = await response.json();

    if (result.status === 'success') {
      ElMessage.success(`修改成功！共更新 ${result.updated_count} 条数据`);

      // 更新当前选中的型号到localStorage
      selectedMachineModel.value = newModel;
      localStorage.setItem('cached_machine_model_optimized', newModel);

      // 延迟后刷新页面
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } else {
      ElMessage.error(`修改失败: ${result.detail || '未知错误'}`);
    }
  } catch (error) {
    console.error('Error updating machine model:', error);
    ElMessage.error('修改失败，请检查网络连接');
  } finally {
    loading.close();
  }
};

// 渲染图表函数
const renderChart = () => {
  if (!chartContainer.value || !allData.value) return;

  const data = allData.value[selectedChartType.value];
  if (!data) return;

  if (chartInstance) {
    chartInstance.destroy();
  }

  const colors = [
    "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD",
    "#8C564B", "#EFC94C", "#17BECF", "#4C72B0", "#DD8452",
    "#55A868", "#C44E52", "#8172B3", "#937860", "#64B5CD",
    "#E99675", "#97BBCD", "#B5BD89", "#FF6F61", "#6A5ACD"
  ];

  let series: Highcharts.SeriesOptionsType[] = [];
  let yAxisTitle = '';
  let chartTitle = '';
  let autoYMin: number | undefined = undefined;
  let autoYMax: number | undefined = undefined;
  let xAxisMax = 0;

  // 通用的单曲线处理函数
  const processSingleSeries = (singleData: SingleSeriesData, name: string, color: string) => {
    if (singleData.x && singleData.y) {
      series = [{
        type: 'line',
        name: name,
        data: singleData.x.map((x: number, i: number) => ({
          x: x,
          y: singleData.y[i],
          t: singleData.t ? singleData.t[i] : undefined
        })),
        color: color,
        marker: {enabled: false},
        connectNulls: true,
      }];

      const yValues = singleData.y.filter(v => v !== null && v !== undefined);
      if (yValues.length > 0) {
        const maxVal = Math.max(...yValues);
        const padding = maxVal * 0.1;
        autoYMin = 0;
        autoYMax = maxVal + padding;

        if (yAxisMax.value === undefined) {
          yAxisMin.value = 0;
          yAxisMax.value = autoYMax;
          yAxisStep.value = Math.ceil(autoYMax * 0.05);
        } else {
          autoYMin = yAxisMin.value;
          autoYMax = yAxisMax.value;
        }
      }

      if (singleData.x.length > 0) {
        const maxX = Math.max(...singleData.x);
        xAxisMax = maxX * 1.2;
      }
    }
  };

  // 通用的双曲线处理函数
  const processDualSeries = (dualData: DualSeriesData, config: Array<{ key: string, name: string, color: string }>) => {
    const seriesArray: Highcharts.SeriesOptionsType[] = [];
    const allYValues: number[] = [];

    config.forEach(({key, name, color}) => {
      const seriesData = dualData[key];
      if (seriesData && seriesData.x && seriesData.y) {
        seriesArray.push({
          type: 'line',
          name: name,
          data: seriesData.x.map((x: number, i: number) => ({
            x: x,
            y: seriesData.y[i],
            t: seriesData.t ? seriesData.t[i] : undefined
          })),
          color: color,
          marker: {enabled: false},
          connectNulls: true
        });

        const validValues = seriesData.y.filter(v => v !== null && v !== undefined);
        allYValues.push(...validValues);

        if (seriesData.x.length > 0 && xAxisMax === 0) {
          const maxX = Math.max(...seriesData.x);
          xAxisMax = maxX * 1.2;
        }
      }
    });

    series = seriesArray;

    if (allYValues.length > 0) {
      const maxVal = Math.max(...allYValues);
      const padding = maxVal * 0.1;
      autoYMin = 0;
      autoYMax = maxVal + padding;

      if (yAxisMax.value === undefined) {
        yAxisMin.value = 0;
        yAxisMax.value = autoYMax;
        yAxisStep.value = Math.ceil(autoYMax * 0.05);
      } else {
        autoYMin = yAxisMin.value;
        autoYMax = yAxisMax.value;
      }
    }
  };

  // 根据图表类型处理数据
  if (selectedChartType.value === 'voltage') {
    series = Object.entries(data as VoltageData).map(([cellName, cellData], index) => ({
      type: 'line',
      name: cellName,
      data: cellData.x.map((x: number, i: number) => ({
        x: x,
        y: cellData.y[i],
        t: cellData.t ? cellData.t[i] : undefined
      })),
      color: colors[index % colors.length],
      marker: {enabled: false},
      connectNulls: true,
    }));
    yAxisTitle = '电压 (mV)';
    chartTitle = '小室电压';

    const maxValue = calculateCurrentChartAutoMaxValue() * 1.1;
    autoYMin = 0;
    autoYMax = maxValue;

    if (yAxisMax.value === undefined) {
      yAxisMin.value = 0;
      yAxisMax.value = maxValue;
      yAxisStep.value = Math.ceil(maxValue * 0.05);
    } else {
      autoYMin = yAxisMin.value;
      autoYMax = yAxisMax.value;
    }

    const firstSeries = series[0];
    if (firstSeries && 'data' in firstSeries && Array.isArray(firstSeries.data) && firstSeries.data.length > 0) {
      const xValues = (firstSeries.data as Array<{ x: number, y: number, t?: string }>).map(point => point.x);
      const maxX = Math.max(...xValues);
      xAxisMax = maxX * 1.2;
    }
  } else if (selectedChartType.value === 'voltage_range') {
    processSingleSeries(data as SingleSeriesData, '极差', '#7cb5ec');
    yAxisTitle = '极差 (mV)';
    chartTitle = '小室极差';
  } else if (selectedChartType.value === 'avg_voltage') {
    processSingleSeries(data as SingleSeriesData, '平均电压', '#FF7F0E');
    yAxisTitle = '小室平均电压 (mV)';
    chartTitle = '小室电压平均值';
  } else if (selectedChartType.value === 'pump_pressure') {
    processSingleSeries(data as SingleSeriesData, '泵后压力', '#2CA02C');
    yAxisTitle = '泵压 (Bar)';
    chartTitle = '泵后压力';
  } else if (selectedChartType.value === 'specific_gravity') {
    processSingleSeries(data as SingleSeriesData, '碱液比重', '#D62728');
    yAxisTitle = '比重 (mg/cm³)';
    chartTitle = '碱液比重';
  } else if (selectedChartType.value === 'hydrogen_flow_meter') {
    processSingleSeries(data as SingleSeriesData, 'Hydrogen Flow', '#9467BD');
    yAxisTitle = '氢流量(L/min)';
    chartTitle = '氢气流量';
  } else if (selectedChartType.value === 'pressure_difference') {
    processSingleSeries(data as SingleSeriesData, 'Pressure Difference', '#E74C3C');
    yAxisTitle = '压力差 (Bar)';
    chartTitle = '电解槽进出口压差';
  } else if (selectedChartType.value === 'inlet_outlet_pressure') {
    processDualSeries(data as DualSeriesData, [
      {key: 'inlet_pressure', name: '进槽压力', color: '#1F77B4'},
      {key: 'oxygen_outlet_pressure', name: '氧侧出槽压力', color: '#FF7F0E'}
    ]);
    yAxisTitle = '压差 (Bar)';
    chartTitle = '电解槽进出槽压力';
  } else if (selectedChartType.value === 'oxygen_hydrogen_outlet_pressure') {
    processDualSeries(data as DualSeriesData, [
      {key: 'oxygen_outlet_pressure', name: '氧侧出槽压力', color: '#2CA02C'},
      {key: 'hydrogen_outlet_pressure', name: '氢侧出槽压力', color: '#D62728'}
    ]);
    yAxisTitle = '压差 (Bar)';
    chartTitle = '电解槽氢氧侧出槽压力';
  } else if (selectedChartType.value === 'oxygen_hydrogen_outlet_temp') {
    processDualSeries(data as DualSeriesData, [
      {key: 'oxygen_outlet_temp', name: '氧侧出槽温度', color: '#FF7F0E'},
      {key: 'hydrogen_outlet_temp', name: '氢气出槽温度', color: '#9467BD'}
    ]);
    yAxisTitle = '温度 (°C)';
    chartTitle = '电解槽氢氧侧出槽温度';
  } else if (selectedChartType.value === 'oxygen_hydrogen_cross') {
    processDualSeries(data as DualSeriesData, [
      {key: 'oxygen_in_hydrogen', name: '氧中氢', color: '#17BECF'},
      {key: 'hydrogen_in_oxygen', name: '氢中氧', color: '#8C564B'}
    ]);
    yAxisTitle = '含量 (ppm)';
    chartTitle = '氧中氢/氢中氧';
  }

  // 创建Highcharts图表
  chartInstance = Highcharts.chart(chartContainer.value, {
    accessibility: {enabled: false},
    boost: {
      useGPUTranslations: true,
      seriesThreshold: 1
    },
    chart: {
      type: 'line',
      zooming: {type: 'x'},
      panning: {enabled: true, type: 'x'},
      animation: false,
      panKey: 'shift'
    },
    title: {text: chartTitle},
    xAxis: {
      title: {text: '时间 (小时)'},
      crosshair: {
        color: '#c50404',
        width: 1,
        dashStyle: 'Solid',
        zIndex: 5
      },
      max: xAxisMax
    },
    yAxis: {
      title: {text: yAxisTitle},
      crosshair: false,
      min: autoYMin,
      max: autoYMax,
      startOnTick: false,
      endOnTick: false
    },
    legend: {
      enabled: ['voltage', 'inlet_outlet_pressure', 'oxygen_hydrogen_outlet_pressure', 'oxygen_hydrogen_outlet_temp', 'oxygen_hydrogen_cross'].includes(selectedChartType.value),
      layout: 'horizontal',
      align: 'center',
      verticalAlign: 'bottom',
      maxHeight: 80
    },
    tooltip: {
      shared: true,
      useHTML: true,
      animation: false,
      positioner: function (labelWidth, labelHeight, point) {
        const chart = this.chart;
        let x = point.plotX + chart.plotLeft + 10;
        let y = point.plotY + chart.plotTop - labelHeight / 2;

        if (x + labelWidth > chart.plotWidth + chart.plotLeft) {
          x = point.plotX + chart.plotLeft - labelWidth - 10;
        }
        if (y < chart.plotTop) {
          y = chart.plotTop;
        }
        if (y + labelHeight > chart.plotTop + chart.plotHeight) {
          y = chart.plotTop + chart.plotHeight - labelHeight;
        }

        return {x, y};
      },
      formatter: function () {
        const timeHours = this.x as number;
        let tooltip = `<div style="font-size: 14px;">`;
        tooltip += `<div style="text-align: center; font-weight: 500; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid #eee;">`;
        tooltip += `时间: <span style="color: #409EFF">${timeHours.toFixed(0)}</span> 小时`;

        if (this.points && this.points.length > 0 && (this.points[0].options as any).t) {
          tooltip += `<br><span style="font-size: 12px; color: #909399;">${(this.points[0].options as any).t}</span>`;
        }

        tooltip += `</div>`;

        if (this.points) {
          let unit = '';
          let precision = 2;

          if (selectedChartType.value === 'voltage' || selectedChartType.value === 'voltage_range' || selectedChartType.value === 'avg_voltage') {
            unit = 'mV';
            precision = 0;
          } else if (selectedChartType.value === 'pump_pressure' || selectedChartType.value === 'inlet_outlet_pressure' || selectedChartType.value === 'oxygen_hydrogen_outlet_pressure' || selectedChartType.value === 'pressure_difference') {
            unit = 'Mpa';
            precision = 2;
          } else if (selectedChartType.value === 'specific_gravity') {
            unit = 'mg/cm³';
            precision = 3;
          } else if (selectedChartType.value === 'oxygen_hydrogen_outlet_temp') {
            unit = '℃';
            precision = 1;
          } else if (selectedChartType.value === 'oxygen_hydrogen_cross') {
            unit = 'ppm';
            precision = 2;
          } else if (selectedChartType.value === 'hydrogen_flow_meter') {
            unit = 'L/min';
            precision = 2;
          }

          this.points.forEach((point: any) => {
            tooltip += `<div style="margin: 4px 0; display: flex; align-items: center; justify-content: space-between;">`;
            tooltip += `<span style="display: flex; align-items: center;">`;
            tooltip += `<span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: ${point.series.color}; margin-right: 8px;"></span>`;
            tooltip += `<span style="font-weight: 500;">${point.series.name}</span>`;
            tooltip += `</span>`;
            tooltip += `<span style="font-weight: bold; color: ${point.series.color};">&nbsp;${Number(point.y).toFixed(precision)}${unit ? ' ' + unit : ''}</span>`;
            tooltip += `</div>`;
          });
        }

        tooltip += `</div>`;
        return tooltip;
      }
    },
    plotOptions: {
      line: {
        animation: false,
        marker: {enabled: false},
        states: {
          hover: {enabled: false, lineWidth: 4}
        }
      }
    },
    series: series,
    credits: {enabled: false},
    responsive: {
      rules: [{
        condition: {maxWidth: 500},
        chartOptions: {
          legend: {enabled: false}
        }
      }]
    }
  });
};

// 生命周期钩子
onMounted(async () => {
  await loadDeviceList();

  const cachedMachineName = localStorage.getItem('cached_machine_name_optimized');
  const cachedMachineModel = localStorage.getItem('cached_machine_model_optimized');

  if (cachedMachineName && cachedMachineModel) {
    const nameExists = deviceList.value.some(d => d.machine_name === cachedMachineName);
    const modelExists = deviceList.value.some(d =>
        d.machine_name === cachedMachineName && d.machine_model === cachedMachineModel
    );

    if (nameExists && modelExists) {
      selectedMachineName.value = cachedMachineName;
      selectedMachineModel.value = cachedMachineModel;
      await loadAllChartData();
    }
  }
});

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy();
  }
});
</script>

<style scoped>
:deep(.el-radio-button__inner) {
  padding: 12px 20px;
}

.load-more-trigger {
  text-align: center;
  padding: 12px;
  cursor: pointer;
  color: #409EFF;
  border-top: 1px solid #EBEEF5;
  user-select: none;
  transition: background-color 0.3s;
}

.load-more-trigger:hover {
  background-color: #f5f7fa;
}

/* 删除列的样式 */
:deep(.deleted-column) {
  background-color: #f5f5f5 !important;
  opacity: 0.6;
}

:deep(.deleted-column .cell) {
  text-decoration: line-through;
  color: #999 !important;
}

:deep(.deleted-input .el-input-number) {
  opacity: 0.5;
}

:deep(.deleted-input .el-input-number__decrease),
:deep(.deleted-input .el-input-number__increase) {
  display: none;
}

/* Highcharts tooltip等宽数字样式 */
:deep(.highcharts-tooltip),
:deep(.highcharts-tooltip-container),
:deep(.highcharts-tooltip *) {
  font-family: "Inter", sans-serif !important;
  font-variant-numeric: tabular-nums lining-nums !important;
  font-feature-settings: "tnum" 1, "ss01" 1 !important;
}
</style>

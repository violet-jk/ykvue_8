<template>
  <el-card>
    <!-- 返回按钮和说明 -->
    <div style="margin-bottom: 20px; display: flex; gap: 12px; align-items: center;">
      <el-button @click="goHome" type="primary" plain icon="ArrowLeft">返回首页</el-button>
      <el-popover
          placement="bottom-start"
          :width="400"
          trigger="hover"
      >
        <template #reference>
          <el-button type="info" plain icon="InfoFilled">说明</el-button>
        </template>
        <div style="line-height: 1.8;">
          <h4 style="margin: 0 0 12px 0; color: #409EFF;">📊 图表说明</h4>
          <p style="margin: 8px 0;"><strong>📈 简要说明:</strong></p>
          <ul style="margin: 4px 0; padding-left: 20px;">
            <li>可自定义Y轴范围或自动适配</li>
            <li>自动过滤小室电压小于1400的时间点</li>
            <li>所有图表的时间点对齐</li>
            <li>所有数据均为平均值(每小时),向下取整</li>
            <li>X轴扩充为最大时间的2倍</li>
          </ul>
          <p style="margin: 8px 0;"><strong>💡 操作提示:</strong></p>
          <ul style="margin: 4px 0; padding-left: 20px;">
            <li>支持X轴缩放,鼠标选中区域就可以放大图表</li>
            <li>按住Shift+拖拽:平移图表</li>
          </ul>
        </div>
      </el-popover>
    </div>

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
  </el-card>
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
        xAxisMax = maxX * 2;
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
          xAxisMax = maxX * 2;
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
      xAxisMax = maxX * 2;
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
</style>

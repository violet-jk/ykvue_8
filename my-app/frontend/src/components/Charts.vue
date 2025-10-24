<template>
  <el-card>
    <!-- 返回按钮 -->
    <div style="margin-bottom: 20px;">
      <el-button @click="goHome" type="primary" plain icon="ArrowLeft">返回首页</el-button>
    </div>

    <!-- 图表类型选择器 -->
    <el-card style="margin-bottom: 20px;">
      <div style="display: flex; gap: 16px; align-items: center; flex-wrap: wrap;">
        <div v-if="chartDataLoaded" >
          <el-radio-group v-model="selectedChartType" @change="handleChartTypeChange" size="large">
            <el-radio-button label="voltage">小室电压</el-radio-button>
            <el-radio-button label="voltage_avg">小室电压平均值</el-radio-button>
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
        <div style="flex: 1; min-width: 100px;max-width: 200px;">
          <div style="margin-bottom: 4px; font-size: 14px; color: #606266;">设备型号 (Machine Model)</div>
          <el-select
              v-model="selectedMachineModel"
              placeholder="请选择设备型号"
              filterable
              clearable
              style="width: 100%"
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
        </div>
        <div v-if="chartDataLoaded"  style="display: flex; gap: 16px; align-items: center;">
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
                      selectedChartType === 'voltage_avg' ? '小室电压平均值' :
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
import {ElMessage} from 'element-plus';
import Highcharts from 'highcharts';
import 'highcharts/modules/boost';
import ChartSkeleton from './ChartSkeleton.vue';

const router = useRouter();

// 返回首页
const goHome = () => {
  router.push('/home');
};


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

interface VoltageRangeData {
  x: number[];
  y: number[];
  t?: string[];
}

interface VoltageAvgData {
  x: number[];
  y: number[];
  t?: string[];
}

interface PumpPressureData {
  x: number[];
  y: number[];
  t?: string[];
}

interface SpecificGravityData {
  x: number[];
  y: number[];
  t?: string[];
}

interface HydrogenFlowMeterData {
  x: number[];
  y: number[];
  t?: string[];
}

interface InletOutletPressureData {
  inlet_pressure: { x: number[]; y: number[]; t?: string[] };
  oxygen_outlet_pressure: { x: number[]; y: number[]; t?: string[] };
}

interface OxygenHydrogenOutletPressureData {
  oxygen_outlet_pressure: { x: number[]; y: number[]; t?: string[] };
  hydrogen_outlet_pressure: { x: number[]; y: number[]; t?: string[] };
}

interface OxygenHydrogenOutletTempData {
  oxygen_outlet_temp: { x: number[]; y: number[]; t?: string[] };
  hydrogen_outlet_temp: { x: number[]; y: number[]; t?: string[] };
}

interface OxygenHydrogenCrossData {
  oxygen_in_hydrogen: { x: number[]; y: number[]; t?: string[] };
  hydrogen_in_oxygen: { x: number[]; y: number[]; t?: string[] };
}

interface PressureDifferenceData {
  x: number[];
  y: number[];
  t?: string[];
}

const deviceList = ref<DeviceInfo[]>([]);
const deviceListLoading = ref(false);
const selectedMachineName = ref('');
const selectedMachineModel = ref('');
const selectedChartType = ref<'voltage' | 'voltage_range' | 'voltage_avg' | 'pump_pressure' | 'specific_gravity' | 'hydrogen_flow_meter' | 'inlet_outlet_pressure' | 'oxygen_hydrogen_outlet_pressure' | 'oxygen_hydrogen_outlet_temp' | 'oxygen_hydrogen_cross' | 'pressure_difference'>('voltage');
const loading = ref(false);
const chartDataLoaded = ref(false);
const chartData = ref<Record<string, VoltageData | VoltageRangeData | VoltageAvgData | PumpPressureData | SpecificGravityData | HydrogenFlowMeterData | InletOutletPressureData | OxygenHydrogenOutletPressureData | OxygenHydrogenOutletTempData | OxygenHydrogenCrossData | PressureDifferenceData>>({});
const chartContainer = ref<HTMLElement | null>(null);
let chartInstance: Highcharts.Chart | null = null;

// 存储从 cell API 返回的 global_start_time，用于后续其他曲线的数据获取
const globalStartTime = ref<string>('');

// 存储 voltage 图表第一条数据的 x 轴，用于其他图表的 x 轴对齐
const voltageXAxis = ref<number[]>([]);

// Y轴最小值和最大值
const yAxisMin = ref(0);
const yAxisMax = ref<number | undefined>(undefined);
const yAxisStep = ref(10);

// 根据图表类型动态设置精度
const yAxisPrecision = computed(() => {
  switch (selectedChartType.value) {
    case 'voltage':
    case 'voltage_range':
    case 'voltage_avg':
      return 0; // 电压 (mV)
    case 'pump_pressure':
    case 'inlet_outlet_pressure':
    case 'oxygen_hydrogen_outlet_pressure':
    case 'pressure_difference':
      return 2; // 压力 (Bar)
    case 'specific_gravity':
      return 3; // 比重 (g/cm³)
    case 'oxygen_hydrogen_outlet_temp':
      return 1; // 温度 (°C)
    case 'oxygen_hydrogen_cross':
      return 2; // 含量 (%) - ppm级别
    case 'hydrogen_flow_meter':
      return 2; // 氢流量 (L/min)
    default:
      return 2;
  }
});

// 获取唯一的 machine_name 列表
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

// 根据选中的 machine_name 过滤 machine_model 列表
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
  return Array.from(models).sort();
});

const selectedDeviceName = computed(() => {
  if (!selectedMachineName.value || !selectedMachineModel.value) return '';
  return `${selectedMachineName.value} - ${selectedMachineModel.value}`;
});

const currentChartInfo = computed(() => {
  const data = chartData.value[selectedChartType.value];
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
  const data = chartData.value[selectedChartType.value];
  if (!data) return 0;
  if (selectedChartType.value === 'voltage') {
    return Object.values(data as VoltageData).reduce((sum, cell) => {
      if (cell.x && cell.y) {
        return sum + Math.min(cell.x.length, cell.y.length);
      }
      return sum;
    }, 0);
  } else if (['inlet_outlet_pressure', 'oxygen_hydrogen_outlet_pressure', 'oxygen_hydrogen_outlet_temp', 'oxygen_hydrogen_cross'].includes(selectedChartType.value)) {
    // 双曲线图表
    const dualData = data as any;
    let total = 0;
    Object.values(dualData).forEach((series: any) => {
      if (series.x && series.y) {
        total += Math.min(series.x.length, series.y.length);
      }
    });
    return total;
  } else {
    const vrData = data as VoltageRangeData;
    if (vrData.x && vrData.y) {
      return Math.min(vrData.x.length, vrData.y.length);
    }
    return 0;
  }
});

// 加载设备列表
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

// 加载图表数据
const loadChartData = async (type: 'voltage' | 'voltage_range' | 'voltage_avg' | 'pump_pressure' | 'specific_gravity' | 'hydrogen_flow_meter' | 'inlet_outlet_pressure' | 'oxygen_hydrogen_outlet_pressure' | 'oxygen_hydrogen_outlet_temp' | 'oxygen_hydrogen_cross' | 'pressure_difference' = 'voltage') => {
  if (!selectedMachineName.value || !selectedMachineModel.value) {
    ElMessage.warning('请先选择设备名称和型号');
    return;
  }

  // 如果不是 voltage 类型，但 globalStartTime 还未获取，则先加载 voltage 数据
  if (type !== 'voltage' && !globalStartTime.value) {
    ElMessage.warning('正在加载起始时间，请稍候...');
    await loadChartData('voltage');
    // 加载完 voltage 后再加载目标类型
    if (globalStartTime.value) {
      await loadChartData(type);
    }
    return;
  }

  // 如果该类型的数据已经加载，直接渲染
  if (chartData.value[type]) {
    renderChart();
    return;
  }

  loading.value = true;
  try {
    // 映射 chart type 到 API endpoint type
    const apiTypeMap: Record<string, string> = {
      'voltage': 'cell',
      'voltage_range': 'voltage_range',
      'voltage_avg': 'voltage_avg',
      'pump_pressure': 'pump_pressure',
      'specific_gravity': 'specific_gravity',
      'hydrogen_flow_meter': 'hydrogen_flow_meter',
      'inlet_outlet_pressure': 'inlet_outlet_pressure',
      'oxygen_hydrogen_outlet_pressure': 'oxygen_hydrogen_outlet_pressure',
      'oxygen_hydrogen_outlet_temp': 'oxygen_hydrogen_outlet_temp',
      'oxygen_hydrogen_cross': 'oxygen_hydrogen_cross',
      'pressure_difference': 'pressure_difference'
    };
    const apiType = apiTypeMap[type];

    // 构建 URL，如果不是 voltage 类型且有 globalStartTime，则添加 start_time 参数
    let url = `/api/get/one_device/${apiType}?machine_name=${encodeURIComponent(selectedMachineName.value)}&machine_model=${encodeURIComponent(selectedMachineModel.value)}`;
    if (type !== 'voltage' && globalStartTime.value) {
      url += `&start_time=${encodeURIComponent(globalStartTime.value)}`;
    }

    const response = await fetch(url);
    const result = await response.json();

    if (result.status === 'success') {
      // 如果是 voltage 类型，保存 global_start_time
      if (type === 'voltage' && result.global_start_time) {
        globalStartTime.value = result.global_start_time;
        console.log('保存 global_start_time:', globalStartTime.value);
      }

      // 将数据存储到对应的 chart type key 下
      chartData.value[type] = result.data;
      chartDataLoaded.value = true;

      // 延迟渲染图表，确保 DOM 已更新
      nextTick(() => {
        renderChart();
      });

      ElMessage.success('数据加载成功');
    } else {
      ElMessage.error('加载数据失败');
    }
  } catch (error) {
    console.error('Error loading chart data:', error);
    ElMessage.error('加载数据失败');
  } finally {
    loading.value = false;
  }
};

// 处理 machine_name 选择变化
const handleMachineNameChange = () => {
  // 保存到浏览器缓存
  if (selectedMachineName.value) {
    localStorage.setItem('cached_machine_name', selectedMachineName.value);
  } else {
    localStorage.removeItem('cached_machine_name');
  }

  // 清空 machine_model 选择
  selectedMachineModel.value = '';
  localStorage.removeItem('cached_machine_model');

  // 销毁图表实例
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  // 重置所有状态
  chartDataLoaded.value = false;
  chartData.value = {};
  globalStartTime.value = '';
  voltageXAxis.value = [];
  selectedChartType.value = 'voltage';
  yAxisMin.value = 0;
  yAxisMax.value = undefined;
  yAxisStep.value = 10;
};

// 处理 machine_model 选择变化
const handleMachineModelChange = async () => {
  // 保存到浏览器缓存
  if (selectedMachineModel.value) {
    localStorage.setItem('cached_machine_model', selectedMachineModel.value);
  } else {
    localStorage.removeItem('cached_machine_model');
  }

  // 销毁旧图表实例
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }

  // 重置所有状态
  chartDataLoaded.value = false;
  chartData.value = {};
  globalStartTime.value = '';
  voltageXAxis.value = [];
  selectedChartType.value = 'voltage';
  yAxisMin.value = 0;
  yAxisMax.value = undefined;
  yAxisStep.value = 10;

  // 如果清空了 model，不加载数据直接返回
  if (!selectedMachineModel.value) {
    return;
  }

  // 等待 DOM 更新后再加载数据
  await nextTick();

  // 自动加载电压数据
  loadChartData('voltage');
};

// 处理图表类型切换
const handleChartTypeChange = () => {
  // 重置Y轴设置为自适应
  yAxisMin.value = 0;
  yAxisMax.value = undefined;
  yAxisStep.value = 10;

  loadChartData(selectedChartType.value);
};

// 计算当前图表的自适应最大值
const calculateCurrentChartAutoMaxValue = () => {
  const data = chartData.value[selectedChartType.value];
  if (!data) return 0;

  let globalMax = 0;

  if (selectedChartType.value === 'voltage') {
    Object.values(data as VoltageData).forEach(cellData => {
      if (cellData.y && cellData.y.length > 0) {
        const max = Math.max(...cellData.y);
        if (max > globalMax) {
          globalMax = max;
        }
      }
    });
  } else if (['inlet_outlet_pressure', 'oxygen_hydrogen_outlet_pressure', 'oxygen_hydrogen_outlet_temp', 'oxygen_hydrogen_cross'].includes(selectedChartType.value)) {
    // 双曲线图表 - 需要先根据voltage x轴过滤数据
    const dualData = data as any;
    Object.values(dualData).forEach((series: any) => {
      if (series.y && series.y.length > 0) {
        // 根据 voltage x 轴过滤数据后再计算最大值
        const filteredData = filterByVoltageXAxis(series);
        if (filteredData.y.length > 0) {
          const max = Math.max(...filteredData.y);
          if (max > globalMax) {
            globalMax = max;
          }
        }
      }
    });
  } else {
    // 单曲线图表 - 需要先根据voltage x轴过滤数据
    const singleData = data as any;
    if (singleData.y && singleData.y.length > 0) {
      // 根据 voltage x 轴过滤数据后再计算最大值
      const filteredData = filterByVoltageXAxis(singleData);
      if (filteredData.y && filteredData.y.length > 0) {
        globalMax = Math.max(...filteredData.y);
      }
    }
  }
  console.info(globalMax*1.1)
  return globalMax;
};

// 自动适配Y轴
const autoFitYAxis = () => {
  const maxValue = calculateCurrentChartAutoMaxValue();
  yAxisMin.value = 0;
  yAxisMax.value = maxValue * 1.1;
  yAxisStep.value = Math.ceil(maxValue * 0.05); // 步进为5%最大值

  if (chartInstance && chartInstance.yAxis && chartInstance.yAxis[0]) {
    chartInstance.yAxis[0].update({
      min: 0,
      max: maxValue * 1.1
    }, true);
  }
};

// 处理Y轴变化
const handleYAxisChange = () => {
  if (chartInstance && chartInstance.yAxis && chartInstance.yAxis[0]) {
    chartInstance.yAxis[0].update({
      min: yAxisMin.value,
      max: yAxisMax.value || undefined
    }, true);
  }
};

// 根据 voltage x 轴过滤数据
const filterByVoltageXAxis = (data: { x: number[]; y: number[]; t?: string[] }) => {
  if (!voltageXAxis.value || voltageXAxis.value.length === 0) {
    return data;
  }

  const voltageXSet = new Set(voltageXAxis.value);
  const filtered = {
    x: [] as number[],
    y: [] as number[],
    t: [] as string[]
  };

  for (let i = 0; i < data.x.length; i++) {
    if (voltageXSet.has(data.x[i])) {
      filtered.x.push(data.x[i]);
      filtered.y.push(data.y[i]);
      if (data.t && data.t[i]) {
        filtered.t.push(data.t[i]);
      }
    }
  }

  return filtered;
};

// 渲染图表
const renderChart = () => {
  if (!chartContainer.value || !chartData.value) return;

  if (!chartData.value[selectedChartType.value]) return;

  // 销毁旧图表
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
  let xAxisMax = 0; // 用于存储X轴的最大值

  if (selectedChartType.value === 'voltage') {
    // 电压图表 - 多条曲线
    series = Object.entries(chartData.value.voltage).map(([cellName, cellData], index) => ({
      type: 'line',
      name: cellName,
      data: cellData.x.map((x: number, i: number) => ({
        x: x,
        y: cellData.y[i],
        t: cellData.t ? cellData.t[i] : undefined
      })),
      color: colors[index % colors.length],
      marker: {
        enabled: false
      }
    }));
    yAxisTitle = '电压 (mV)';
    chartTitle = '小室电压';

    // 电压图表：最小值为0，自动计算最大值
    const maxValue = calculateCurrentChartAutoMaxValue() * 1.1;
    autoYMin = 0;
    autoYMax = maxValue;

    // 更新全局Y轴设置（仅首次加载或需要时）
    if (yAxisMax.value === undefined) {
      yAxisMin.value = 0;
      yAxisMax.value = maxValue;
      yAxisStep.value = Math.ceil(maxValue * 0.05); // 步进为5%最大值
    } else {
      // 使用用户设置的值
      autoYMin = yAxisMin.value;
      autoYMax = yAxisMax.value;
    }

    // 存储 voltage 图表第一条数据的 x 轴
    const firstSeries = series[0];
    if (firstSeries && 'data' in firstSeries && Array.isArray(firstSeries.data) && firstSeries.data.length > 0) {
      voltageXAxis.value = (firstSeries.data as Array<{ x: number, y: number, t?: string }>).map(point => point.x);
      // 计算X轴最大值
      const maxX = Math.max(...voltageXAxis.value);
      xAxisMax = maxX * 2; // X轴最大坐标扩展为2倍
    } else {
      voltageXAxis.value = [];
    }
  } else if (selectedChartType.value === 'voltage_range') {
    // 电压范围图表 - 单条曲线
    const vrData = chartData.value[selectedChartType.value] as VoltageRangeData;
    if (vrData.x && vrData.y) {
      // 根据 voltage x 轴过滤数据
      const filteredData = filterByVoltageXAxis(vrData);

      series = [{
        type: 'line',
        name: '极差',
        data: filteredData.x.map((x: number, i: number) => ({
          x: x,
          y: filteredData.y[i],
          t: filteredData.t ? filteredData.t[i] : undefined
        })),
        color: '#7cb5ec',
        marker: {
          enabled: false
        }
      }];

      // 自动计算最大值，最小值为0
      const yValues = filteredData.y.filter(v => v !== null && v !== undefined);
      if (yValues.length > 0) {
        const maxVal = Math.max(...yValues);
        const padding = maxVal * 0.1; // 添加10%的padding
        autoYMin = 0;
        autoYMax = maxVal + padding;

        // 更新输入框显示的值
        if (yAxisMax.value === undefined) {
          yAxisMin.value = 0;
          yAxisMax.value = autoYMax;
          yAxisStep.value = Math.ceil(autoYMax * 0.05); // 步进为5%最大值
        } else {
          autoYMin = yAxisMin.value;
          autoYMax = yAxisMax.value;
        }
      }

      // 计算X轴最大值
      if (filteredData.x.length > 0) {
        const maxX = Math.max(...filteredData.x);
        xAxisMax = maxX * 2;
      }
    } else {
      series = [];
    }
    yAxisTitle = '极差 (mV)';
    chartTitle = '小室极差';
  } else if (selectedChartType.value === 'voltage_avg') {
    // 平均电压图表 - 单条曲线
    const avgData = chartData.value[selectedChartType.value] as VoltageAvgData;
    if (avgData.x && avgData.y) {
      // 根据 voltage x 轴过滤数据
      const filteredData = filterByVoltageXAxis(avgData);

      series = [{
        type: 'line',
        name: '平均电压',
        data: filteredData.x.map((x: number, i: number) => ({
          x: x,
          y: filteredData.y[i],
          t: filteredData.t ? filteredData.t[i] : undefined
        })),
        color: '#FF7F0E',
        marker: {
          enabled: false
        }
      }];

      // 自动计算最大值，最小值为0
      const yValues = filteredData.y.filter(v => v !== null && v !== undefined);
      if (yValues.length > 0) {
        const maxVal = Math.max(...yValues);
        const padding = maxVal * 0.1; // 添加10%的padding
        autoYMin = 0;
        autoYMax = maxVal + padding;

        // 更新输入框显示的值
        if (yAxisMax.value === undefined) {
          yAxisMin.value = 0;
          yAxisMax.value = autoYMax;
          yAxisStep.value = Math.ceil(autoYMax * 0.05); // 步进为5%最大值
        } else {
          autoYMin = yAxisMin.value;
          autoYMax = yAxisMax.value;
        }
      }

      // 计算X轴最大值
      if (filteredData.x.length > 0) {
        const maxX = Math.max(...filteredData.x);
        xAxisMax = maxX * 2;
      }
    } else {
      series = [];
    }
    yAxisTitle = '小室平均电压 (mV)';
    chartTitle = '小室电压平均值';
  } else if (selectedChartType.value === 'pump_pressure') {
    // 泵压图表 - 单条曲线
    const ppData = chartData.value[selectedChartType.value] as PumpPressureData;
    if (ppData.x && ppData.y) {
      // 根据 voltage x 轴过滤数据
      const filteredData = filterByVoltageXAxis(ppData);

      series = [{
        type: 'line',
        name: '泵后压力',
        data: filteredData.x.map((x: number, i: number) => ({
          x: x,
          y: filteredData.y[i],
          t: filteredData.t ? filteredData.t[i] : undefined
        })),
        color: '#2CA02C',
        marker: {
          enabled: false
        }
      }];

      // 自动计算最大值，最小值为0
      const yValues = filteredData.y.filter(v => v !== null && v !== undefined);
      if (yValues.length > 0) {
        const maxVal = Math.max(...yValues);
        const padding = maxVal * 0.1; // 添加10%的padding
        autoYMin = 0;
        autoYMax = maxVal + padding;

        // 更新输入框显示的值
        if (yAxisMax.value === undefined) {
          yAxisMin.value = 0;
          yAxisMax.value = autoYMax;
          yAxisStep.value = Math.ceil(autoYMax * 0.05); // 步进为5%最大值
        } else {
          autoYMin = yAxisMin.value;
          autoYMax = yAxisMax.value;
        }
      }

      // 计算X轴最大值
      if (filteredData.x.length > 0) {
        const maxX = Math.max(...filteredData.x);
        xAxisMax = maxX * 2;
      }
    } else {
      series = [];
    }
    yAxisTitle = '泵压 (Bar)';
    chartTitle = '泵后压力';
  } else if (selectedChartType.value === 'specific_gravity') {
    // 比重图表 - 单条曲线
    const sgData = chartData.value[selectedChartType.value] as SpecificGravityData;
    if (sgData.x && sgData.y) {
      // 根据 voltage x 轴过滤数据
      const filteredData = filterByVoltageXAxis(sgData);

      series = [{
        type: 'line',
        name: '碱液比重',
        data: filteredData.x.map((x: number, i: number) => ({
          x: x,
          y: filteredData.y[i],
          t: filteredData.t ? filteredData.t[i] : undefined
        })),
        color: '#D62728',
        marker: {
          enabled: false
        }
      }];

      // 自动计算最大值，最小值为0
      const yValues = filteredData.y.filter(v => v !== null && v !== undefined);
      if (yValues.length > 0) {
        const maxVal = Math.max(...yValues);
        const padding = maxVal * 0.1; // 添加10%的padding
        autoYMin = 0;
        autoYMax = maxVal + padding;

        // 更新输入框显示的值
        if (yAxisMax.value === undefined) {
          yAxisMin.value = 0;
          yAxisMax.value = autoYMax;
          yAxisStep.value = Math.ceil(autoYMax * 0.05); // 步进为5%最大值
        } else {
          autoYMin = yAxisMin.value;
          autoYMax = yAxisMax.value;
        }
      }

      // 计算X轴最大值
      if (filteredData.x.length > 0) {
        const maxX = Math.max(...filteredData.x);
        xAxisMax = maxX * 2;
      }
    } else {
      series = [];
    }
    yAxisTitle = '比重 (g/cm³)';
    chartTitle = '碱液比重';
  } else if (selectedChartType.value === 'inlet_outlet_pressure') {
    // 进出口压差图表 - 双条曲线
    const ioData = chartData.value[selectedChartType.value] as InletOutletPressureData;
    if (ioData.inlet_pressure && ioData.oxygen_outlet_pressure) {
      // 根据 voltage x 轴过滤数据
      const filteredInlet = filterByVoltageXAxis(ioData.inlet_pressure);
      const filteredOutlet = filterByVoltageXAxis(ioData.oxygen_outlet_pressure);

      series = [
        {
          type: 'line',
          name: '进槽压力',
          data: filteredInlet.x.map((x: number, i: number) => ({
            x: x,
            y: filteredInlet.y[i],
            t: filteredInlet.t ? filteredInlet.t[i] : undefined
          })),
          color: '#1F77B4',
          marker: {
            enabled: false
          }
        },
        {
          type: 'line',
          name: '氧侧出槽压力',
          data: filteredOutlet.x.map((x: number, i: number) => ({
            x: x,
            y: filteredOutlet.y[i],
            t: filteredOutlet.t ? filteredOutlet.t[i] : undefined
          })),
          color: '#FF7F0E',
          marker: {
            enabled: false
          }
        }
      ];

      // 自动计算最大值，最小值为0
      const yValues = [...filteredInlet.y, ...filteredOutlet.y].filter(v => v !== null && v !== undefined);
      if (yValues.length > 0) {
        const maxVal = Math.max(...yValues);
        const padding = maxVal * 0.1; // 添加10%的padding
        autoYMin = 0;
        autoYMax = maxVal + padding;

        // 更新输入框显示的值
        if (yAxisMax.value === undefined) {
          yAxisMin.value = 0;
          yAxisMax.value = autoYMax;
          yAxisStep.value = Math.ceil(autoYMax * 0.05); // 步进为5%最大值
        } else {
          autoYMin = yAxisMin.value;
          autoYMax = yAxisMax.value;
        }
      }

      // 计算X轴最大值
      if (filteredInlet.x.length > 0) {
        const maxX = Math.max(...filteredInlet.x);
        xAxisMax = maxX * 2;
      }
    } else {
      series = [];
    }
    yAxisTitle = '压差 (Bar)';
    chartTitle = '电解槽进出槽压力';
  } else if (selectedChartType.value === 'oxygen_hydrogen_outlet_pressure') {
    // 氧氢出口压差图表 - 双条曲线
    const ohData = chartData.value[selectedChartType.value] as OxygenHydrogenOutletPressureData;
    if (ohData.oxygen_outlet_pressure && ohData.hydrogen_outlet_pressure) {
      // 根据 voltage x 轴过滤数据
      const filteredOxygen = filterByVoltageXAxis(ohData.oxygen_outlet_pressure);
      const filteredHydrogen = filterByVoltageXAxis(ohData.hydrogen_outlet_pressure);

      series = [
        {
          type: 'line',
          name: '氧侧出槽压力',
          data: filteredOxygen.x.map((x: number, i: number) => ({
            x: x,
            y: filteredOxygen.y[i],
            t: filteredOxygen.t ? filteredOxygen.t[i] : undefined
          })),
          color: '#2CA02C',
          marker: {
            enabled: false
          }
        },
        {
          type: 'line',
          name: '氢侧出槽压力',
          data: filteredHydrogen.x.map((x: number, i: number) => ({
            x: x,
            y: filteredHydrogen.y[i],
            t: filteredHydrogen.t ? filteredHydrogen.t[i] : undefined
          })),
          color: '#D62728',
          marker: {
            enabled: false
          }
        }
      ];

      // 自动计算最大值，最小值为0
      const yValues = [...filteredOxygen.y, ...filteredHydrogen.y].filter(v => v !== null && v !== undefined);
      if (yValues.length > 0) {
        const maxVal = Math.max(...yValues);
        const padding = maxVal * 0.1; // 添加10%的padding
        autoYMin = 0;
        autoYMax = maxVal + padding;

        // 更新输入框显示的值
        if (yAxisMax.value === undefined) {
          yAxisMin.value = 0;
          yAxisMax.value = autoYMax;
          yAxisStep.value = Math.ceil(autoYMax * 0.05); // 步进为5%最大值
        } else {
          autoYMin = yAxisMin.value;
          autoYMax = yAxisMax.value;
        }
      }

      // 计算X轴最大值
      if (filteredOxygen.x.length > 0) {
        const maxX = Math.max(...filteredOxygen.x);
        xAxisMax = maxX * 2;
      }
    } else {
      series = [];
    }
    yAxisTitle = '压差 (Bar)';
    chartTitle = '电解槽氢氧侧出槽压力';
  } else if (selectedChartType.value === 'oxygen_hydrogen_outlet_temp') {
    // 氧氢出口温度图表 - 双条曲线
    const otData = chartData.value[selectedChartType.value] as OxygenHydrogenOutletTempData;
    if (otData.oxygen_outlet_temp && otData.hydrogen_outlet_temp) {
      // 根据 voltage x 轴过滤数据
      const filteredOxygen = filterByVoltageXAxis(otData.oxygen_outlet_temp);
      const filteredHydrogen = filterByVoltageXAxis(otData.hydrogen_outlet_temp);

      series = [
        {
          type: 'line',
          name: '氧侧出槽温度',
          data: filteredOxygen.x.map((x: number, i: number) => ({
            x: x,
            y: filteredOxygen.y[i],
            t: filteredOxygen.t ? filteredOxygen.t[i] : undefined
          })),
          color: '#FF7F0E',
          marker: {
            enabled: false
          }
        },
        {
          type: 'line',
          name: '氢气出槽温度',
          data: filteredHydrogen.x.map((x: number, i: number) => ({
            x: x,
            y: filteredHydrogen.y[i],
            t: filteredHydrogen.t ? filteredHydrogen.t[i] : undefined
          })),
          color: '#9467BD',
          marker: {
            enabled: false
          }
        }
      ];

      // 自动计算最大值，最小值为0
      const yValues = [...filteredOxygen.y, ...filteredHydrogen.y].filter(v => v !== null && v !== undefined);
      if (yValues.length > 0) {
        const maxVal = Math.max(...yValues);
        const padding = maxVal * 0.1; // 添加10%的padding
        autoYMin = 0;
        autoYMax = maxVal + padding;

        // 更新输入框显示的值
        if (yAxisMax.value === undefined) {
          yAxisMin.value = 0;
          yAxisMax.value = autoYMax;
          yAxisStep.value = Math.ceil(autoYMax * 0.05); // 步进为5%最大值
        } else {
          autoYMin = yAxisMin.value;
          autoYMax = yAxisMax.value;
        }
      }

      // 计算X轴最大值
      if (filteredOxygen.x.length > 0) {
        const maxX = Math.max(...filteredOxygen.x);
        xAxisMax = maxX * 2;
      }
    } else {
      series = [];
    }
    yAxisTitle = '温度 (°C)';
    chartTitle = '电解槽氢氧侧出槽温度';
  } else if (selectedChartType.value === 'oxygen_hydrogen_cross') {
    // 氧氢交叉图表 - 双条曲线
    const ocData = chartData.value[selectedChartType.value] as OxygenHydrogenCrossData;
    if (ocData.oxygen_in_hydrogen && ocData.hydrogen_in_oxygen) {
      // 根据 voltage x 轴过滤数据
      const filteredOxygenInHydrogen = filterByVoltageXAxis(ocData.oxygen_in_hydrogen);
      const filteredHydrogenInOxygen = filterByVoltageXAxis(ocData.hydrogen_in_oxygen);

      series = [
        {
          type: 'line',
          name: '氧中氢',
          data: filteredOxygenInHydrogen.x.map((x: number, i: number) => ({
            x: x,
            y: filteredOxygenInHydrogen.y[i],
            t: filteredOxygenInHydrogen.t ? filteredOxygenInHydrogen.t[i] : undefined
          })),
          color: '#17BECF',
          marker: {
            enabled: false
          }
        },
        {
          type: 'line',
          name: '氢中氧',
          data: filteredHydrogenInOxygen.x.map((x: number, i: number) => ({
            x: x,
            y: filteredHydrogenInOxygen.y[i],
            t: filteredHydrogenInOxygen.t ? filteredHydrogenInOxygen.t[i] : undefined
          })),
          color: '#8C564B',
          marker: {
            enabled: false
          }
        }
      ];

      // 自动计算最大值，最小值为0
      const yValues = [...filteredOxygenInHydrogen.y, ...filteredHydrogenInOxygen.y].filter(v => v !== null && v !== undefined);
      if (yValues.length > 0) {
        const maxVal = Math.max(...yValues);
        const padding = maxVal * 0.1; // 添加10%的padding
        autoYMin = 0;
        autoYMax = maxVal + padding;

        // 更新输入框显示的值
        if (yAxisMax.value === undefined) {
          yAxisMin.value = 0;
          yAxisMax.value = autoYMax;
          yAxisStep.value = Math.ceil(autoYMax * 0.05); // 步进为5%最大值
        } else {
          autoYMin = yAxisMin.value;
          autoYMax = yAxisMax.value;
        }
      }

      // 计算X轴最大值
      if (filteredOxygenInHydrogen.x.length > 0) {
        const maxX = Math.max(...filteredOxygenInHydrogen.x);
        xAxisMax = maxX * 2;
      }
    } else {
      series = [];
    }
    yAxisTitle = '含量 (ppm)';
    chartTitle = '氧中氢/氢中氧';
  } else if (selectedChartType.value === 'pressure_difference') {
    // 压力差图表 - 单条曲线
    const pdData = chartData.value[selectedChartType.value] as PressureDifferenceData;
    if (pdData.x && pdData.y) {
      // 根据 voltage x 轴过滤数据
      const filteredData = filterByVoltageXAxis(pdData);

      series = [{
        type: 'line',
        name: 'Pressure Difference',
        data: filteredData.x.map((x: number, i: number) => ({
          x: x,
          y: filteredData.y[i],
          t: filteredData.t ? filteredData.t[i] : undefined
        })),
        color: '#E74C3C',
        marker: {
          enabled: false
        }
      }];

      // 自动计算最大值，最小值为0
      const yValues = filteredData.y.filter(v => v !== null && v !== undefined);
      if (yValues.length > 0) {
        const maxVal = Math.max(...yValues);
        const padding = maxVal * 0.1; // 添加10%的padding
        autoYMin = 0;
        autoYMax = maxVal + padding;

        // 更新输入框显示的值
        if (yAxisMax.value === undefined) {
          yAxisMin.value = 0;
          yAxisMax.value = autoYMax;
          yAxisStep.value = Math.ceil(autoYMax * 0.05); // 步进为5%最大值
        } else {
          autoYMin = yAxisMin.value;
          autoYMax = yAxisMax.value;
        }
      }

      // 计算X轴最大值
      if (filteredData.x.length > 0) {
        const maxX = Math.max(...filteredData.x);
        xAxisMax = maxX * 2;
      }
    } else {
      series = [];
    }
    yAxisTitle = '压力差 (Bar)';
    chartTitle = '电解槽进出口压差';
  } else {
    // 氢流量图表 - 单条曲线
    const hfData = chartData.value[selectedChartType.value] as HydrogenFlowMeterData;
    if (hfData.x && hfData.y) {
      // 根据 voltage x 轴过滤数据
      const filteredData = filterByVoltageXAxis(hfData);

      series = [{
        type: 'line',
        name: 'Hydrogen Flow',
        data: filteredData.x.map((x: number, i: number) => ({
          x: x,
          y: filteredData.y[i],
          t: filteredData.t ? filteredData.t[i] : undefined
        })),
        color: '#9467BD',
        marker: {
          enabled: false
        }
      }];

      // 自动计算最大值，最小值为0
      const yValues = filteredData.y.filter(v => v !== null && v !== undefined);
      if (yValues.length > 0) {
        const maxVal = Math.max(...yValues);
        const padding = maxVal * 0.1; // 添加10%的padding
        autoYMin = 0;
        autoYMax = maxVal + padding;

        // 更新输入框显示的值
        if (yAxisMax.value === undefined) {
          yAxisMin.value = 0;
          yAxisMax.value = autoYMax;
          yAxisStep.value = Math.ceil(autoYMax * 0.05); // 步进为5%最大值
        } else {
          autoYMin = yAxisMin.value;
          autoYMax = yAxisMax.value;
        }
      }

      // 计算X轴最大值
      if (filteredData.x.length > 0) {
        const maxX = Math.max(...filteredData.x);
        xAxisMax = maxX * 2;
      }
    } else {
      series = [];
    }
    yAxisTitle = '氢流量';
    chartTitle = '氢气流量';
  }

  // 创建新图表，启用 Boost 模式
  chartInstance = Highcharts.chart(chartContainer.value, {
    accessibility: {
      enabled: false
    },
    boost: {
      useGPUTranslations: true,
      seriesThreshold: 1  // 从1条series开始就启用boost
    },
    chart: {
      type: 'line',
      zooming: {
        type: 'x'
      },
      panning: {
        enabled: true,
        type: 'x'
      },
      animation: false,
      panKey: 'shift'
    },
    title: {
      text: chartTitle
    },
    xAxis: {
      title: {
        text: '时间 (小时)'
      },
      crosshair: true,
      max: xAxisMax // 设置X轴最大值
    },
    yAxis: {
      title: {
        text: yAxisTitle
      },
      crosshair: true,
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
        // 获取图表和鼠标位置
        const chart = this.chart;

        // 计算tooltip位置：数据点右侧10px
        let x = point.plotX + chart.plotLeft + 10;
        let y = point.plotY + chart.plotTop - labelHeight / 2;

        // 确保tooltip不超出图表边界
        if (x + labelWidth > chart.plotWidth + chart.plotLeft) {
          x = point.plotX + chart.plotLeft - labelWidth - 10; // 如果右侧空间不够，显示在左侧
        }
        if (y < chart.plotTop) {
          y = chart.plotTop; // 确保不超出顶部
        }
        if (y + labelHeight > chart.plotTop + chart.plotHeight) {
          y = chart.plotTop + chart.plotHeight - labelHeight; // 确保不超出底部
        }

        return { x, y };
      },
      formatter: function () {
        const timeHours = this.x as number;
        let tooltip = `<div style="font-size: 14px;">`;
        tooltip += `<div style="text-align: center; font-weight: 500; margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid #eee;">`;
        tooltip += `时间: <span style="color: #409EFF">${timeHours.toFixed(0)}</span> 小时`;

        // 显示实际时间戳（如果存在）
        if (this.points && this.points.length > 0 && (this.points[0].options as any).t) {
          tooltip += `<br><span style="font-size: 12px; color: #909399;">${(this.points[0].options as any).t}</span>`;
        }

        tooltip += `</div>`;

        if (this.points) {
          // 根据图表类型确定单位和精度
          let unit = '';
          let precision = 2;

          if (selectedChartType.value === 'voltage' || selectedChartType.value === 'voltage_range' || selectedChartType.value === 'voltage_avg') {
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
            unit = '';
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
        marker: {
          enabled: false
        },
        states: {
          hover: {
            enabled: true,
            lineWidth: 4
          }
        }
      }
    },
    series: series,
    credits: {
      enabled: false
    },
    responsive: {
      rules: [{
        condition: {
          maxWidth: 500
        },
        chartOptions: {
          legend: {
            enabled: false
          }
        }
      }]
    }
  });
};

onMounted(async () => {
  // 先加载设备列表
  await loadDeviceList();

  // 从浏览器缓存恢复上次选择的设备名称和型号
  const cachedMachineName = localStorage.getItem('cached_machine_name');
  const cachedMachineModel = localStorage.getItem('cached_machine_model');

  if (cachedMachineName && cachedMachineModel) {
    // 验证缓存的值在设备列表中存在
    const nameExists = deviceList.value.some(d => d.machine_name === cachedMachineName);
    const modelExists = deviceList.value.some(d =>
        d.machine_name === cachedMachineName && d.machine_model === cachedMachineModel
    );

    if (nameExists && modelExists) {
      selectedMachineName.value = cachedMachineName;
      selectedMachineModel.value = cachedMachineModel;

      // 自动加载上次选择的设备的电压数据
      await loadChartData('voltage');
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

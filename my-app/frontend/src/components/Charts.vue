<template>
  <el-card>
    <!-- 设备选择器 -->
    <el-card style="margin-bottom: 20px;">
      <div style="display: flex; gap: 16px; align-items: center; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 200px;">
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
        <div style="flex: 1; min-width: 200px;">
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
        <el-button
          type="primary"
          :loading="loading"
          :disabled="!selectedMachineName || !selectedMachineModel"
          @click="loadChartData"
          style="margin-top: 24px;"
        >
          加载数据
        </el-button>
      </div>
    </el-card>

    <!-- 图表类型选择器 -->
    <el-card v-if="chartDataLoaded" style="margin-bottom: 20px;">
      <el-radio-group v-model="selectedChartType" @change="handleChartTypeChange">
        <el-radio-button label="voltage">电压图表 (Voltage)</el-radio-button>
        <el-radio-button label="voltage_range">电压范围图表 (Voltage Range)</el-radio-button>
      </el-radio-group>
    </el-card>

    <!-- 图表显示区域 -->
    <el-card v-if="chartDataLoaded">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div style="font-size: 16px; font-weight: 500;">
            {{ selectedChartType === 'voltage' ? '电压图表 (Voltage)' : '电压范围图表 (Voltage Range)' }}
          </div>
          <div v-if="currentChartInfo" style="font-size: 14px; color: #666;">
            {{ currentChartInfo }}
          </div>
        </div>
      </template>

      <ChartSkeleton v-if="loading" />
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

    <!-- 空状态提示 -->
    <el-empty v-if="!chartDataLoaded" description="请选择设备名称和型号并加载数据" :image-size="200" />
  </el-card>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed, onBeforeUnmount } from 'vue';
import { ElMessage } from 'element-plus';
import Highcharts from 'highcharts';
import 'highcharts/modules/boost';
import ChartSkeleton from './ChartSkeleton.vue';


interface DeviceInfo {
  machine_name: string;
  machine_model: string;
}

interface ChartData {
  voltage: Record<string, { x: number[]; y: number[] }>;
  voltage_range: { x: number[]; y: number[] };
}

const deviceList = ref<DeviceInfo[]>([]);
const deviceListLoading = ref(false);
const selectedMachineName = ref('');
const selectedMachineModel = ref('');
const selectedChartType = ref<'voltage' | 'voltage_range'>('voltage');
const loading = ref(false);
const chartDataLoaded = ref(false);
const chartData = ref<ChartData | null>(null);
const chartContainer = ref<HTMLElement | null>(null);
let chartInstance: Highcharts.Chart | null = null;

// 获取唯一的 machine_name 列表
const machineNameList = computed(() => {
  const names = new Set<string>();
  deviceList.value.forEach(device => {
    if (device.machine_name) {
      names.add(device.machine_name);
    }
  });
  return Array.from(names).sort();
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
  if (!chartData.value) return '';
  if (selectedChartType.value === 'voltage') {
    const cellCount = Object.keys(chartData.value.voltage).length;
    return `${cellCount} 条曲线`;
  } else {
    return '1 条曲线';
  }
});

const totalDataPoints = computed(() => {
  if (!chartData.value) return 0;
  if (selectedChartType.value === 'voltage') {
    return Object.values(chartData.value.voltage).reduce((sum, cell) => sum + cell.x.length, 0);
  } else {
    return chartData.value.voltage_range.x.length;
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
const loadChartData = async () => {
  if (!selectedMachineName.value || !selectedMachineModel.value) {
    ElMessage.warning('请先选择设备名称和型号');
    return;
  }

  loading.value = true;
  try {
    const response = await fetch(
      `/api/get/one_device?machine_name=${encodeURIComponent(selectedMachineName.value)}&machine_model=${encodeURIComponent(selectedMachineModel.value)}`
    );
    const result = await response.json();

    if (result.status === 'success') {
      chartData.value = result;
      chartDataLoaded.value = true;

      // 延迟渲染图表，确保 DOM 已更新
      setTimeout(() => {
        renderChart();
      }, 100);

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
  // 清空 machine_model 选择
  selectedMachineModel.value = '';
  // 清空图表数据
  chartDataLoaded.value = false;
  chartData.value = null;
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
};

// 处理 machine_model 选择变化
const handleMachineModelChange = () => {
  // 清空图表数据
  chartDataLoaded.value = false;
  chartData.value = null;
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
};

// 处理图表类型切换
const handleChartTypeChange = () => {
  if (chartData.value) {
    renderChart();
  }
};

// 渲染图表
const renderChart = () => {
  if (!chartContainer.value || !chartData.value) return;

  // 销毁旧图表
  if (chartInstance) {
    chartInstance.destroy();
  }

  const colors = [
    '#7cb5ec', '#434348', '#90ed7d', '#f7a35c', '#8085e9',
    '#f15c80', '#e4d354', '#2b908f', '#f45b5b', '#91e8e1',
    '#7cb5ec', '#434348', '#90ed7d', '#f7a35c', '#8085e9',
    '#f15c80', '#e4d354', '#2b908f', '#f45b5b', '#91e8e1'
  ];

  let series: Highcharts.SeriesOptionsType[] = [];
  let yAxisTitle = '';
  let chartTitle = '';

  if (selectedChartType.value === 'voltage') {
    // 电压图表 - 多条曲线
    series = Object.entries(chartData.value.voltage).map(([cellName, cellData], index) => ({
      type: 'line',
      name: cellName,
      data: cellData.x.map((x, i) => [x, cellData.y[i]]),
      color: colors[index % colors.length],
      marker: {
        enabled: false
      }
    }));
    yAxisTitle = '电压 (mV)';
    chartTitle = '电压图表 (Voltage)';
    console.info(series)
  } else {
    // 电压范围图表 - 单条曲线
    const vrData = chartData.value.voltage_range;
    series = [{
      type: 'line',
      name: 'Voltage Range',
      data: vrData.x.map((x, i) => [x, vrData.y[i]]),
      color: '#7cb5ec',
      marker: {
        enabled: false
      }
    }];
    yAxisTitle = '电压范围 (mV)';
    chartTitle = '电压范围图表 (Voltage Range)';
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
      crosshair: true
    },
    yAxis: {
      title: {
        text: yAxisTitle
      },
      crosshair: true
    },
    legend: {
      enabled: selectedChartType.value === 'voltage',
      layout: 'horizontal',
      align: 'center',
      verticalAlign: 'bottom',
      maxHeight: 80
    },
    tooltip: {
      shared: false,
      formatter: function() {
        return `<b>${this.series.name}</b><br/>时间: ${this.x} 小时<br/>值: ${this.y}`;
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
            lineWidth: 3
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

onMounted(() => {
  loadDeviceList();
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

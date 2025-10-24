<template>
  <div class="home-container">
    <!-- 顶部统计卡片 -->
    <div class="stats-row">
      <el-card class="stat-card">
        <template #header>
          <div class="card-header">正在运行的设备</div>
        </template>
        <template #default>
          <div class="stat-content">
            <div class="circle-progress">
              <svg viewBox="0 0 200 200" class="progress-svg">
                <defs>
                  <linearGradient id="gradientStroke" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color: #4facfe; stop-opacity: 1"/>
                    <stop offset="100%" style="stop-color: #00f2fe; stop-opacity: 1"/>
                  </linearGradient>
                </defs>
                <!-- 背景圆环 -->
                <circle cx="100" cy="100" r="80" class="progress-bg"/>
                <!-- 进度圆环 -->
                <circle
                    cx="100"
                    cy="100"
                    r="80"
                    class="progress-circle"
                    :style="{
                    strokeDashoffset: 502.4 - (502.4 * runningDevicesCount / 15)
                  }"
                />
              </svg>
              <div class="circle-text">
                <div class="circle-value">{{ runningDevicesCount }}</div>
                <div class="circle-total">/15</div>
              </div>
            </div>
            <!-- MQTT 状态显示在右下角 -->
            <div class="mqtt-status-badge">
              <div class="status-indicator" :class="serverStatus">
                <span class="status-dot"></span>
                <span class="status-text">{{ serverStatus === 'running' ? '运行中' : '未运行' }}</span>
              </div>
            </div>
          </div>
        </template>
      </el-card>
      <el-card class="stat-card">
        <template #header>
          <div class="card-header">最近查询时间</div>
        </template>
        <template #default>
          <div class="stat-content">
            <div class="stat-value">{{ queryTime }}</div>
            <div class="refresh-countdown">自动刷新倒计时：{{ formattedCountdown }}</div>

          </div>
        </template>
      </el-card>
      <el-card class="stat-card">
        <template #header>
          <div class="card-header">图表显示时间</div>
        </template>
        <template #default>
          <div class="stat-content">
            <div class="day-selector">
              <button
                  class="day-btn"
                  :class="{ active: selectedDay === 1 }"
                  @click="selectDay(1)"
              >
                最近1天
              </button>
              <button
                  class="day-btn"
                  :class="{ active: selectedDay === 7 }"
                  @click="selectDay(7)"
              >
                最近一周
              </button>
            </div>
          </div>
        </template>
      </el-card>
      <el-card class="stat-card">
        <template #header>
          <div class="card-header">其他</div>
        </template>
        <div class="button-group">
          <el-button type="success" class="action-btn" @click="handleExportData">
            <span class="btn-icon">📥</span>
            导出数据
          </el-button>
          <el-button type="primary" class="action-btn" @click="handleHistoryClick">
            <span class="btn-icon">📋</span>
            查看历史记录
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 设备电压图表 -->
    <div v-if="loading" class="charts-container">
      <el-card class="chart-card">
        <template #header>
          <div class="chart-title">总看板</div>
        </template>
        <template #default>
          <ChartSkeleton/>
        </template>
      </el-card>
    </div>
    <div v-else-if="devicesWithData.length === 0" class="charts-container">
      <el-card class="no-data-card">
        <template #default>
          <div class="no-data">暂无数据</div>
        </template>
      </el-card>
    </div>
    <el-card v-else class="chart-card">
      <template #header>
        <div class="chart-title">所有设备电压平均值总览</div>
      </template>
      <template #default>
        <div id="combined-chart" class="chart-wrapper-large"></div>
      </template>
    </el-card>

    <!-- 导出数据对话框 -->
    <el-dialog
      v-model="exportDialogVisible"
      title="导出数据"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="export-dialog-content">
        <div class="date-range-label">选择时间范围</div>
        <el-date-picker
          v-model="exportDateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="起始时间"
          end-placeholder="截止时间"
          format="YYYY-MM-DD HH:mm:ss"
          style="width: 90%"
        />
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="exportDialogVisible = false" :disabled="exportLoading">取消</el-button>
          <el-button type="primary" @click="confirmExport" :loading="exportLoading">
            {{ exportLoading ? '导出中...' : '确认导出' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted, onUnmounted} from 'vue'
import {useRouter} from 'vue-router'
import axios from 'axios'
import Highcharts from 'highcharts'
import {ElMessage} from 'element-plus'
import ChartSkeleton from './ChartSkeleton.vue'

interface VoltageData {
  date: string
  time: string
  avg_voltage: number
}

interface Device {
  machine_name: string
  voltage_data: VoltageData[]
}

interface OverviewResponse {
  query_time: string
  devices: Device[]
}

// 响应式数据
const router = useRouter()
const loading = ref(false)
const selectedDay = ref(1)
const queryTime = ref('')
const devicesData = ref<Device[]>([])
const chartsMap = new Map<string, Highcharts.Chart>()
const refreshCountdown = ref(300)
const serverStatus = ref<'running' | 'stopped'>('stopped') // 默认为未运行
let refreshInterval: ReturnType<typeof setInterval> | null = null
let countdownInterval: ReturnType<typeof setInterval> | null = null

// 计算属性
const runningDevicesCount = computed(() => {
  return devicesData.value.filter(device => {
    // 设备有数据，且最近一次电压值 >= 100 才算正在运行
    if (device.voltage_data.length === 0) return false
    const lastVoltage = device.voltage_data[device.voltage_data.length - 1]
    return lastVoltage.avg_voltage >= 100
  }).length
})

const devicesWithData = computed(() => {
  return devicesData.value.filter(device => device.voltage_data.length > 0)
})

// 格式化倒计时为 X:Y 格式（分:秒）
const formattedCountdown = computed(() => {
  const minutes = Math.floor(refreshCountdown.value / 60)
  const seconds = refreshCountdown.value % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
})

// 获取后端数据
const fetchOverviewData = async () => {
  loading.value = true
  try {
    const response = await axios.get<OverviewResponse>('/api/home/overview', {
      params: {
        day: selectedDay.value
      }
    })

    queryTime.value = response.data.query_time
    devicesData.value = response.data.devices

    // 获取数据后初始化图表
    setTimeout(() => {
      initCharts()
    }, 100)
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 获取MQTT连接状态
const fetchMqttStatus = async () => {
  try {
    const response = await axios.get('/api/mqtt/status')
    serverStatus.value = response.data.connected ? 'running' : 'stopped'
  } catch (error) {
    console.error('获取MQTT状态失败:', error)
    serverStatus.value = 'stopped'
  }
}

// 启动自动刷新
const startAutoRefresh = () => {
  // 清除之前的定时器
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  if (countdownInterval) {
    clearInterval(countdownInterval)
  }

  // 每300秒（5分钟）刷新一次数据
  refreshInterval = setInterval(() => {
    fetchOverviewData()
    fetchMqttStatus() // 同时检查MQTT状态
    refreshCountdown.value = 300
  }, 300000)

  // 每秒更新倒计时
  countdownInterval = setInterval(() => {
    if (refreshCountdown.value > 0) {
      refreshCountdown.value--
    }
  }, 1000)

  // 每60秒检查一次MQTT连接状态
  const mqttStatusInterval = setInterval(() => {
    fetchMqttStatus()
  }, 60000)

  // 保存MQTT状态检查定时器的引用，以便后续清理
  ;(window as any).__mqttStatusInterval = mqttStatusInterval
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
  if (countdownInterval) {
    clearInterval(countdownInterval)
    countdownInterval = null
  }
  // 清除MQTT状态检查定时器
  if ((window as any).__mqttStatusInterval) {
    clearInterval((window as any).__mqttStatusInterval)
    ;(window as any).__mqttStatusInterval = null
  }
}

// 处理历史记录按钮点击
const handleHistoryClick = () => {
  router.push('/charts')
}

// 导出对话框相关
const exportDialogVisible = ref(false)
const exportLoading = ref(false)

// 初始化默认时间范围（最近一个月到现在）
const getDefaultDateRange = (): [Date, Date] => {
  const endDate = new Date()
  const startDate = new Date()
  startDate.setMonth(startDate.getMonth() - 1)
  return [startDate, endDate]
}

const exportDateRange = ref<[Date, Date]>(getDefaultDateRange())

// 处理导出数据
const handleExportData = () => {
  // 每次打开对话框时重新设置默认时间范围
  exportDateRange.value = getDefaultDateRange()
  exportDialogVisible.value = true
}

// 确认导出
const confirmExport = async () => {
  if (!exportDateRange.value || exportDateRange.value.length !== 2) {
    ElMessage.warning('请选择起始和截止时间')
    return
  }

  const [startDate, endDate] = exportDateRange.value

  // 格式化时间为 YYYY-MM-DD HH:MM:SS
  const formatDateTime = (date: Date) => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  }

  const startDateTime = formatDateTime(startDate)
  const endDateTime = formatDateTime(endDate)

  exportLoading.value = true // 开始加载

  try {
    // 调用后端API导出数据
    const response = await axios.get('/api/home/export', {
      params: {
        start_datetime: startDateTime,
        end_datetime: endDateTime
      },
      responseType: 'blob'
    })

    // 创建下载链接
    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    // 从响应头获取文件名，如果没有则使用默认名称
    const contentDisposition = response.headers['content-disposition']
    let filename = `设备数据_${startDateTime.replace(/[:\s-]/g, '')}_${endDateTime.replace(/[:\s-]/g, '')}.csv`
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename=(.+)/)
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1]
      }
    }

    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('数据导出成功')
    exportDialogVisible.value = false
  } catch (error: any) {
    console.error('导出数据失败:', error)
    if (error.response && error.response.data) {
      // 如果是Blob类型的错误响应，需要读取其内容
      const reader = new FileReader()
      reader.onload = () => {
        try {
          const errorData = JSON.parse(reader.result as string)
          ElMessage.error(errorData.detail || '导出数据失败')
        } catch {
          ElMessage.error('导出数据失败，请稍后重试')
        }
      }
      reader.readAsText(error.response.data)
    } else {
      ElMessage.error('导出数据失败，请稍后重试')
    }
  } finally {
    exportLoading.value = false // 结束加载
  }
}

// 选择查询天数
const selectDay = (day: number) => {
  selectedDay.value = day
  fetchOverviewData()
}

// 初始化图表
const initCharts = () => {
  if (devicesWithData.value.length === 0) return

  const chartId = 'combined-chart'
  const chartElement = document.getElementById(chartId)

  if (!chartElement) return

  // 销毁旧图表实例（如果存在）
  if (chartsMap.has(chartId)) {
    const oldChart = chartsMap.get(chartId)
    if (oldChart) {
      oldChart.destroy()
    }
    chartsMap.delete(chartId)
  }

  // 收集所有时间点（用作X轴分类）
  const timePointsSet = new Set<string>()
  devicesWithData.value.forEach(device => {
    device.voltage_data.forEach(d => {
      timePointsSet.add(`${d.date} ${d.time}`)
    })
  })
  const categories = Array.from(timePointsSet).sort()

  // 将时间字符串转换为时间戳（毫秒）
  const categoryTimestamps = categories.map(cat => {
    return new Date(cat).getTime()
  })

  // 为每个设备创建数据系列，颜色自动分配
  const colors = [
    "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728", "#9467BD",
    "#8C564B", "#EFC94C", "#17BECF", "#4C72B0", "#DD8452",
    "#55A868", "#C44E52", "#8172B3", "#937860", "#64B5CD",
    "#E99675", "#97BBCD", "#B5BD89", "#FF6F61", "#6A5ACD"
  ];

  const series = devicesWithData.value.map((device, index) => {
    // 为当前设备的所有时间点创建数据映射
    const dataMap = new Map<string, number>()
    device.voltage_data.forEach(d => {
      const timePoint = `${d.date} ${d.time}`
      dataMap.set(timePoint, d.avg_voltage)
    })

    // 生成完整的数据序列，使用 [时间戳, 值] 格式
    const data = categories.map((cat, idx) => {
      const voltage = dataMap.get(cat)
      if (voltage !== undefined) {
        return [categoryTimestamps[idx], voltage]
      }
      return [categoryTimestamps[idx], null]
    })

    return {
      name: device.machine_name,
      data: data,
      color: colors[index % colors.length],
      type: 'line' as const,
      marker: {
        enabled: false
      }
    }
  })

  // 创建合并图表
  const newChart = Highcharts.chart(chartId, {
    chart: {
      type: 'line' as const,
      height: 550
    },
    title: {
      text: ''
    },
    xAxis: {
      type: 'datetime',
      title: {
        text: '时间'
      },
      labels: {
        rotation: 0,
        align: 'center',
      },
      dateTimeLabelFormats: {
        millisecond: '%H:%M:%S.%L',
        second: '%H:%M:%S',
        minute: '%H:%M',
        hour: '%H:%M',
        day: '%m-%d',
        week: '%m-%d',
        month: '%Y-%m',
        year: '%Y'
      }
    },
    yAxis: {
      title: {
        text: '平均电压值 (mV)'
      },
      min: 0
    },
    tooltip: {
      shared: true,
      crosshairs: true,
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#ddd',
      borderRadius: 8,
      borderWidth: 1,
      padding: 12,
      useHTML: true,
      formatter: function (this: any): string {
        const date = new Date(this.x)
        const year = date.getFullYear()
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        const hours = String(date.getHours()).padStart(2, '0')
        const minutes = String(date.getMinutes()).padStart(2, '0')
        const seconds = String(date.getSeconds()).padStart(2, '0')
        const formattedTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`

        let s = '<div style="color: #333; font-weight: 700; margin-bottom: 8px; font-size: 13px;">' + formattedTime + '</div>'

        this.points?.forEach((point: any) => {
          if (point.y !== null && point.y !== undefined) {
            s += '<div style="margin: 4px 0; color: #333; font-weight: 500;">' +
                '<span style="color: ' + point.color + '; font-weight: 700; margin-right: 6px;">●</span>' +
                '<span style="color: ' + point.color + '; font-weight: 700;">' + point.series.name + ': ' + point.y.toFixed(2) + ' mV</span></div>'
          }
        })

        return s
      }
    } as any,
    legend: {
      enabled: true,
      layout: 'horizontal',
      align: 'center',
      verticalAlign: 'bottom'
    },
    series: series,
    credits: {
      enabled: false
    },
    responsive: {
      rules: [
        {
          condition: {
            maxWidth: 500
          },
          chartOptions: {
            xAxis: {
              labels: {
                rotation: -45,
                align: 'right'
              },
            },
            legend: {
              layout: 'horizontal',
              align: 'center',
              verticalAlign: 'bottom'
            }
          }
        }
      ]
    }
  } as any)

  // 存储图表引用
  chartsMap.set(chartId, newChart)
}

// 页面加载时获取数据并启动自动刷新
onMounted(() => {
  fetchOverviewData()
  fetchMqttStatus() // 初始化MQTT状态检查
  startAutoRefresh()
})

// 页面卸载时停止自动刷新
onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
/* 全局容器 */
.home-container {
  padding: 24px;
  background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
  position: relative;
  overflow: hidden;
}

.home-container::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.3) 0%, transparent 70%);
  animation: rotate 30s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 统计卡片行 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 32px;
  position: relative;
  z-index: 1;
}

.stat-card {
  position: relative;
  overflow: hidden;
  border: none;
  height: 220px;
}

.stat-card :deep(.el-card) {
  border: none;
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  overflow: hidden;
  position: relative;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.stat-card :deep(.el-card):hover {
  transform: translateY(-12px) scale(1.02);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
}

.stat-card :deep(.el-card__body) {
  padding: 16px 20px;
  position: relative;
  z-index: 2;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-card :deep(.el-card__header) {
  padding: 10px 20px;
  border-bottom: none;
  background: transparent;
  position: relative;
  z-index: 3;
}

.card-header {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-align: center;
  color: #2d3748;
  margin: 0;
  padding-top: 2px;
}

/* 为每个卡片标题设置不同的颜色 */
.stat-card:nth-child(1) .card-header {
  color: #0284c7;
}

.stat-card:nth-child(2) .card-header {
  color: #0ea5e9;
}

.stat-card:nth-child(3) .card-header {
  color: #0891b2;
}

.stat-card:nth-child(4) .card-header {
  color: #0e7490;
}

/* 第一个卡片 - 运行设备 */
.stat-card:nth-child(1) :deep(.el-card)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 6px;
  background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%);
}

/* 第二个卡片 - 查询时间 */
.stat-card:nth-child(2) :deep(.el-card)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 6px;
  background: linear-gradient(90deg, #38bdf8 0%, #7dd3fc 100%);
}

/* 第三个卡片 - 服务器状态 */
.stat-card:nth-child(3) :deep(.el-card)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 6px;
  background: linear-gradient(90deg, #0ea5e9 0%, #06b6d4 100%);
}

/* 第四个卡片 - 查询天数 */
.stat-card:nth-child(4) :deep(.el-card)::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 6px;
  background: linear-gradient(90deg, #06b6d4 0%, #0891b2 100%);
}

.stat-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 140px;
}

.mqtt-status-badge {
  position: absolute;
  bottom: -10px;
  right: -10px;
  z-index: 10;
}


.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a202c;
  position: relative;
  z-index: 2;
  letter-spacing: 1px;
  text-align: center;
  line-height: 1.4;
}

.stat-card:nth-child(2) .stat-value {
  color: #2d3748;
  font-size: 20px;
  margin-bottom: 10px;
  font-weight: 600;
  max-width: 260px;
}

/* 圆环进度条 */
.circle-progress {
  position: relative;
  width: 130px;
  height: 130px;
  margin: 8px auto 0;
}

.progress-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
  filter: drop-shadow(0 4px 12px rgba(79, 172, 254, 0.3));
}

.progress-bg {
  fill: none;
  stroke: #e2e8f0;
  stroke-width: 14;
}

.progress-circle {
  fill: none;
  stroke: url(#gradientStroke);
  stroke-width: 14;
  stroke-linecap: round;
  stroke-dasharray: 502.4;
  stroke-dashoffset: 0;
  transition: stroke-dashoffset 0.8s cubic-bezier(0.65, 0, 0.35, 1);
}

.circle-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 3;
}

.circle-value {
  font-size: 42px;
  font-weight: 800;
  letter-spacing: -2px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.circle-total {
  font-size: 18px;
  font-weight: 600;
  color: #a0aec0;
  margin-top: 2px;
}

.refresh-countdown {
  font-size: 18px;
  margin-top: 8px;
  position: relative;
  z-index: 2;
  font-weight: 700;
  padding: 12px 24px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ff5252 100%);
  color: white;
  border-radius: 24px;
  box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
  display: inline-block;
  letter-spacing: 1px;
}

/* 服务器状态 */
.server-status {
  margin: 6px 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 18px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.status-indicator.running {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  color: white;
}

.status-indicator.stopped {
  background: linear-gradient(135deg, #6b7280 0%, #9ca3af 100%);
  color: white;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: white;
  animation: pulse 2s infinite;
  box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

.status-text {
  font-weight: 600;
  letter-spacing: 0.5px;
}

/* 历史记录按钮 */
.history-btn {
  margin-top: 15px;
  padding: 12px 28px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 16px;
  border: none;
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
  transition: all 0.3s ease;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.history-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
}

.history-btn:active {
  transform: translateY(0);
}

/* 按钮组 */
.button-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
  align-items: center;
  margin-top: 5px;
}

.action-btn {
  padding: 12px 32px !important;
  border: 2px solid #bfdbfe !important;
  border-radius: 20px !important;
  background: white !important;
  color: #64748b !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  cursor: pointer !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
  position: relative !important;
  overflow: hidden !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 6px !important;
  width: auto !important;
}

.action-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.1), transparent);
  transition: left 0.5s ease;
}

.action-btn:hover::before {
  left: 100%;
}

.action-btn:hover {
  border-color: #38bdf8 !important;
  color: #0284c7 !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(56, 189, 248, 0.2) !important;
}

.action-btn:active {
  transform: translateY(0);
}

.action-btn :deep(.el-button) {
  background: transparent !important;
  border: none !important;
}

.btn-icon {
  font-size: 18px;
}

.history-btn :deep(.el-button) {
  background: transparent;
  border: none;
}

/* 天数选择器 */
.day-selector {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 5px;
}

.day-btn {
  padding: 12px 32px;
  border: 2px solid #bfdbfe;
  border-radius: 20px;
  background: white;
  color: #64748b;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

.day-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.1), transparent);
  transition: left 0.5s ease;
}

.day-btn:hover::before {
  left: 100%;
}

.day-btn:hover {
  border-color: #38bdf8;
  color: #0284c7;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(56, 189, 248, 0.2);
}

.day-btn.active {
  background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
  border-color: #38bdf8;
  color: white;
  box-shadow: 0 4px 15px rgba(56, 189, 248, 0.4);
}

.day-btn:active {
  transform: translateY(0);
}

/* 参数选择行 */
.params-row {
  margin-bottom: 32px;
  position: relative;
  z-index: 1;
}

.params-row :deep(.el-card) {
  border: none;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}

.params-row :deep(.el-card__body) {
  padding: 20px 28px;
}

.param-item {
  display: flex;
  align-items: center;
  gap: 20px;
}

.param-item label {
  font-size: 15px;
  color: #2d3748;
  font-weight: 600;
}

.param-item :deep(.el-radio-group) {
  display: flex;
  gap: 12px;
}

.param-item :deep(.el-radio) {
  margin-right: 0;
}

.param-item :deep(.el-radio__label) {
  font-weight: 500;
  color: #4a5568;
}

.param-item :deep(.el-radio__input.is-checked + .el-radio__label) {
  color: #4facfe;
}

.param-item :deep(.el-radio__input.is-checked .el-radio__inner) {
  background-color: #4facfe;
  border-color: #4facfe;
}

/* 图表卡片 */
.charts-container {
  position: relative;
  z-index: 1;
}

.chart-card {
  width: 100%;
  margin-bottom: 24px;
}

.chart-card :deep(.el-card) {
  border: none;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}

.chart-card :deep(.el-card__header) {
  padding: 20px 28px;
  border-bottom: 2px solid #e2e8f0;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
}

.chart-card {
  width: 100%;
  margin-bottom: 24px;
  min-height: 630px;
}

.chart-card :deep(.el-card) {
  border: none;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  min-height: 630px;
  display: flex;
  flex-direction: column;
}

.chart-card :deep(.el-card__body) {
  padding: 28px;
  flex: 1;
}

.chart-title {
  font-size: 18px;
  font-weight: 700;
  color: #2d3748;
  letter-spacing: 0.3px;
}

.chart-wrapper-large {
  width: 100%;
  height: 550px;
  border-radius: 8px;
  overflow: hidden;
}

/* 暂无数据 */
.no-data-card {
  width: 100%;
  min-height: 630px;
}

.no-data-card :deep(.el-card) {
  border: none;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  min-height: 630px;
  display: flex;
  flex-direction: column;
}

.no-data-card :deep(.el-card__body) {
  padding: 28px;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.no-data {
  text-align: center;
  color: #a0aec0;
  font-size: 18px;
  font-weight: 600;
  position: relative;
}

.no-data::before {
  content: '📊';
  display: block;
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .home-container {
    padding: 16px;
  }

  .stats-row {
    grid-template-columns: 1fr;
    gap: 16px;
    margin-bottom: 24px;
  }

  .stat-card :deep(.el-card__body) {
    padding: 24px 20px;
  }

  .stat-label {
    font-size: 18px;
  }

  .stat-value {
    font-size: 28px;
  }

  .circle-progress {
    width: 160px;
    height: 160px;
  }

  .circle-value {
    font-size: 48px;
  }

  .circle-total {
    font-size: 18px;
  }

  .chart-wrapper-large {
    height: 350px;
  }

  .params-row :deep(.el-card__body) {
    padding: 16px 20px;
  }

  .param-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .stat-card:nth-child(2) .stat-value {
    font-size: 16px;
  }

  .refresh-countdown {
    font-size: 12px;
    padding: 8px 14px;
  }

  .chart-title {
    font-size: 16px;
  }
}

/* 导出对话框样式 */
.export-dialog-content {
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.date-range-label {
  font-size: 15px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 12px;
  text-align: center;
  width: 100%;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.dialog-footer .el-button {
  padding: 10px 24px;
  border-radius: 8px;
  font-weight: 600;
}

</style>


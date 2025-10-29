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
              <div class="status-indicator" :class="serverStatus" @click="showLogsDialog" style="cursor: pointer;">
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
        <template #default>
          <div class="button-group">
            <el-button type="info" class="action-btn" @click="handleChangelogClick">
              <span class="btn-icon">📝</span>
              更新日志
            </el-button>
            <el-button type="success" class="action-btn" @click="handleExportData">
              <span class="btn-icon">📥</span>
              导出数据
            </el-button>
            <el-button type="primary" class="action-btn" @click="handleHistoryClick">
              <span class="btn-icon">📋</span>
              查看历史记录
            </el-button>
          </div>
        </template>
      </el-card>
    </div>

    <!-- 设备实时电压状态卡片 -->
    <el-card class="voltage-status-card">
      <template #header>
        <div class="voltage-status-header">
          <span class="voltage-status-title">设备实时电压状态</span>
          <span class="voltage-status-subtitle">（绿色：运行中 | 灰色：停止）</span>
        </div>
      </template>
      <template #default>
        <div class="devices-grid">
          <div
              v-for="device in allDevicesStatus"
              :key="device.machine_name"
              class="device-item"
              :class="{ 'running': device.isRunning, 'stopped': !device.isRunning }"
              @click="handleDeviceClick(device.machine_name)"
          >
            <div class="device-status-dot" :class="{ 'running': device.isRunning, 'stopped': !device.isRunning }"></div>
            <div class="device-name">{{ device.machine_name }}</div>
            <div class="device-voltage">
              <span class="voltage-value">{{ device.voltage }}</span>
              <span class="voltage-unit">mV</span>
            </div>
          </div>
        </div>
      </template>
    </el-card>

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

    <!-- 日志对话框 -->
    <el-dialog
        v-model="logsDialogVisible"
        title="系统日志"
        width="80%"
        :close-on-click-modal="false"
    >
      <div class="logs-dialog-content">
        <div class="logs-container" ref="logsContainerRef">
          <div
              v-for="(log, index) in systemLogs"
              :key="index"
              class="log-line"
              :class="{'log-error': log.includes('[错误]'), 'log-warning': log.includes('[警告]'), 'log-success': log.includes('[成功]')}"
          >
            {{ log }}
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="systemLogs = []">清除日志</el-button>
          <el-button type="primary" @click="closeLogsDialog">关闭</el-button>
        </div>
      </template>
    </el-dialog>

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

    <!-- 更新日志对话框 -->
    <el-dialog
        v-model="changelogDialogVisible"
        title="更新日志"
        width="700px"
        :close-on-click-modal="false"
    >
      <div class="changelog-dialog-content">
        <div
            v-for="(log, index) in changelogData"
            :key="index"
            class="changelog-item"
        >
          <div class="changelog-header">
            <div class="changelog-version">{{ log.version }}</div>
            <div class="changelog-date">{{ log.date }}</div>
          </div>
          <div class="changelog-content">
            <div
                v-for="(item, idx) in log.changes"
                :key="idx"
                class="changelog-change"
            >
              <span class="changelog-icon">•</span>
              <span class="changelog-text">{{ item }}</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="changelogDialogVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 设备详细图表对话框 -->
    <el-dialog
        v-model="deviceChartDialogVisible"
        :title="`${selectedDeviceName} 电压趋势图`"
        width="85%"
        :close-on-click-modal="false"
        align-center
        destroy-on-close
        top="5vh"
    >
      <div class="device-chart-container">
        <div id="device-detail-chart" class="device-detail-chart"></div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="deviceChartDialogVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import {ref, computed, onMounted, onUnmounted, watch, nextTick} from 'vue'
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

// 从localStorage加载上次选择的天数，如果没有则默认为1
const loadSelectedDay = (): number => {
  const saved = localStorage.getItem('selectedDay')
  if (saved) {
    const day = parseInt(saved)
    return [1, 7].includes(day) ? day : 1
  }
  return 1
}

const selectedDay = ref(loadSelectedDay())
const queryTime = ref('')
const devicesData = ref<Device[]>([])
const chartsMap = new Map<string, Highcharts.Chart>()
const refreshCountdown = ref(300)
const serverStatus = ref<'running' | 'stopped'>('stopped') // 默认为未运行
let refreshInterval: ReturnType<typeof setInterval> | null = null
let countdownInterval: ReturnType<typeof setInterval> | null = null


const devicesWithData = computed(() => {
  return devicesData.value.filter(device => device.voltage_data.length > 0)
})

// 计算所有15个设备的实时状态
const allDevicesStatus = computed(() => {
  const result = []

  for (let i = 1; i <= 15; i++) {
    const machineName = `${i}#`
    const device = devicesData.value.find(d => d.machine_name === machineName)

    let voltage = 0
    let isRunning = false

    if (device && device.voltage_data.length > 0) {
      // 获取最后一条数据
      const lastData = device.voltage_data[device.voltage_data.length - 1]
      const lastDataTime = new Date(`${lastData.date} ${lastData.time}`).getTime()
      const queryTimeMs = new Date(queryTime.value).getTime()

      // 计算时间差（毫秒）
      const timeDiff = queryTimeMs - lastDataTime
      const halfHourMs = 30 * 60 * 1000 // 30分钟的毫秒数

      // 如果最近一次数据在半小时内
      if (timeDiff <= halfHourMs) {
        voltage = Math.round(lastData.avg_voltage)
        // 只要电压不是0就算运行中
        isRunning = voltage !== 0
      } else {
        // 超过半小时，电压显示为0，状态为未运行
        voltage = 0
        isRunning = false
      }
    }

    result.push({
      machine_name: machineName,
      voltage: voltage,
      isRunning: isRunning
    })
  }

  return result
})

// 计算运行中的设备数量（从卡片状态中统计）
const runningDevicesCount = computed(() => {
  return allDevicesStatus.value.filter(device => device.isRunning).length
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

// 日志对话框相关
const logsDialogVisible = ref(false)
const logsContainerRef = ref<HTMLElement | null>(null)
const systemLogs = ref<string[]>([])
let logsRefreshInterval: ReturnType<typeof setInterval> | null = null

// 自动滚动到日志底部
const scrollLogsToBottom = async () => {
  // 使用 nextTick 确保 DOM 已更新
  await nextTick()
  if (logsContainerRef.value) {
    logsContainerRef.value.scrollTop = logsContainerRef.value.scrollHeight
  }
}

// 记录上次最后一条日志内容
let lastLogContent = ''

// 监听 systemLogs 变化，通过比较最后一条日志内容来判断是否有新日志
watch(systemLogs, (newLogs) => {
  // 获取当前最后一条日志内容
  const currentLastLog = newLogs.length > 0 ? newLogs[newLogs.length - 1] : ''

  // 如果最后一条日志内容与上次不同，说明有新日志，需要滚动到底部
  if (currentLastLog && currentLastLog !== lastLogContent) {
    console.log(`[日志] 检测到新日志，自动滚动到底部`)
    console.log(`[日志] 最新日志: ${currentLastLog.substring(0, 80)}...`)
    scrollLogsToBottom()
  }

  // 更新记录的最后一条日志内容
  lastLogContent = currentLastLog
})

// 获取MQTT日志
const fetchMqttLogs = async () => {
  try {
    const response = await axios.get('/api/mqtt/logs')
    // 将日志对象数组转换为格式化的字符串数组
    systemLogs.value = response.data.logs.map((log: any) => {
      return `[${log.timestamp}] [${log.level}] ${log.message}`
    })
  } catch (error) {
    console.error('获取MQTT日志失败:', error)
    systemLogs.value = ['[系统] 获取日志失败']
  }
}

// 显示日志对话框
const showLogsDialog = () => {
  fetchMqttLogs() // 打开对话框时刷新日志
  logsDialogVisible.value = true

  // 打开对话框后，每2秒自动刷新一次日志
  if (logsRefreshInterval) {
    clearInterval(logsRefreshInterval)
  }
  logsRefreshInterval = setInterval(() => {
    if (logsDialogVisible.value) {
      fetchMqttLogs()
    }
  }, 2000)
}

// 关闭日志对话框时停止自动刷新
const closeLogsDialog = () => {
  logsDialogVisible.value = false
  if (logsRefreshInterval) {
    clearInterval(logsRefreshInterval)
    logsRefreshInterval = null
  }
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

// 更新日志相关
const changelogDialogVisible = ref(false)

// 设备详细图表对话框相关
const deviceChartDialogVisible = ref(false)
const selectedDeviceName = ref('')
let deviceDetailChart: Highcharts.Chart | null = null

// 更新日志数据（本地数据）
const changelogData = [
  {
    version: 'v1.0.0',
    date: '2025-10-27',
    changes: [
      '新增主页看板, 显示当前所有设备的运行状态,每5分钟自动刷新数据',
      '新增更新日志功能, 可查看系统历史更新记录',
      '所有数据查看迁移至历史记录页面, 优化主页面布局',
      '新增数据导出功能, 可选择时间范围(默认一个月)导出所有设备的数据为CSV文件',
      '新增MQTT中转服务器状态显示, 实时查看服务器连接状态及日志',
    ]
  },
]

// 处理更新日志按钮点击
const handleChangelogClick = () => {
  changelogDialogVisible.value = true
}

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
    const blob = new Blob([response.data], {type: 'text/csv;charset=utf-8;'})
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
  // 保存到localStorage
  localStorage.setItem('selectedDay', day.toString())
  fetchOverviewData()
}

// 处理设备卡片点击
const handleDeviceClick = (machineName: string) => {
  selectedDeviceName.value = machineName
  deviceChartDialogVisible.value = true

  // 使用nextTick确保dialog渲染完成后再创建图表
  nextTick(() => {
    createDeviceDetailChart(machineName)
  })
}

// 创建设备详细图表
const createDeviceDetailChart = (machineName: string) => {
  // 查找该设备的数据
  const device = devicesData.value.find(d => d.machine_name === machineName)

  if (!device || device.voltage_data.length === 0) {
    ElMessage.warning('该设备暂无数据')
    return
  }

  const chartElement = document.getElementById('device-detail-chart')
  if (!chartElement) return

  // 销毁旧图表实例
  if (deviceDetailChart) {
    deviceDetailChart.destroy()
    deviceDetailChart = null
  }

  // 准备数据
  const data: [number, number][] = []
  device.voltage_data.forEach(d => {
    const timePoint = `${d.date} ${d.time}`
    const timestamp = new Date(timePoint).getTime()
    data.push([timestamp, d.avg_voltage])
  })

  // 按时间戳排序
  data.sort((a, b) => a[0] - b[0])

  // 获取设备在总览图中的颜色
  const colors = [
    '#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD',
    '#8C564B', '#E377C2', '#7F7F7F', '#BCBD22', '#17BECF',
    '#FFA600', '#FF0054', '#00CC96', '#AB63FA', '#19D3F3'
  ]

  // 找到设备在devicesWithData中的索引，以获取对应的颜色
  const deviceIndex = devicesWithData.value.findIndex(d => d.machine_name === machineName)
  const deviceColor = colors[deviceIndex % colors.length]

  // 计算最大时间戳
  let maxDataTimestamp = 0
  if (data.length > 0) {
    maxDataTimestamp = data[data.length - 1][0]
  }

  // 获取 queryTime 的时间戳
  const queryTimestamp = new Date(queryTime.value).getTime()
  const xAxisMax = maxDataTimestamp < queryTimestamp ? queryTimestamp : undefined

  // 创建图表
  deviceDetailChart = Highcharts.chart('device-detail-chart', {
    time: {
      useUTC: false
    },
    chart: {
      type: 'line' as const,
      height: 600,
      marginBottom: 100,
      marginTop: 80,
      spacingBottom: 15,
      spacingRight: 15,
      spacingLeft: 15,
      spacingTop: 10
    },
    title: {
      text: `${machineName} 电压趋势`,
      style: {
        fontSize: '22px',
        fontWeight: 'bold',
        color: '#1e293b'
      }
    },
    subtitle: {
      text: `数据点数: ${data.length} | 时间范围: ${selectedDay.value === 1 ? '最近1天' : '最近7天'}`,
      style: {
        fontSize: '14px',
        color: '#64748b'
      }
    },
    xAxis: {
      type: 'datetime',
      title: {
        text: '时间',
        style: {
          fontSize: '16px',
          fontWeight: '600',
          color: '#334155'
        },
        margin: 20
      },
      max: xAxisMax,
      labels: {
        rotation: 0,
        align: 'center',
        useHTML: true,
        style: {
          fontSize: '13px'
        },
        y: 35,
        formatter: function (this: any): string {
          const date = new Date(this.value)
          const month = String(date.getMonth() + 1).padStart(2, '0')
          const day = String(date.getDate()).padStart(2, '0')
          const hours = String(date.getHours()).padStart(2, '0')
          const minutes = String(date.getMinutes()).padStart(2, '0')

          return '<div style="text-align: center;">' +
              '<div style="color: #666; font-size: 13px; font-weight: 600;">' + month + '-' + day + '</div>' +
              '<div style="color: #333; font-size: 14px; font-weight: 700; margin-top: 2px;">' + hours + ':' + minutes + '</div>' +
              '</div>'
        }
      },
      gridLineWidth: 1,
      gridLineColor: '#f1f5f9'
    },
    yAxis: {
      title: {
        text: '平均电压值 (mV)',
        style: {
          fontSize: '16px',
          fontWeight: '600',
          color: '#334155'
        }
      },
      min: 0,
      labels: {
        style: {
          fontSize: '13px',
          color: '#64748b'
        }
      },
      gridLineWidth: 1,
      gridLineColor: '#f1f5f9'
    },
    tooltip: {
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

        let s = '<div style="color: #333; font-weight: 700; margin-bottom: 8px; font-size: 14px;">' + formattedTime + '</div>'
        s += '<div style="margin: 4px 0; color: #333; font-weight: 500; font-size: 14px;">' +
            '<span style="color: ' + deviceColor + '; font-weight: 700; margin-right: 6px;">●</span>' +
            '<span style="color: ' + deviceColor + '; font-weight: 700;">电压: ' + this.y.toFixed(0) + ' mV</span></div>'

        return s
      }
    } as any,
    legend: {
      enabled: true,
      layout: 'horizontal',
      align: 'center',
      verticalAlign: 'top',
      y: 10,
      itemStyle: {
        fontSize: '14px',
        fontWeight: '600',
        color: '#334155'
      }
    },
    series: [{
      name: `${machineName} - 电压`,
      data: data,
      color: deviceColor,
      type: 'line' as const,
      lineWidth: 3,
      marker: {
        enabled: false,
        radius: 3,
        symbol: 'circle'
      },
      states: {
        hover: {
          lineWidthPlus: 2
        }
      },
      dataLabels: {
        enabled: false
      }
    }],
    credits: {
      enabled: false
    },
    responsive: {
      rules: [
        {
          condition: {
            maxWidth: 1400
          },
          chartOptions: {
            chart: {
              height: 550,
              marginBottom: 90
            },
            title: {
              style: {
                fontSize: '20px'
              }
            },
            xAxis: {
              labels: {
                y: 30,
                style: {
                  fontSize: '12px'
                }
              }
            }
          }
        },
        {
          condition: {
            maxWidth: 800
          },
          chartOptions: {
            chart: {
              height: 450,
              marginBottom: 80
            },
            title: {
              style: {
                fontSize: '18px'
              }
            },
            subtitle: {
              style: {
                fontSize: '12px'
              }
            },
            xAxis: {
              labels: {
                rotation: -30,
                align: 'right',
                y: 20,
                style: {
                  fontSize: '11px'
                }
              }
            }
          }
        },
        {
          condition: {
            maxWidth: 500
          },
          chartOptions: {
            chart: {
              height: 350,
              marginBottom: 70
            },
            title: {
              style: {
                fontSize: '16px'
              }
            },
            xAxis: {
              labels: {
                rotation: -45,
                align: 'right',
                y: 15,
                style: {
                  fontSize: '10px'
                }
              }
            }
          }
        }
      ]
    }
  } as any)

  console.log('图表创建完成')
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

  // 为每个设备创建数据系列，颜色自动分配
  const colors = [
    '#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD',
    '#8C564B', '#E377C2', '#7F7F7F', '#BCBD22', '#17BECF',
    '#FFA600', '#FF0054', '#00CC96', '#AB63FA', '#19D3F3'
  ];

  const series = devicesWithData.value.map((device, index) => {
    // 为当前设备创建数据序列，只添加有实际数据的点
    const data: [number, number][] = []

    device.voltage_data.forEach(d => {
      const timePoint = `${d.date} ${d.time}`
      const timestamp = new Date(timePoint).getTime()
      data.push([timestamp, d.avg_voltage])
    })

    // 按时间戳排序，确保数据点按时间顺序连接
    data.sort((a, b) => a[0] - b[0])

    return {
      name: device.machine_name,
      data: data,
      color: colors[index % colors.length],
      type: 'line' as const,
      marker: {
        enabled: false
      },
      connectNulls: false  // 确保不连接缺失的数据点
    }
  })

  // 计算所有数据的最大时间戳
  let maxDataTimestamp = 0
  series.forEach(s => {
    if (s.data.length > 0) {
      const lastPoint = s.data[s.data.length - 1]
      if (lastPoint[0] > maxDataTimestamp) {
        maxDataTimestamp = lastPoint[0]
      }
    }
  })

  // 获取 queryTime 的时间戳
  const queryTimestamp = new Date(queryTime.value).getTime()

  // 如果数据的最大时间小于 queryTime，则将 x 轴扩展到 queryTime
  const xAxisMax = maxDataTimestamp < queryTimestamp ? queryTimestamp : undefined

  // 创建合并图表
  const newChart = Highcharts.chart(chartId, {
    time: {
      useUTC: false
    },
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
      max: xAxisMax,  // 设置 x 轴最大值，如果数据时间小于 queryTime，则扩展到 queryTime
      labels: {
        rotation: 0,
        align: 'center',
        useHTML: true,
        formatter: function (this: any): string {
          const date = new Date(this.value)
          const month = String(date.getMonth() + 1).padStart(2, '0')
          const day = String(date.getDate()).padStart(2, '0')
          const hours = String(date.getHours()).padStart(2, '0')
          const minutes = String(date.getMinutes()).padStart(2, '0')

          // 日期和时间分行显示，使用不同的样式
          return '<div style="text-align: center;">' +
              '<div style="color: #666; font-size: 11px; font-weight: 600;">' + month + '-' + day + '</div>' +
              '<div style="color: #333; font-size: 12px; font-weight: 700; margin-top: 2px;">' + hours + ':' + minutes + '</div>' +
              '</div>'
        }
      },
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
                '<span style="color: ' + point.color + '; font-weight: 700;">' + point.series.name + ': ' + point.y.toFixed(0) + ' mV</span></div>'
          }
        })

        return s
      }
    } as any,
    legend: {
      enabled: true,
      layout: 'horizontal',
      align: 'center',
      verticalAlign: 'bottom',
      itemStyle: {
        fontSize: '14px',
        fontWeight: '500',
        cursor: 'pointer'
      },
      itemHoverStyle: {
        color: '#000'
      },
      symbolWidth: 30,
      symbolHeight: 16,
      symbolRadius: 8,
      itemDistance: 20,
      padding: 15,
      itemMarginTop: 8,
      itemMarginBottom: 8
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
              verticalAlign: 'bottom',
              itemStyle: {
                fontSize: '13px',
                fontWeight: '500'
              },
              symbolWidth: 25,
              symbolHeight: 14,
              itemDistance: 15
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
  // 清理日志刷新定时器
  if (logsRefreshInterval) {
    clearInterval(logsRefreshInterval)
    logsRefreshInterval = null
  }
  // 清理设备详细图表
  if (deviceDetailChart) {
    deviceDetailChart.destroy()
    deviceDetailChart = null
  }
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
  margin-left: 0 !important;
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

/* 设备实时电压状态卡片样式 */
.voltage-status-card {
  margin-bottom: 32px;
  position: relative;
  z-index: 1;
}

.voltage-status-card :deep(.el-card) {
  border: none;
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}

.voltage-status-card :deep(.el-card__header) {
  padding: 20px 28px;
  border-bottom: 2px solid #e2e8f0;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
}

.voltage-status-card :deep(.el-card__body) {
  padding: 28px;
}

.voltage-status-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.voltage-status-title {
  font-size: 20px;
  font-weight: 700;
  color: #0284c7;
  letter-spacing: 0.5px;
}

.voltage-status-subtitle {
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
}

/* 设备网格布局 - 一行8个 */
.devices-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 16px;
  padding: 8px 0;
}

/* 设备项 */
.device-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 16px;
  border-radius: 12px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

.device-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: #e2e8f0;
  transition: all 0.3s ease;
}

.device-item.running::before {
  background: linear-gradient(90deg, #10b981 0%, #34d399 100%);
}

.device-item.stopped::before {
  background: #9ca3af;
}

.device-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  border-color: #0ea5e9;
}

.device-item:active {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.device-item.running {
  border-color: #10b981;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
}

.device-item.stopped {
  border-color: #d1d5db;
  background: #f9fafb;
}

/* 设备状态圆点 */
.device-status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-bottom: 12px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.device-status-dot.running {
  background: #10b981;
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.6), 0 2px 8px rgba(16, 185, 129, 0.4);
  animation: pulse-dot 2s infinite;
}

.device-status-dot.stopped {
  background: #9ca3af;
  box-shadow: 0 2px 8px rgba(107, 114, 128, 0.3);
}

@keyframes pulse-dot {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.6), 0 2px 8px rgba(16, 185, 129, 0.4);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.3);
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.8), 0 2px 12px rgba(16, 185, 129, 0.6);
  }
}

/* 设备名称 */
.device-name {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

/* 设备电压 */
.device-voltage {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.voltage-value {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.5px;
}

.device-item.running .voltage-value {
  color: #059669;
}

.device-item.stopped .voltage-value {
  color: #6b7280;
}

.voltage-unit {
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
}

/* 响应式布局 */
@media (max-width: 1600px) {
  .devices-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}

@media (max-width: 1200px) {
  .devices-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 768px) {
  .devices-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }

  .device-item {
    padding: 12px 8px;
  }

  .voltage-status-title {
    font-size: 18px;
  }

  .voltage-status-subtitle {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .devices-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 日志对话框样式 */
.logs-dialog-content {
  padding: 12px 0;
}

.logs-container {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #1a1a2e;
  padding: 12px;
  max-height: 70vh;
  height: 500px;
  overflow-y: auto;
  font-family: 'Courier New', 'Monaco', monospace;
  font-size: 13px;
}

.log-line {
  color: #d1d5db;
  padding: 6px 8px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  border-left: 3px solid transparent;
  margin-bottom: 4px;
}

.log-line:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.log-error {
  color: #f87171;
  border-left-color: #ef4444;
}

.log-warning {
  color: #fbbf24;
  border-left-color: #f59e0b;
}

.log-success {
  color: #86efac;
  border-left-color: #22c55e;
}

.logs-container::-webkit-scrollbar {
  width: 6px;
}

.logs-container::-webkit-scrollbar-track {
  background: #2a2a3e;
  border-radius: 3px;
}

.logs-container::-webkit-scrollbar-thumb {
  background: #4a4a6a;
  border-radius: 3px;
}

.logs-container::-webkit-scrollbar-thumb:hover {
  background: #5a5a7a;
}

.status-indicator:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

/* 更新日志对话框样式 */
.changelog-dialog-content {
  padding: 12px 0;
  max-height: 500px;
  overflow-y: auto;
  overflow-x: hidden;
}

.changelog-item {
  margin-bottom: 24px;
  padding: 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border-left: 4px solid #0ea5e9;
  transition: all 0.3s ease;
}

.changelog-item:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.changelog-item:last-child {
  margin-bottom: 0;
}

.changelog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e2e8f0;
}

.changelog-version {
  font-size: 18px;
  font-weight: 700;
  color: #0284c7;
  letter-spacing: 0.5px;
}

.changelog-date {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  background: white;
  padding: 4px 12px;
  border-radius: 12px;
}

.changelog-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.changelog-change {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: #334155;
  font-size: 14px;
  line-height: 1.6;
}

.changelog-icon {
  color: #0ea5e9;
  font-size: 20px;
  font-weight: 700;
  margin-top: -2px;
}

.changelog-text {
  flex: 1;
  color: #475569;
  font-weight: 500;
}

.changelog-dialog-content::-webkit-scrollbar {
  width: 6px;
}

.changelog-dialog-content::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.changelog-dialog-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.changelog-dialog-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 导出对话框样式 */
.export-dialog-content {
  padding: 20px 10px;
}

.date-range-label {
  font-size: 15px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 12px;
}

/* 设备详细图表对话框样式 */
.device-chart-container {
  width: 100%;
  height: auto;
  padding: 15px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  box-sizing: border-box;
}

.device-detail-chart {
  width: 100%;
  max-width: 100%;
  height: auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: visible;
  box-sizing: border-box;
}

/* 确保dialog body不溢出 */
:deep(.el-dialog__body) {
  padding: 20px;
  overflow-x: hidden;
  overflow-y: auto;
  max-height: 75vh;
  box-sizing: border-box;
}

:deep(.el-dialog__footer) {
  padding: 15px 20px;
  border-top: 1px solid #e5e7eb;
}

:deep(.el-dialog) {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

:deep(.el-dialog__header) {
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}
</style>


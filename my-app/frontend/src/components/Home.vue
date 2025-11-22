<template>
  <div
      class="h-[90vh] flex flex-col bg-background text-slate-600 antialiased font-sans overflow-hidden"
  >
    <!-- 1. 顶部导航 -->
    <nav
        class="bg-surface sticky top-0 z-50 border-b border-slate-200 px-6 py-4 shadow-sm backdrop-blur-md bg-white/90"
    >
      <div class="max-w-8xl mx-auto flex justify-between items-center">
        <!-- 左侧区域：包含 Logo、标题 和 服务器状态 -->
        <div class="flex items-center gap-6">
          <div class="flex items-center gap-3">
            <div
                class="w-10 h-10 bg-blue-600 text-white rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/30"
            >
              <svg
                  class="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
              >
                <path
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1"
                ></path>
              </svg>
            </div>
            <div>
              <h1 class="text-xl font-bold text-slate-800 tracking-tight">
                电解槽电压监控中心
              </h1>
              <p class="text-xs text-slate-500 font-medium">
                实时数据流 (mV) | 自动刷新
              </p>
            </div>
          </div>

          <!-- 服务器状态展示符号 -->
          <div
              class="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-emerald-50/80 border border-emerald-100 rounded-full shadow-sm transition-all hover:bg-emerald-50 cursor-pointer"
              title="点击查看日志"
              @click="showLogsDialog"
          >
            <span class="relative flex h-2.5 w-2.5">
              <span
                  :class="serverStatus ? 'bg-emerald-400' : 'bg-red-400'"
                  class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
              ></span>
              <span
                  :class="serverStatus ? 'bg-emerald-500' : 'bg-red-500'"
                  class="relative inline-flex rounded-full h-2.5 w-2.5"
              ></span>
            </span>
            <span
                :class="serverStatus ? 'text-emerald-700' : 'text-red-700'"
                class="text-xs font-semibold"
            >
              {{ serverStatus ? "MQTT服务器正常" : "MQTT连接断开" }}
            </span>
            <div v-if="serverStatus" class="w-px h-3 bg-emerald-200 mx-1"></div>
            <span
                v-if="serverStatus"
                class="text-[10px] font-mono text-emerald-600/80"
            >{{ latency }}ms</span
            >
          </div>
        </div>

        <div class="flex items-center gap-6">
          <div class="hidden md:flex gap-6 text-sm">
            <div class="flex flex-col items-end">
              <span class="text-xs text-slate-400">正常运转</span>
              <span class="font-bold text-emerald-600"
              >{{ runningCount }} 台</span
              >
            </div>
            <div class="flex flex-col items-end">
              <span class="text-xs text-slate-400">异常警报</span>
              <span
                  :class="warningCount > 0 ? 'text-red-500' : 'text-slate-400'"
                  class="font-bold"
              >{{ warningCount }} 台</span
              >
            </div>
            <div class="flex flex-col items-end">
              <span class="text-xs text-slate-400">停止状态</span>
              <span class="font-bold text-slate-400"
              >{{ stoppedCount }} 台</span
              >
            </div>
          </div>
          <div class="flex items-center gap-3">
            <button
                :disabled="loading"
                class="bg-white border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-200 px-4 py-2 rounded-lg text-sm font-medium shadow-sm transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                @click="refreshAll"
            >
              {{ loading ? "刷新中..." : "立即刷新" }}
            </button>
            <div
                class="flex items-center gap-2 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg"
            >
              <svg
                  class="w-4 h-4 text-slate-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
              >
                <path
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                ></path>
              </svg>
              <span class="text-sm font-mono text-slate-600 font-medium">{{
                  countdownDisplay
                }}</span>
            </div>
          </div>

          <!-- 其他操作下拉菜单 -->
          <div class="relative group">
            <button
                class="bg-slate-100 border border-slate-200 text-slate-600 hover:bg-slate-200 px-4 py-2 rounded-lg text-sm font-medium shadow-sm transition-all flex items-center gap-2"
            >
              <span>其他操作</span>
              <svg
                  class="w-4 h-4 transition-transform group-hover:rotate-180"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
              >
                <path
                    d="M19 9l-7 7-7-7"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                ></path>
              </svg>
            </button>
            <!-- 下拉内容 -->
            <div
                class="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-slate-100 overflow-hidden transition-all opacity-0 invisible group-hover:opacity-100 group-hover:visible translate-y-2 group-hover:translate-y-0 z-50"
            >
              <div class="py-1">
                <a
                    class="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 hover:text-blue-600 cursor-pointer flex items-center gap-2"
                    @click="handleChangelogClick"
                >
                  <span>📝</span> 更新日志
                </a>
                <a
                    class="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 hover:text-blue-600 cursor-pointer flex items-center gap-2"
                    @click="handleExportData"
                >
                  <span>📥</span> 导出数据
                </a>
                <a
                    class="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 hover:text-blue-600 cursor-pointer flex items-center gap-2"
                    @click="handleHistoryClick"
                >
                  <span>📋</span> 历史数据
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- 2. 主要内容区域 -->
    <main class="flex-1 p-6 max-w-8xl mx-auto w-full overflow-y-auto">
      <div class="flex justify-between items-end mb-6">
        <h2 class="text-lg font-bold text-slate-700">电解槽列表(15)</h2>
        <span class="text-xs font-mono text-slate-400">
          当前时间: {{ currentTime }}
        </span>
      </div>

      <!-- 网格布局 -->
      <div class="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-5 gap-6">
        <div
            v-for="device in devices"
            :key="device.id"
            :class="[
            device.isWarning
              ? 'shadow-[0_8px_30px_-4px_rgba(239,68,68,0.2)] ring-1 ring-red-200'
              : 'shadow-sm hover:shadow-xl hover:shadow-blue-500/5 hover:-translate-y-1',
          ]"
            class="bg-white rounded-2xl border border-slate-100 p-5 flex flex-col justify-between transition-all duration-300 group relative overflow-hidden h-48 cursor-pointer"
            @click="handleDeviceClick(device)"
        >
          <!-- 异常状态下的顶部红条 -->
          <div
              v-if="device.isWarning"
              class="absolute top-0 left-0 w-full h-1.5 bg-red-500 z-10"
          ></div>

          <!-- 卡片上半部分：信息 (增加 z-index 确保文字浮在图表之上) -->
          <div class="relative z-20">
            <div class="flex justify-between items-start mb-2">
              <div class="flex flex-col">
                <span
                    class="text-xs font-bold text-slate-400 uppercase tracking-wider"
                >{{ device.id }}</span
                >
                <span
                    :title="device.model"
                    class="text-sm font-semibold text-slate-700 truncate w-24"
                >{{ device.model }}</span
                >
              </div>
              <!-- 运行时长和状态指示灯 -->
              <div class="flex items-center gap-2">
                <!-- 运行时长显示 -->
                <div
                    v-if="!device.hoursLoading && (device.totalHours !== undefined || device.currentHours !== undefined)"
                    class="flex items-center gap-1 text-[10px] font-mono mr-1"
                >
                  <span class="text-slate-500">总|当前:</span>
                  <span class="font-semibold text-emerald-600">{{ device.totalHours?.toFixed(1) || '0.0' }}</span>
                  <span class="text-slate-400">|</span>
                  <span class="font-semibold text-blue-600">{{ device.currentHours?.toFixed(1) || '0.0' }}</span>
                  <span class="text-slate-400">(小时)</span>
                </div>
                <!-- Loading 状态 -->
                <div
                    v-else-if="device.hoursLoading"
                    class="flex items-center justify-center w-20 h-6 mr-1"
                >
                  <svg
                      class="animate-spin h-4 w-4 text-slate-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      xmlns="http://www.w3.org/2000/svg"
                  >
                    <circle
                        class="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        stroke-width="4"
                    ></circle>
                    <path
                        class="opacity-75"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        fill="currentColor"
                    ></path>
                  </svg>
                </div>
                <!-- 状态指示灯 -->
                <div
                    class="flex items-center gap-1.5 bg-slate-50/80 backdrop-blur-sm px-2 py-1 rounded-full border border-slate-100"
                >
                  <span
                      :class="getStatusColorClass(device)"
                      class="w-2 h-2 rounded-full"
                  ></span>
                  <span
                      :class="getStatusTextClass(device)"
                      class="text-[10px] font-medium"
                  >
                    {{ getStatusText(device) }}
                  </span>
                </div>
              </div>
            </div>

            <div class="flex items-baseline gap-1">
              <span
                  class="text-3xl font-bold tracking-tight text-slate-800 drop-shadow-sm"
              >
                {{ device.currentVoltage }}
              </span>
              <!-- 单位 mV -->
              <span class="text-xs font-medium text-slate-400">mV</span>
              <span
                  :class="device.trend >= 0 ? 'text-blue-500' : 'text-orange-500'"
                  class="ml-2 text-xs font-medium"
              >
                {{ device.trend > 0 ? "+" : "" }}{{ device.trend }}
              </span>
            </div>
          </div>

          <!-- 底部图表区域：h-36 -->
          <div
              class="absolute bottom-0 left-0 right-0 h-36 w-full pointer-events-none z-10"
          >
            <svg
                class="w-full h-full"
                preserveAspectRatio="none"
                viewBox="0 0 100 100"
            >
              <defs>
                <linearGradient
                    :id="'grad-light-' + device.id"
                    x1="0%"
                    x2="0%"
                    y1="0%"
                    y2="100%"
                >
                  <stop
                      :stop-color="device.isWarning ? '#ef4444' : '#3b82f6'"
                      offset="0%"
                      stop-opacity="0.25"
                  />
                  <stop
                      :stop-color="device.isWarning ? '#ef4444' : '#3b82f6'"
                      offset="100%"
                      stop-opacity="0.02"
                  />
                </linearGradient>
              </defs>

              <path
                  :d="getAreaPath(device.history)"
                  :fill="'url(#grad-light-' + device.id + ')'"
                  class="transition-all duration-300 ease-out"
              />

              <path
                  :d="getPolylinePath(device.history)"
                  :stroke="device.isWarning ? '#ef4444' : '#3b82f6'"
                  class="transition-all duration-300 ease-out"
                  fill="none"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1"
              />
            </svg>
          </div>
        </div>
      </div>

      <!-- 日志对话框 -->
      <el-dialog
          v-model="logsDialogVisible"
          align-center
          class="rounded-xl overflow-hidden"
          title="MQTT 系统日志"
          width="800px"
      >
        <div
            class="bg-slate-900 text-slate-300 p-4 rounded-lg h-[500px] overflow-y-auto font-mono text-xs"
        >
          <div
              v-for="(log, index) in systemLogs"
              :key="index"
              class="mb-1 border-b border-slate-800 pb-1 last:border-0 break-words whitespace-pre-wrap"
          >
            <span
                :class="{
                'text-red-400': log.includes('ERROR') || log.includes('错误'),
                'text-yellow-400':
                  log.includes('WARNING') || log.includes('警告'),
                'text-emerald-400':
                  log.includes('INFO') ||
                  log.includes('信息') ||
                  log.includes('成功'),
              }"
            >{{ log }}</span
            >
          </div>
          <div
              v-if="systemLogs.length === 0"
              class="text-center text-slate-500 mt-10"
          >
            暂无日志
          </div>
        </div>
      </el-dialog>

      <!-- 导出数据对话框 -->
      <el-dialog
          v-model="exportDialogVisible"
          :close-on-click-modal="false"
          align-center
          class="rounded-xl"
          title="导出数据"
          width="500px"
      >
        <div class="p-4">
          <div class="mb-2 text-sm font-medium text-slate-700">
            选择时间范围
          </div>
          <el-date-picker
              v-model="exportDateRange"
              end-placeholder="截止时间"
              format="YYYY-MM-DD HH:mm:ss"
              range-separator="至"
              start-placeholder="起始时间"
              style="width: 100%"
              type="datetimerange"
          />
        </div>
        <template #footer>
          <div class="flex justify-end gap-2">
            <el-button
                :disabled="exportLoading"
                @click="exportDialogVisible = false"
            >取消
            </el-button>
            <el-button
                :loading="exportLoading"
                type="primary"
                @click="confirmExport"
            >
              {{ exportLoading ? "导出中..." : "确认导出" }}
            </el-button>
          </div>
        </template>
      </el-dialog>

      <!-- 更新日志对话框 -->
      <el-dialog
          v-model="changelogDialogVisible"
          :close-on-click-modal="false"
          align-center
          class="rounded-xl"
          title="更新日志"
          width="700px"
      >
        <div class="h-[500px] overflow-y-auto p-4">
          <div
              v-for="(log, index) in sortedChangelogData"
              :key="index"
              class="mb-6 last:mb-0 border-b border-slate-100 pb-6 last:border-0 last:pb-0"
          >
            <div class="flex justify-between items-center mb-3">
              <div class="text-lg font-bold text-slate-800">
                {{ log.version }}
              </div>
              <div class="text-sm text-slate-400 font-mono">{{ log.date }}</div>
            </div>
            <div class="space-y-2">
              <div
                  v-for="(item, idx) in log.changes"
                  :key="idx"
                  class="flex items-start gap-2 text-sm text-slate-600"
              >
                <span class="text-blue-400 mt-1">•</span>
                <span>{{ item }}</span>
              </div>
            </div>
          </div>
        </div>
        <template #footer>
          <div class="flex justify-end">
            <el-button type="primary" @click="changelogDialogVisible = false"
            >关闭
            </el-button>
          </div>
        </template>
      </el-dialog>

      <!-- 设备详情图表对话框 -->
      <el-dialog
          v-model="deviceChartDialogVisible"
          :title="`${selectedDeviceName} 电压趋势详情`"
          align-center
          class="rounded-xl"
          destroy-on-close
          width="90%"
          @close="handleCloseChartDialog"
      >
        <div v-loading="detailLoading" class="flex flex-col gap-4 p-2">
          <!-- 天数选择器 -->
          <div class="flex justify-end gap-2">
            <button
                v-for="d in [1, 7, 15, 30]"
                :key="d"
                :class="
                detailDay === d
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              "
                class="px-3 py-1 rounded-md text-sm font-medium transition-colors"
                @click="changeDetailDay(d)"
            >
              最近{{ d }}天
            </button>
          </div>

          <!-- 图表容器 -->
          <div id="device-detail-chart" class="w-full h-[500px]"></div>
        </div>
      </el-dialog>
    </main>
  </div>
</template>

<script lang="ts" setup>
import {computed, nextTick, onMounted, onUnmounted, ref} from "vue";
import {useRouter} from "vue-router";
import axios from "axios";
import {ElMessage} from "element-plus";
import Highcharts from "highcharts";

const router = useRouter();

// 类型定义
interface VoltageData {
  date: string;
  time: string;
  avg_voltage: number;
}

interface BackendDevice {
  machine_name: string;
  machine_model?: string;
  voltage_data: VoltageData[];
}

interface OverviewResponse {
  query_time: string;
  devices: BackendDevice[];
  is_incremental?: boolean;
}

interface DeviceDisplay {
  id: string;
  model: string;
  currentVoltage: number;
  history: number[];
  isWarning: boolean;
  isRunning: boolean; // 为了区分 停止 vs 异常
  trend: number;
  totalHours?: number; // 总运行时长
  currentHours?: number; // 当前运行时长
  hoursLoading?: boolean; // 时长加载状态
}

interface HoursData {
  name: string;
  total_hours: number;
  current_hours: number;
  model: string | null;
  start_time: string | null;
}

// 状态
const devices = ref<DeviceDisplay[]>([]);
const currentTime = ref("");
const latency = ref(0);
const serverStatus = ref(false);
const loading = ref(false);
const logsDialogVisible = ref(false);
const systemLogs = ref<string[]>([]);
const warningCount = computed(
    () => devices.value.filter((d) => d.isWarning).length
);
const runningCount = computed(
    () => devices.value.filter((d) => d.isRunning && !d.isWarning).length
);
const stoppedCount = computed(
    () => devices.value.filter((d) => !d.isRunning && !d.isWarning).length
);
const lastQueryTime = ref<string>("");

// 定时器
let refreshInterval: ReturnType<typeof setInterval> | null = null;
let timeInterval: ReturnType<typeof setInterval> | null = null;
let countdownInterval: ReturnType<typeof setInterval> | null = null;
let hoursRefreshInterval: ReturnType<typeof setInterval> | null = null; // 运行时长刷新定时器
let hoursCountdownInterval: ReturnType<typeof setInterval> | null = null; // 运行时长倒计时定时器

// 倒计时（秒）
const countdown = ref(300); // 5分钟 = 300秒
const hoursCountdown = ref(3600); // 60分钟 = 3600秒

// 初始化空数据 (1-15号机)
const initDevices = () => {
  devices.value = Array.from({length: 15}, (_, i) => ({
    id: `${i + 1}#`,
    model: "",
    currentVoltage: 0,
    history: Array(120).fill(0), // 历史长度改为120
    isWarning: false,
    isRunning: false,
    trend: 0,
    totalHours: undefined,
    currentHours: undefined,
    hoursLoading: true, // 初始为加载状态
  }));
};

// 获取数据
const fetchOverviewData = async (isIncremental = false) => {
  loading.value = true;
  // const startTime = performance.now() // 移除延迟计算
  try {
    const params: any = {day: 1, isfake: 1};
    if (isIncremental && lastQueryTime.value) {
      params.last_query_time = lastQueryTime.value;
    }

    const response = await axios.get<OverviewResponse>("/api/home/overview", {
      params,
    });

    // latency.value = Math.round(performance.now() - startTime) // 移除延迟计算

    // 更新时间
    if (response.data.query_time) {
      lastQueryTime.value = response.data.query_time;
      currentTime.value = new Date(response.data.query_time).toLocaleTimeString(
          "zh-CN"
      );
    } else {
      currentTime.value = new Date().toLocaleTimeString("zh-CN");
    }

    // 处理数据
    processDevicesData(response.data.devices, isIncremental);

    // 检查MQTT状态
    checkServerStatus();
  } catch (error) {
    console.error("获取数据失败", error);
    ElMessage.error("数据同步失败");
    serverStatus.value = false;
  } finally {
    loading.value = false;
  }
};

const processDevicesData = (
    backendDevices: BackendDevice[],
    isIncremental: boolean
) => {
  // 遍历所有15个设备插槽
  devices.value.forEach((deviceDisplay) => {
    const backendDevice = backendDevices.find(
        (d) => d.machine_name === deviceDisplay.id
    );

    if (backendDevice && backendDevice.voltage_data.length > 0) {
      // 更新型号
      if (backendDevice.machine_model) {
        deviceDisplay.model = backendDevice.machine_model;
      }

      // 提取最新电压
      const latestData =
          backendDevice.voltage_data[backendDevice.voltage_data.length - 1];
      const newVoltage = Math.round(latestData.avg_voltage);

      // 计算趋势: 最新的电压和前一点电压的差值
      if (backendDevice.voltage_data.length >= 2) {
        // 如果本次返回的数据中有多个点，取最后两个点计算
        const prevData =
            backendDevice.voltage_data[backendDevice.voltage_data.length - 2];
        deviceDisplay.trend = newVoltage - Math.round(prevData.avg_voltage);
      } else {
        // 如果只有一个点（或者是增量更新只回了一个点），则对比上次保存的电压
        deviceDisplay.trend = newVoltage - deviceDisplay.currentVoltage;
      }

      // 更新当前电压
      deviceDisplay.currentVoltage = newVoltage;

      // 更新历史数据 (用于绘图)
      // 如果是增量更新，append数据；如果是全量，重置history
      // 保持 history 为最近 120 个点
      if (isIncremental) {
        // 简单的把新点加进去
        deviceDisplay.history.push(newVoltage);
        if (deviceDisplay.history.length > 120) deviceDisplay.history.shift();
      } else {
        // 全量更新，取最后120个点
        const historyData = backendDevice.voltage_data
            .slice(-120)
            .map((v) => v.avg_voltage);
        // 补齐120个点
        while (historyData.length < 120) {
          historyData.unshift(0);
        }
        deviceDisplay.history = historyData;
      }

      // 状态判断
      // 1. <= 0 : 停止
      // 2. > 1680 : 正常 (运行)
      // 3. 0 < x <= 1680 : 异常
      if (newVoltage <= 0) {
        deviceDisplay.isRunning = false;
        deviceDisplay.isWarning = false;
      } else {
        deviceDisplay.isRunning = true;
        deviceDisplay.isWarning = newVoltage <= 1680;
      }
    } else if (!isIncremental) {
      // 全量更新时，如果没有数据，重置为0
      deviceDisplay.currentVoltage = 0;
      deviceDisplay.trend = 0;
      deviceDisplay.isRunning = false;
      deviceDisplay.isWarning = false;
      deviceDisplay.history = Array(120).fill(0);
      deviceDisplay.model = "";
    }
  });
};

const checkServerStatus = async () => {
  const start = performance.now();
  try {
    const res = await axios.get("/api/mqtt/status");
    serverStatus.value = res.data.connected;
    latency.value = Math.round(performance.now() - start);
  } catch {
    serverStatus.value = false;
    latency.value = 0;
  }
};

// 获取运行时长数据
const fetchHoursData = async () => {
  // 开始加载前，先设置所有设备的loading状态为true
  devices.value.forEach((device) => {
    device.hoursLoading = true;
  });

  try {
    const response = await axios.get<HoursData[]>("/api/home/hours");
    const hoursDataMap = new Map(
        response.data.map((item) => [item.name, item])
    );

    devices.value.forEach((device) => {
      const hoursData = hoursDataMap.get(device.id);
      if (hoursData) {
        device.totalHours = hoursData.total_hours;
        device.currentHours = hoursData.current_hours;
      } else {
        device.totalHours = 0;
        device.currentHours = 0;
      }
      device.hoursLoading = false;
    });
  } catch (error) {
    console.error("获取运行时长失败:", error);
    // 即使失败也要设置 loading 为 false
    devices.value.forEach((device) => {
      device.hoursLoading = false;
      device.totalHours = 0;
      device.currentHours = 0;
    });
  }
};

// 获取日志
const fetchMqttLogs = async () => {
  try {
    const response = await axios.get("/api/mqtt/logs");
    systemLogs.value = response.data.logs.map((log: any) => {
      return `[${log.timestamp}] [${log.level}] ${log.message}`;
    });
  } catch (error) {
    console.error("获取MQTT日志失败:", error);
    ElMessage.error("获取日志失败");
    systemLogs.value = ["[系统] 获取日志失败"];
  }
};

const showLogsDialog = () => {
  fetchMqttLogs();
  logsDialogVisible.value = true;
};

// SVG 路径生成 helper
// 固定量程 0-2000
const getPolylinePath = (history: number[]) => {
  const max = 2800;
  const min = 0;
  const width = 100;

  let d = "";
  history.forEach((val, i) => {
    const x = (i / Math.max(history.length - 1, 1)) * width;

    // 计算 Y 轴比例 (0.0 - 1.0)
    let normalizedY = (val - min) / (max - min);
    normalizedY = Math.max(0, Math.min(1, normalizedY));

    // 映射到 SVG 高度 (0-100)
    // 使用 90% 的高度空间，留出 10% 边距
    const y = 100 - normalizedY * 90;

    d += `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)} `;
  });
  return d;
};

const getAreaPath = (history: number[]) => {
  const linePath = getPolylinePath(history);
  return `${linePath} L100,100 L0,100 Z`;
};

// 辅助函数：状态显示
const getStatusColorClass = (device: DeviceDisplay) => {
  if (device.isWarning) return "bg-red-500 animate-ping";
  if (device.isRunning) return "bg-emerald-400";
  return "bg-slate-400"; // 停止
};

const getStatusTextClass = (device: DeviceDisplay) => {
  if (device.isWarning) return "text-red-500";
  if (device.isRunning) return "text-emerald-500";
  return "text-slate-500";
};

const getStatusText = (device: DeviceDisplay) => {
  if (device.isWarning) return "异常";
  if (device.isRunning) return "运行";
  return "停止";
};

const refreshAll = () => {
  fetchOverviewData(false);
  fetchHoursData(); // 同时刷新运行时长
  // 重置倒计时为5分钟
  countdown.value = 300;
  // 重置运行时长倒计时为60分钟
  hoursCountdown.value = 3600;
};

// 倒计时显示格式化为 mm:ss
const countdownDisplay = computed(() => {
  const minutes = Math.floor(countdown.value / 60);
  const seconds = countdown.value % 60;
  return `${minutes.toString().padStart(2, "0")}:${seconds
      .toString()
      .padStart(2, "0")}`;
});

// 更新日志相关
const changelogDialogVisible = ref(false);
const changelogData = [
  {
    version: "v1.0.0",
    date: "2025-10-27",
    changes: [
      "新增主页看板, 显示当前所有设备的运行状态,每5分钟自动刷新数据",
      "新增更新日志功能, 可查看系统历史更新记录",
      "所有数据查看迁移至历史记录页面, 优化主页面布局",
      "新增数据导出功能, 可选择时间范围(默认一个月)导出所有设备的数据为CSV文件",
      "新增MQTT中转服务器状态显示, 实时查看服务器连接状态及日志",
    ],
  },
  {
    version: "v1.1.0",
    date: "2025-11-17",
    changes: [
      "图表中X轴延长1倍修改为20%",
      "设备型号增加修改名称的功能",
      "数据过滤从1400改为1680",
      "时间轴时长删除空段后要延续",
      "自定义修改/删除小室电压的值",
    ],
  },
  {
    version: "v2.0.0",
    date: "2025-11-19",
    changes: ["重做监控页面, 使用SVG绘制简易折线图, 提升性能和视觉效果"],
  },
];
const sortedChangelogData = computed(() => [...changelogData].reverse());

const handleChangelogClick = () => {
  changelogDialogVisible.value = true;
};

// 历史数据跳转
const handleHistoryClick = () => {
  router.push("/charts");
};

// 导出数据相关
const exportDialogVisible = ref(false);
const exportLoading = ref(false);

// 初始化默认时间范围（最近一个月到现在）
const getDefaultDateRange = (): [Date, Date] => {
  const endDate = new Date();
  const startDate = new Date();
  startDate.setMonth(startDate.getMonth() - 1);
  return [startDate, endDate];
};

const exportDateRange = ref<[Date, Date]>(getDefaultDateRange());

const handleExportData = () => {
  // 每次打开对话框时重新设置默认时间范围
  exportDateRange.value = getDefaultDateRange();
  exportDialogVisible.value = true;
};

const confirmExport = async () => {
  if (!exportDateRange.value || exportDateRange.value.length !== 2) {
    ElMessage.warning("请选择起始和截止时间");
    return;
  }

  const [startDate, endDate] = exportDateRange.value;

  // 格式化时间为 YYYY-MM-DD HH:MM:SS
  const formatDateTime = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const seconds = String(date.getSeconds()).padStart(2, "0");
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  };

  const startDateTime = formatDateTime(startDate);
  const endDateTime = formatDateTime(endDate);

  exportLoading.value = true; // 开始加载

  try {
    // 调用后端API导出数据
    const response = await axios.get("/api/home/export", {
      params: {
        start_datetime: startDateTime,
        end_datetime: endDateTime,
      },
      responseType: "blob",
    });

    // 创建下载链接
    const blob = new Blob([response.data], {type: "text/csv;charset=utf-8;"});
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;

    // 从响应头获取文件名，如果没有则使用默认名称
    const contentDisposition = response.headers["content-disposition"];
    let filename = `设备数据_${startDateTime.replace(
        /[:\s-]/g,
        ""
    )}_${endDateTime.replace(/[:\s-]/g, "")}.csv`;
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename=(.+)/);
      if (filenameMatch && filenameMatch[1]) {
        filename = filenameMatch[1];
      }
    }

    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    ElMessage.success("数据导出成功");
    exportDialogVisible.value = false;
  } catch (error: any) {
    console.error("导出数据失败:", error);
    if (error.response && error.response.data) {
      // 如果是Blob类型的错误响应，需要读取其内容
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const errorData = JSON.parse(reader.result as string);
          ElMessage.error(errorData.detail || "导出数据失败");
        } catch {
          ElMessage.error("导出数据失败，请稍后重试");
        }
      };
      reader.readAsText(error.response.data);
    } else {
      ElMessage.error("导出数据失败，请稍后重试");
    }
  } finally {
    exportLoading.value = false; // 结束加载
  }
};

// 详情图表相关
const deviceChartDialogVisible = ref(false);
const selectedDeviceName = ref("");
const detailDay = ref(1);
const detailLoading = ref(false);
let detailChart: Highcharts.Chart | null = null;

const handleDeviceClick = (device: DeviceDisplay) => {
  selectedDeviceName.value = device.id;
  detailDay.value = 1;
  deviceChartDialogVisible.value = true;
  nextTick(() => {
    fetchAndRenderDetail();
  });
};

const changeDetailDay = (d: number) => {
  if (detailDay.value === d) return;
  detailDay.value = d;
  fetchAndRenderDetail();
};

const handleCloseChartDialog = () => {
  if (detailChart) {
    detailChart.destroy();
    detailChart = null;
  }
};

const fetchAndRenderDetail = async () => {
  detailLoading.value = true;
  try {
    const res = await axios.get<OverviewResponse>("/api/home/overview", {
      params: {day: detailDay.value},
    });
    const devData = res.data.devices.find(
        (d) => d.machine_name === selectedDeviceName.value
    );
    if (devData) {
      renderDetailChart(devData.voltage_data, res.data.query_time);
    } else {
      ElMessage.warning("未找到该设备数据");
    }
  } catch (e) {
    console.error(e);
    ElMessage.error("加载详情失败");
  } finally {
    detailLoading.value = false;
  }
};

const renderDetailChart = (data: VoltageData[], queryTimeStr: string) => {
  const chartData = data
      .map((d) => {
        const ts = new Date(`${d.date} ${d.time}`).getTime();
        return [ts, d.avg_voltage];
      })
      .sort((a: any, b: any) => a[0] - b[0]);

  if (chartData.length === 0) {
    // 如果没有数据，也应该清空或显示无数据
    if (detailChart) detailChart.destroy();
    detailChart = null;
    return;
  }

  const maxDataTime = (chartData[chartData.length - 1] as any)[0];
  const queryTime = new Date(queryTimeStr).getTime();

  let xMin, xMax;
  const diff = queryTime - maxDataTime;
  const dayMs = detailDay.value * 24 * 3600 * 1000;

  if (diff < 30 * 60 * 1000) {
    // 差值小于30分钟
    xMax = maxDataTime;
    xMin = maxDataTime - dayMs;
  } else {
    xMax = queryTime;
    xMin = queryTime - dayMs;
  }

  if (detailChart) detailChart.destroy();

  detailChart = Highcharts.chart("device-detail-chart", {
    time: {
      useUTC: false,
    },
    chart: {
      type: "line",
      zoomType: "x",
      panning: true,
      panKey: "shift",
    },
    title: {text: undefined},
    xAxis: {
      type: "datetime",
      min: xMin,
      max: xMax,
      gridLineWidth: 1,
      gridLineColor: "#f1f5f9",
      dateTimeLabelFormats: {
        millisecond: "%H:%M:%S.%L",
        second: "%H:%M:%S",
        minute: "%H:%M",
        hour: "%H:%M",
        day: "%m月%d日",
        week: "%m月%d日",
        month: "%Y年%m月",
        year: "%Y年",
      },
    },
    yAxis: {
      title: {text: "平均电压 (mV)"},
      gridLineWidth: 1,
      gridLineColor: "#f1f5f9",
      min: 0,
    },
    tooltip: {
      shared: true,
      useHTML: true,
      formatter: function (this: any) {
        const date = new Date(this.x);
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, "0");
        const day = date.getDate().toString().padStart(2, "0");
        const hours = date.getHours().toString().padStart(2, "0");
        const minutes = date.getMinutes().toString().padStart(2, "0");
        const seconds = date.getSeconds().toString().padStart(2, "0");

        let s = `<div style="font-size: 12px; font-weight: bold; margin-bottom: 5px;">${year}年${month}月${day}日 ${hours}:${minutes}:${seconds}</div>`;

        this.points.forEach((point: any) => {
          s += `<div style="margin-top: 2px;"><span style="color: ${point.color}">●</span> ${point.series.name}: <b>${point.y} mV</b></div>`;
        });

        return s;
      },
    },
    legend: {enabled: true},
    credits: {enabled: false},
    series: [
      {
        type: "line",
        name: selectedDeviceName.value,
        data: chartData as any,
        color: "#3b82f6",
        lineWidth: 2,
        marker: {
          enabled: false,
          states: {
            hover: {
              enabled: true,
            },
          },
        },
      },
    ],
  } as any);
};

onMounted(() => {
  initDevices();
  fetchOverviewData(false);

  // 异步获取运行时长数据
  fetchHoursData();

  // 每 5 分钟刷新一次电压数据
  refreshInterval = setInterval(() => {
    fetchOverviewData(true); // 尝试增量更新
    countdown.value = 300; // 重置倒计时
  }, 300000);

  // 每 60 分钟刷新一次运行时长数据
  hoursRefreshInterval = setInterval(() => {
    fetchHoursData();
    hoursCountdown.value = 3600; // 重置运行时长倒计时
  }, 3600000);

  // 每秒更新一次时间显示
  timeInterval = setInterval(() => {
    currentTime.value = new Date().toLocaleTimeString("zh-CN");
  }, 1000);

  // 每秒更新倒计时
  countdownInterval = setInterval(() => {
    if (countdown.value > 0) {
      countdown.value--;
    }
  }, 1000);

  // 每秒更新运行时长倒计时
  hoursCountdownInterval = setInterval(() => {
    if (hoursCountdown.value > 0) {
      hoursCountdown.value--;
    }
  }, 1000);
});

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval);
  if (timeInterval) clearInterval(timeInterval);
  if (countdownInterval) clearInterval(countdownInterval);
  if (hoursRefreshInterval) clearInterval(hoursRefreshInterval);
  if (hoursCountdownInterval) clearInterval(hoursCountdownInterval);
});
</script>

<style scoped>
/* 配合 Tailwind 这里的 style 可以很少 */
</style>

<script lang="ts" setup>
import {ref, onMounted, computed} from 'vue'

interface DeviceInfo {
  device_id: string
  device: string
  anode: string
  cathode: string
  size: string  // 新增size字段
  start_time: string  // 新增start_time字段
  end_time: string
  jihua_exists?: boolean  // 新增jihua_exists字段
  voltage_exists?: boolean  // 新增voltage_exists字段
  diding_exists?: boolean  // 新增diding_exists字段
  last_voltage_time?: string  // 耐久最后运行时间
}

interface SelectOption {
  device?: string
  anode?: string
  cathode?: string
}

const emit = defineEmits(['selectionChange'])

// 响应式数据
const allDeviceOptions = ref<SelectOption[]>([])
const allAnodeOptions = ref<SelectOption[]>([])
const allCathodeOptions = ref<SelectOption[]>([])
const allDeviceInfo = ref<DeviceInfo[]>([])

const deviceSelected = ref<string[]>([])
const anodeSelected = ref<string[]>([])
const cathodeSelected = ref<string[]>([])

const deviceDropdownOpen = ref(false)
const anodeDropdownOpen = ref(false)
const cathodeDropdownOpen = ref(false)

const selectedDeviceIds = ref<string[]>([])
const isRefreshing = ref(false)

// 格式化时间，只显示年月日时分
function formatTimeShort(dateTimeStr: string | undefined): string {
  if (!dateTimeStr) return ''
  try {
    // 格式: YYYY-MM-DD HH:mm，去掉 T
    return dateTimeStr.slice(0, 16).replace('T', ' ')
  } catch {
    return dateTimeStr
  }
}

// 计算可用选项（基于当前筛选条件）
const availableDeviceOptions = computed(() => {
  if (anodeSelected.value.length === 0 && cathodeSelected.value.length === 0) {
    return allDeviceOptions.value
  }

  const availableDevices = new Set<string>()
  filteredDeviceInfo.value.forEach(item => {
    availableDevices.add(item.device)
  })

  return allDeviceOptions.value.filter(option => availableDevices.has(option.device!))
})

const availableAnodeOptions = computed(() => {
  if (deviceSelected.value.length === 0 && cathodeSelected.value.length === 0) {
    return allAnodeOptions.value
  }

  const availableAnodes = new Set<string>()
  filteredDeviceInfo.value.forEach(item => {
    availableAnodes.add(item.anode)
  })

  return allAnodeOptions.value.filter(option => availableAnodes.has(option.anode!))
})

const availableCathodeOptions = computed(() => {
  if (deviceSelected.value.length === 0 && anodeSelected.value.length === 0) {
    return allCathodeOptions.value
  }

  const availableCathodes = new Set<string>()
  filteredDeviceInfo.value.forEach(item => {
    availableCathodes.add(item.cathode)
  })

  return allCathodeOptions.value.filter(option => availableCathodes.has(option.cathode!))
})

// 基于其他两个选择器的筛选条件，获取可用的设备信息
const filteredDeviceInfo = computed(() => {
  return allDeviceInfo.value.filter(item => {
    const deviceMatch = deviceSelected.value.length === 0 || deviceSelected.value.includes(item.device)
    const anodeMatch = anodeSelected.value.length === 0 || anodeSelected.value.includes(item.anode)
    const cathodeMatch = cathodeSelected.value.length === 0 || cathodeSelected.value.includes(item.cathode)

    return deviceMatch && anodeMatch && cathodeMatch
  })
})

// 计算属性
const hasSelection = computed(() =>
    deviceSelected.value.length > 0 ||
    anodeSelected.value.length > 0 ||
    cathodeSelected.value.length > 0
)

const filteredResults = computed(() => {
  if (!hasSelection.value) return []
  return filteredDeviceInfo.value
})

// API 调用函数
async function fetchDeviceOptions() {
  try {
    const response = await fetch('/api/get/v1/device')
    const data = await response.json()
    allDeviceOptions.value = data.data || []
  } catch (error) {
    console.error('获取配置选项失败:', error)
  }
}

async function fetchAnodeOptions() {
  try {
    const response = await fetch('/api/get/v1/anode')
    const data = await response.json()
    allAnodeOptions.value = data.data || []
  } catch (error) {
    console.error('获取阳极选项失败:', error)
  }
}

async function fetchCathodeOptions() {
  try {
    const response = await fetch('/api/get/v1/cathode')
    const data = await response.json()
    allCathodeOptions.value = data.data || []
  } catch (error) {
    console.error('获取阴极选项失败:', error)
  }
}

// 获取所有设备的标签信息
async function fetchDevicesTags() {
  try {
    const response = await fetch('/api/get/devices_tags')
    const data = await response.json()
    if (data.status === 'success') {
      return data.data || []
    }
    return []
  } catch (error) {
    console.error('获取设备标签失败:', error)
    return []
  }
}

async function fetchAllDeviceInfo() {
  try {
    // 并行获取设备信息和标签信息
    const [deviceResponse, tagsData] = await Promise.all([
      fetch('/api/get/v1/filtered_device_info'),
      fetchDevicesTags()
    ])

    const deviceData = await deviceResponse.json()
    const devices = deviceData.data || []

    // 创建标签映射以便快速查找
    const tagsMap = new Map<string, { jihua_exists: boolean; voltage_exists: boolean; diding_exists: boolean; last_voltage_time?: string }>()
    tagsData.forEach((tag: { device_id: string; jihua_exists: boolean; voltage_exists: boolean; diding_exists: boolean; last_voltage_time?: string }) => {
      tagsMap.set(tag.device_id, {
        jihua_exists: tag.jihua_exists,
        voltage_exists: tag.voltage_exists,
        diding_exists: tag.diding_exists,
        last_voltage_time: tag.last_voltage_time
      })
    })

    // 合并设备信息和标签信息
    const devicesWithTags: DeviceInfo[] = devices.map((device: any): DeviceInfo => {
      const tags = tagsMap.get(device.device_id) ?? {
        jihua_exists: false,
        voltage_exists: false,
        diding_exists: false,
        last_voltage_time: undefined
      }
      return {
        ...device,
        jihua_exists: tags.jihua_exists,
        voltage_exists: tags.voltage_exists,
        diding_exists: tags.diding_exists,
        last_voltage_time: tags.last_voltage_time
      } as DeviceInfo
    })

    allDeviceInfo.value = devicesWithTags
  } catch (error) {
    console.error('获取配置信息失败:', error)
  }
}

// 事件处理函数
function onSelectionChange() {
  // 当筛选条件变化时，清空已选择的设备ID
  selectedDeviceIds.value = []
}

function toggleDeviceSelection(deviceId: string) {
  const index = selectedDeviceIds.value.indexOf(deviceId)
  if (index > -1) {
    selectedDeviceIds.value.splice(index, 1)
  } else {
    selectedDeviceIds.value.push(deviceId)
  }
}

function removeDeviceId(deviceId: string) {
  const index = selectedDeviceIds.value.indexOf(deviceId)
  if (index > -1) {
    selectedDeviceIds.value.splice(index, 1)
  }
}

function clearAll() {
  deviceSelected.value = []
  anodeSelected.value = []
  cathodeSelected.value = []
  selectedDeviceIds.value = []
  deviceDropdownOpen.value = false
  anodeDropdownOpen.value = false
  cathodeDropdownOpen.value = false
}

function confirmSelection() {
  emit('selectionChange', {
    deviceIds: selectedDeviceIds.value,
    filters: {
      device: deviceSelected.value,
      anode: anodeSelected.value,
      cathode: cathodeSelected.value
    },
    results: filteredResults.value
  })
}

// 点击外部关闭下拉框
function handleClickOutside(event: Event) {
  const target = event.target as HTMLElement
  if (!target.closest('.multi-select')) {
    deviceDropdownOpen.value = false
    anodeDropdownOpen.value = false
    cathodeDropdownOpen.value = false
  }
}

// 刷新数据的函数
async function refreshData() {
  try {
    isRefreshing.value = true
    // 保留当前筛选条件
    const currentDeviceSelection = [...deviceSelected.value]
    const currentAnodeSelection = [...anodeSelected.value]
    const currentCathodeSelection = [...cathodeSelected.value]

    // 重新获取所有选项和设备信息
    await Promise.all([
      fetchDeviceOptions(),
      fetchAnodeOptions(),
      fetchCathodeOptions(),
      fetchAllDeviceInfo()
    ])

    // 恢复筛选条件
    deviceSelected.value = currentDeviceSelection
    anodeSelected.value = currentAnodeSelection
    cathodeSelected.value = currentCathodeSelection
  } catch (error) {
    console.error('刷新数据失败:', error)
  } finally {
    isRefreshing.value = false
  }
}

onMounted(async () => {
  await Promise.all([
    fetchDeviceOptions(),
    fetchAnodeOptions(),
    fetchCathodeOptions(),
    fetchAllDeviceInfo()
  ])

  document.addEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="triple-selector">
    <div class="selector-header">
      <h3>配置筛选</h3>
      <div class="action-buttons">
        <button class="refresh-btn" @click="refreshData" :disabled="isRefreshing">
          <span class="refresh-icon" :class="{ 'spinning': isRefreshing }">⟳</span>
          {{ isRefreshing ? '刷新中...' : '刷新' }}
        </button>
        <button class="clear-btn" @click="clearAll">清空</button>
        <button :disabled="!hasSelection" class="confirm-btn" @click="confirmSelection">确认选择</button>
      </div>
    </div>

    <div class="selector-container">
      <!-- Device 选择器 -->
      <div class="selector-item">
        <label>编号</label>
        <el-select
            v-model="deviceSelected"
            clearable
            filterable
            multiple
            placeholder="请选择编号"
            size="large"
            style="width: 100%"
            @change="onSelectionChange"
        >
          <el-option
              v-for="item in availableDeviceOptions"
              :key="item.device"
              :label="item.device"
              :title="item.device"
              :value="item.device"
              class="my-custom-option"
          >
            <div class="option-content">{{ item.device }}</div>
          </el-option>
        </el-select>
      </div>

      <!-- Anode 选择器 -->
      <div class="selector-item">
        <label>阳极</label>
        <el-select
            v-model="anodeSelected"
            clearable
            filterable
            multiple
            placeholder="请选择阳极"
            popper-style="max-width: 400px;"
            size="large"
            style="width: 100%"
            @change="onSelectionChange"
        >
          <el-option
              v-for="item in availableAnodeOptions"
              :key="item.anode"
              :label="item.anode"
              :title="item.anode"
              :value="item.anode"
              class="my-custom-option"
          >
            <div class="option-content">{{ item.anode }}</div>
          </el-option>
        </el-select>
      </div>

      <!-- Cathode 选择器 -->
      <div class="selector-item">
        <label>阴极</label>
        <el-select
            v-model="cathodeSelected"
            clearable
            filterable
            multiple
            placeholder="请选择阴极"
            size="large"
            style="width: 100%"
            @change="onSelectionChange"
        >
          <el-option
              v-for="item in availableCathodeOptions"
              :key="item.cathode"
              :label="item.cathode"
              :title="item.cathode"
              :value="item.cathode"
              class="my-custom-option"
          >
            <div class="option-content">{{ item.cathode }}</div>
          </el-option>
        </el-select>
      </div>
    </div>

    <!-- 筛选结果展示 -->
    <div v-if="filteredResults.length" class="results-section">
      <h4>筛选结果 ({{ filteredResults.length }} 条)</h4>
      <div class="results-list">
        <div
            v-for="item in filteredResults"
            :key="item.device_id"
            :class="{ 'selected': selectedDeviceIds.includes(item.device_id) }"
            class="result-item"
            @click="toggleDeviceSelection(item.device_id)"
        >
          <div class="result-info">
            <div class="device-id">{{ item.device_id }}
              <el-tag type="info" v-if="item.start_time" effect="dark" style="margin-left: 5px">开始于 {{item.start_time}}</el-tag>
              <el-tag type="success" v-if="!item.end_time" effect="dark" style="margin-left: 5px">运行中</el-tag>
              <el-tag type="danger" v-if="item.end_time" effect="dark" style="margin-left: 5px">停止于 {{item.end_time}}</el-tag>
              <el-tag type="primary" v-if="item.jihua_exists" effect="dark" style="margin-left: 5px">极化</el-tag>
              <el-tag type="warning" v-if="item.voltage_exists" effect="dark" style="margin-left: 5px">耐久</el-tag>
              <el-tag type="warning" v-if="item.last_voltage_time" effect="plain" size="small" style="margin-left: 5px">{{ formatTimeShort(item.last_voltage_time) }}</el-tag>
              <el-tag type="info" v-if="item.diding_exists" effect="dark" style="margin-left: 5px">滴定</el-tag>
            </div>
            <div class="device-details">
              <span class="detail-item">编号: {{ item.device }}</span>
              <span class="detail-item">阳极: {{ item.anode }}</span>
              <span class="detail-item">阴极: {{ item.cathode }}</span>
              <span class="detail-item">尺寸: {{ item.size }}</span>
            </div>
          </div>
          <div class="selection-indicator">
            <i v-if="selectedDeviceIds.includes(item.device_id)">
              <el-icon><Select/></el-icon>
            </i>
          </div>
        </div>
      </div>
      <!-- 已选择的设备ID展示 -->
      <div v-if="selectedDeviceIds.length" class="selected-ids">
        <h4>已选择的配置ID ({{ selectedDeviceIds.length }} 个)</h4>
        <div class="id-tags">
        <span
            v-for="id in selectedDeviceIds"
            :key="id"
            class="id-tag"
            @click="removeDeviceId(id)"
        >
          {{ id }} <i class="remove">×</i>
        </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.triple-selector {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  max-width: 100%;
  transition: all 0.3s ease;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f1f5f9;
}

.selector-header h3 {
  margin: 0;
  color: #1e293b;
  font-size: 20px;
  font-weight: 600;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.refresh-btn, .clear-btn, .confirm-btn {
  padding: 10px 20px;
  border-radius: 8px;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.refresh-btn {
  background: #e0f7fa;
  color: #00796b;
  border: 1px solid #b2dfdb;
  display: flex;
  align-items: center;
  gap: 6px;
}

.refresh-btn:hover:not(:disabled) {
  background: #b2ebf2;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.refresh-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.refresh-icon {
  display: inline-block;
  font-size: 18px;
  line-height: 1;
  transition: transform 0.3s ease;
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.clear-btn {
  background: #f8fafc;
  color: #64748b;
  border: 1px solid #e2e8f0;
}

.clear-btn:hover {
  background: #f1f5f9;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.confirm-btn {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.3);
}

.confirm-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.confirm-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.selector-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.selector-item {
  position: relative;
}

.selector-item label {
  display: block;
  margin-bottom: 10px;
  font-weight: 600;
  color: #374151;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 覆盖 el-select 输入框字体和颜色 */
:deep(.el-select .el-input__inner) {
  font-size: 18px !important;
  color: #1a1a1a !important;
  font-weight: 600 !important;
  background-color: #fff !important;
}

/* 覆盖 el-select 输入框占位符颜色 */
:deep(.el-select .el-input__inner::placeholder) {
  color: #666 !important;
  font-weight: 500 !important;
}

/* 覆盖下拉选项字体和颜色 */
:deep(.el-select-dropdown__item) {
  max-width: 100% !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  font-size: 18px !important;
  font-weight: 500 !important;
  color: #1a1a1a !important;
}

/* 下拉选项悬停效果 */
:deep(.el-select-dropdown__item:hover),
:deep(.el-select-dropdown__item.hover) {
  background-color: #e6f4ff !important;
  white-space: normal !important;
  height: auto !important;
  overflow: visible !important;
  word-break: break-all !important;
  z-index: 100 !important;
}

/* 选中项高亮色加强 */
:deep(.el-select-dropdown__item.selected) {
  font-weight: 700 !important;
  color: #1a1a1a !important;
  background-color: #bae7ff !important;
}

:deep(.el-select__tags-text) {
  max-width: 80px !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  display: inline-block !important;
}

:deep(.el-tag) {
  max-width: 150px !important;
}

:deep(.el-tag:hover .el-select__tags-text) {
  max-width: none !important;
  overflow: visible !important;
}

:deep(.el-input__inner) {
  font-size: 16px !important;
  color: #1a1a1a !important;
  font-weight: 500 !important;
}

/* el-select 整体容器样式 */
:deep(.el-select) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

/* 输入框聚焦时的样式 */
:deep(.el-select.is-focus .el-input__inner) {
  border-color: #1677ff !important;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.2) !important;
}

/* 自定义下拉框宽度控制 */
.custom-select-dropdown {
  width: auto !important;
  min-width: 100% !important;
  max-width: 100% !important;
}

.custom-select-dropdown .el-select-dropdown__item {
  max-width: 100% !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

.custom-select-dropdown .el-select-dropdown__item:hover {
  white-space: normal !important;
  height: auto !important;
  overflow: visible !important;
  word-break: break-all !important;
}


.results-section {
  margin-top: 10px;
  padding-top: 24px;
  border-top: 2px solid #f1f5f9;
}

.results-section h4 {
  margin: 0 0 20px 0;
  color: #1e293b;
  font-size: 18px;
  font-weight: 600;
}

.results-list {
  display: grid;
  gap: 16px;
  max-height: 350px;
  overflow-y: auto;
  padding-right: 8px;
}

.results-list::-webkit-scrollbar {
  width: 6px;
}

.results-list::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.results-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.result-item {
  margin-top: 2px;
  margin-bottom: 1px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.result-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.result-item.selected {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  box-shadow: 0 8px 25px rgba(59, 130, 246, 0.2);
}

.result-info {
  flex: 1;
}

.device-id {
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 8px;
  font-size: 16px;
}

.device-details {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.detail-item {
  font-size: 12px;
  color: #64748b;
  background: #f8fafc;
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px solid #e2e8f0;
  font-weight: 500;
}

.selection-indicator {
  color: #3b82f6;
  font-weight: bold;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #eff6ff;
  border: 2px solid #3b82f6;
}

.selected-ids {
  margin-bottom: 10px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 2px solid #f1f5f9;
}

.selected-ids h4 {
  margin: 0 0 16px 0;
  color: #1e293b;
  font-size: 16px;
  font-weight: 600;
}

.id-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.id-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  padding: 8px 16px;
  border-radius: 24px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 14px rgba(59, 130, 246, 0.3);
}

.id-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
}

.id-tag .remove {
  font-style: normal;
  font-weight: bold;
  cursor: pointer;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  transition: background 0.2s ease;
}

.id-tag .remove:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
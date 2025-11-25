<template>
  <div class="h-[90vh] flex flex-col bg-background text-slate-600 antialiased font-sans overflow-hidden">
    <!-- 顶部导航 -->
    <nav
        class="bg-surface sticky top-0 z-50 border-b border-slate-200 px-6 py-4 shadow-sm backdrop-blur-md bg-white/90">
      <div class="max-w-8xl mx-auto flex justify-between items-center">
        <div class="flex items-center gap-3">
          <div
              class="w-10 h-10 bg-blue-600 text-white rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/30">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                    stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
            </svg>
          </div>
          <div>
            <h1 class="text-xl font-bold text-slate-800 tracking-tight">数据表格</h1>
            <p class="text-xs text-slate-500 font-medium">WinCC 历史数据查询</p>
          </div>
        </div>
        <button
            class="bg-white border border-slate-200 text-slate-600 hover:text-blue-600 hover:border-blue-200 px-4 py-2 rounded-lg text-sm font-medium shadow-sm transition-all active:scale-95"
            @click="goBack">
          返回首页
        </button>
      </div>
    </nav>

    <!-- 主要内容区域 -->
    <main class="flex-1 p-6 max-w-8xl mx-auto w-full overflow-hidden flex flex-col gap-4">
      <!-- 筛选栏 -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm">
        <!-- 标题栏 - 可点击展开/收起 -->
        <div
            class="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-slate-50 transition-colors rounded-t-xl"
            @click="filterPanelExpanded = !filterPanelExpanded"
        >
          <div class="flex items-center gap-2">
            <svg
                :class="{ 'rotate-90': filterPanelExpanded }"
                class="w-5 h-5 text-slate-500 transition-transform duration-200"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
            >
              <path d="M9 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
            </svg>
            <h3 class="text-sm font-semibold text-slate-700">筛选条件</h3>
            <span class="text-xs text-slate-400">(点击展开/收起)</span>
          </div>
          <div class="text-xs text-slate-400">
            {{ filterPanelExpanded ? '收起' : '展开' }}
          </div>
        </div>

        <!-- 筛选内容 - 可伸缩 -->
        <transition
            enter-active-class="transition-all duration-200 ease-out"
            enter-from-class="max-h-0 opacity-0"
            enter-to-class="max-h-[600px] opacity-100"
            leave-active-class="transition-all duration-200 ease-in"
            leave-from-class="max-h-[600px] opacity-100"
            leave-to-class="max-h-0 opacity-0"
        >
          <div v-show="filterPanelExpanded" class="overflow-hidden">
            <div class="p-4 border-t border-slate-100">
              <div class="flex flex-col gap-4">
                <!-- 第一行：数据筛选 -->
                <div class="flex flex-col md:flex-row gap-4">
                  <!-- 设备名称选择 -->
                  <div class="md:w-40">
                    <label class="block text-xs font-medium text-slate-600 mb-2">设备名称</label>
                    <el-select v-model="filters.machineName" class="w-full" clearable placeholder="选择设备"
                               @change="handleFilterChange">
                      <el-option v-for="i in 15" :key="i" :label="`${i}#`" :value="`${i}#`"/>
                    </el-select>
                  </div>

                  <!-- 日期时间范围选择 -->
                  <div class="flex-1">
                    <label class="block text-xs font-medium text-slate-600 mb-2">日期时间范围</label>
                    <el-date-picker
                        v-model="filters.dateTimeRange"
                        class="w-full"
                        clearable
                        end-placeholder="结束时间"
                        format="YYYY-MM-DD HH:mm:ss"
                        range-separator="至"
                        start-placeholder="开始时间"
                        type="datetimerange"
                        value-format="YYYY-MM-DD HH:mm:ss"
                        @change="handleFilterChange"
                    />
                  </div>

                  <!-- 操作按钮 -->
                  <div class="flex items-end gap-2">
                    <el-button :loading="loading" type="primary" @click="handleSearch">查询</el-button>
                    <el-button @click="handleReset">重置</el-button>
                  </div>
                </div>

                <!-- 第二行：字段筛选 -->
                <div class="border-t border-slate-100 pt-4">
                  <div class="flex items-center justify-between mb-2">
                    <label class="text-xs font-medium text-slate-600">显示字段</label>
                    <div class="flex gap-2">
                      <el-button size="small" @click="selectAllFields">全选</el-button>
                      <el-button size="small" @click="selectDefaultFields">默认</el-button>
                      <el-button size="small" @click="clearAllFields">清空</el-button>
                    </div>
                  </div>
                  <el-select
                      v-model="selectedFields"
                      :max-collapse-tags="3"
                      class="w-full"
                      clearable
                      collapse-tags
                      collapse-tags-tooltip
                      multiple
                      placeholder="选择要显示的字段"
                      @change="handleFieldsChange"
                  >
                    <el-option-group label="基本信息">
                      <el-option label="设备编号" value="machine_name"/>
                      <el-option label="设备型号" value="machine_model"/>
                      <el-option label="日期" value="date"/>
                      <el-option label="时间" value="time"/>
                    </el-option-group>
                    <el-option-group label="运行时间">
                      <el-option label="运行小时数" value="hours"/>
                    </el-option-group>
                    <el-option-group label="电流电压">
                      <el-option label="总电流" value="total_current"/>
                      <el-option label="总电压" value="total_voltage"/>
                    </el-option-group>
                    <el-option-group label="小室电压">
                      <el-option v-for="i in 20" :key="`cell_${i}`" :label="`CELL-${i}`" :value="`cell_${i}`"/>
                    </el-option-group>
                    <el-option-group label="电压统计">
                      <el-option label="电压最大值" value="max_voltage"/>
                      <el-option label="电压最小值" value="min_voltage"/>
                      <el-option label="平均电压" value="avg_voltage"/>
                      <el-option label="电压极差" value="voltage_range"/>
                      <el-option label="标准差" value="std_deviation"/>
                    </el-option-group>
                    <el-option-group label="泵和风扇">
                      <el-option label="泵后压力" value="pump_pressure"/>
                      <el-option label="泵开度" value="pump_opening"/>
                      <el-option label="风扇开度" value="fan_opening"/>
                    </el-option-group>
                    <el-option-group label="比重和液位">
                      <el-option label="碱液比重" value="specific_gravity"/>
                      <el-option label="液位" value="liquid_level"/>
                    </el-option-group>
                    <el-option-group label="压力">
                      <el-option label="进槽压力" value="inlet_pressure"/>
                      <el-option label="氧侧压力" value="oxygen_outlet_pressure"/>
                      <el-option label="氢侧压力" value="hydrogen_outlet_pressure"/>
                      <el-option label="进出压差" value="pressure_diff"/>
                      <el-option label="氢氧压差" value="sep_pressure_diff"/>
                    </el-option-group>
                    <el-option-group label="温度">
                      <el-option label="碱液温度" value="alkali_inlet_temp"/>
                      <el-option label="氧侧温度" value="oxygen_outlet_temp"/>
                      <el-option label="氢气温度" value="hydrogen_outlet_temp"/>
                      <el-option label="氢气出温" value="hydrogen_gas_temp"/>
                    </el-option-group>
                    <el-option-group label="流量和浓度">
                      <el-option label="氢气流量" value="hydrogen_flow_meter"/>
                      <el-option label="氧中氢" value="oxygen_in_hydrogen"/>
                      <el-option label="氢中氧" value="hydrogen_in_oxygen"/>
                      <el-option label="碱液流量" value="alkali_flow_meter"/>
                    </el-option-group>
                    <el-option-group label="能耗">
                      <el-option label="当前能耗" value="current_power"/>
                    </el-option-group>
                  </el-select>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- 表格容器 -->
      <div class="bg-white rounded-xl border border-slate-100 shadow-sm flex-1 overflow-hidden flex flex-col">
        <div class="flex-1 p-4 relative">
          <!-- 加载提示 -->
          <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
            <div class="text-center">
              <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-3"></div>
              <p class="text-sm text-slate-600">加载中...</p>
            </div>
          </div>

          <!-- 无数据提示 -->
          <div v-if="!loading && rowData.length === 0" class="absolute inset-0 flex items-center justify-center">
            <div class="text-center">
              <svg class="w-16 h-16 text-slate-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                    d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                    stroke-linecap="round" stroke-linejoin="round"
                    stroke-width="2"></path>
              </svg>
              <p class="text-slate-600 font-medium">暂无数据</p>
              <p class="text-sm text-slate-400 mt-1">请调整筛选条件后重试</p>
            </div>
          </div>

          <ag-grid-vue
              :columnDefs="columnDefs"
              :defaultColDef="defaultColDef"
              :rowData="rowData"
              class="ag-theme-alpine"
              style="width: 100%; height: 100%;"
              @grid-ready="onGridReady"
          />
        </div>

        <!-- 分页栏 -->
        <div class="border-t border-slate-100 px-4 py-3 flex justify-between items-center">
          <div class="text-sm text-slate-600">
            共 <span class="font-semibold text-blue-600">{{ totalRecords }}</span> 条记录
          </div>
          <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[15,30,60,120]"
              :total="totalRecords"
              layout="sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
          />
        </div>
      </div>
    </main>
  </div>
</template>

<script lang="ts" setup>
import {computed, onMounted, ref} from 'vue'
import {useRouter} from 'vue-router'
import {AgGridVue} from 'ag-grid-vue3'
import axios from 'axios'
import {ElMessage} from 'element-plus'
import type {ColDef, GridReadyEvent} from 'ag-grid-community'
import {AllCommunityModule, ModuleRegistry} from 'ag-grid-community'

// 注册 AG Grid 社区版模块
ModuleRegistry.registerModules([AllCommunityModule])

const router = useRouter()

// 筛选条件
const filters = ref({
  machineName: '',
  dateTimeRange: null as [string, string] | null,
})

// 字段筛选 - 默认显示除 cell_1 到 cell_20 外的所有字段
const selectedFields = ref<string[]>([
  'machine_name', 'machine_model', 'date', 'time', 'hours',
  'total_current', 'total_voltage',
  'max_voltage', 'min_voltage', 'avg_voltage', 'voltage_range', 'std_deviation',
  'pump_pressure', 'pump_opening', 'fan_opening',
  'specific_gravity', 'liquid_level',
  'inlet_pressure', 'oxygen_outlet_pressure', 'hydrogen_outlet_pressure', 'pressure_diff', 'sep_pressure_diff',
  'alkali_inlet_temp', 'oxygen_outlet_temp', 'hydrogen_outlet_temp', 'hydrogen_gas_temp',
  'hydrogen_flow_meter', 'oxygen_in_hydrogen', 'hydrogen_in_oxygen', 'alkali_flow_meter',
  'current_power'
])

// 所有可用字段
const allFieldKeys = [
  'machine_name', 'machine_model', 'date', 'time', 'hours',
  'total_current', 'total_voltage',
  'cell_1', 'cell_2', 'cell_3', 'cell_4', 'cell_5', 'cell_6', 'cell_7', 'cell_8', 'cell_9', 'cell_10',
  'cell_11', 'cell_12', 'cell_13', 'cell_14', 'cell_15', 'cell_16', 'cell_17', 'cell_18', 'cell_19', 'cell_20',
  'max_voltage', 'min_voltage', 'avg_voltage', 'voltage_range', 'std_deviation',
  'pump_pressure', 'pump_opening', 'fan_opening',
  'specific_gravity', 'liquid_level',
  'inlet_pressure', 'oxygen_outlet_pressure', 'hydrogen_outlet_pressure', 'pressure_diff', 'sep_pressure_diff',
  'alkali_inlet_temp', 'oxygen_outlet_temp', 'hydrogen_outlet_temp', 'hydrogen_gas_temp',
  'hydrogen_flow_meter', 'oxygen_in_hydrogen', 'hydrogen_in_oxygen', 'alkali_flow_meter',
  'current_power'
]

// 分页
const currentPage = ref(1)
const pageSize = ref(15)
const totalRecords = ref(0)

// 筛选面板伸缩状态
const filterPanelExpanded = ref(false)

// 表格数据
const rowData = ref<any[]>([])
const loading = ref(false)
const gridApi = ref<any>(null)

// 所有列定义的映射
const allColumnDefsMap: Record<string, ColDef> = {
  machine_name: {field: 'machine_name', headerName: '设备编号', width: 120, pinned: 'left'},
  machine_model: {field: 'machine_model', headerName: '设备型号', width: 120, pinned: 'left'},
  date: {field: 'date', headerName: '日期', width: 120},
  time: {field: 'time', headerName: '时间', width: 120},
  hours: {field: 'hours', headerName: '运行小时数(h)', width: 130, type: 'numericColumn'},
  total_current: {field: 'total_current', headerName: '总电流(A)', width: 120, type: 'numericColumn'},
  total_voltage: {field: 'total_voltage', headerName: '总电压(V)', width: 120, type: 'numericColumn'},
  cell_1: {field: 'cell_1', headerName: 'CELL-1(mV)', width: 130, type: 'numericColumn'},
  cell_2: {field: 'cell_2', headerName: 'CELL-2(mV)', width: 130, type: 'numericColumn'},
  cell_3: {field: 'cell_3', headerName: 'CELL-3(mV)', width: 130, type: 'numericColumn'},
  cell_4: {field: 'cell_4', headerName: 'CELL-4(mV)', width: 130, type: 'numericColumn'},
  cell_5: {field: 'cell_5', headerName: 'CELL-5(mV)', width: 130, type: 'numericColumn'},
  cell_6: {field: 'cell_6', headerName: 'CELL-6(mV)', width: 130, type: 'numericColumn'},
  cell_7: {field: 'cell_7', headerName: 'CELL-7(mV)', width: 130, type: 'numericColumn'},
  cell_8: {field: 'cell_8', headerName: 'CELL-8(mV)', width: 130, type: 'numericColumn'},
  cell_9: {field: 'cell_9', headerName: 'CELL-9(mV)', width: 130, type: 'numericColumn'},
  cell_10: {field: 'cell_10', headerName: 'CELL-10(mV)', width: 130, type: 'numericColumn'},
  cell_11: {field: 'cell_11', headerName: 'CELL-11(mV)', width: 130, type: 'numericColumn'},
  cell_12: {field: 'cell_12', headerName: 'CELL-12(mV)', width: 130, type: 'numericColumn'},
  cell_13: {field: 'cell_13', headerName: 'CELL-13(mV)', width: 130, type: 'numericColumn'},
  cell_14: {field: 'cell_14', headerName: 'CELL-14(mV)', width: 130, type: 'numericColumn'},
  cell_15: {field: 'cell_15', headerName: 'CELL-15(mV)', width: 130, type: 'numericColumn'},
  cell_16: {field: 'cell_16', headerName: 'CELL-16(mV)', width: 130, type: 'numericColumn'},
  cell_17: {field: 'cell_17', headerName: 'CELL-17(mV)', width: 130, type: 'numericColumn'},
  cell_18: {field: 'cell_18', headerName: 'CELL-18(mV)', width: 130, type: 'numericColumn'},
  cell_19: {field: 'cell_19', headerName: 'CELL-19(mV)', width: 130, type: 'numericColumn'},
  cell_20: {field: 'cell_20', headerName: 'CELL-20(mV)', width: 130, type: 'numericColumn'},
  max_voltage: {field: 'max_voltage', headerName: '电压最大值(mV)', width: 140, type: 'numericColumn'},
  min_voltage: {field: 'min_voltage', headerName: '电压最小值(mV)', width: 140, type: 'numericColumn'},
  avg_voltage: {field: 'avg_voltage', headerName: '平均电压(mV)', width: 140, type: 'numericColumn'},
  voltage_range: {field: 'voltage_range', headerName: '电压极差(mV)', width: 140, type: 'numericColumn'},
  std_deviation: {field: 'std_deviation', headerName: '标准差(mV)', width: 130, type: 'numericColumn'},
  pump_pressure: {field: 'pump_pressure', headerName: '泵后压力(MPa)', width: 140, type: 'numericColumn'},
  pump_opening: {field: 'pump_opening', headerName: '泵开度(Hz)', width: 120, type: 'numericColumn'},
  fan_opening: {field: 'fan_opening', headerName: '风扇开度(Hz)', width: 120, type: 'numericColumn'},
  specific_gravity: {field: 'specific_gravity', headerName: '碱液比重(mg/cm³)', width: 150, type: 'numericColumn'},
  liquid_level: {field: 'liquid_level', headerName: '液位(mm)', width: 120, type: 'numericColumn'},
  inlet_pressure: {field: 'inlet_pressure', headerName: '进槽压力(MPa)', width: 140, type: 'numericColumn'},
  oxygen_outlet_pressure: {
    field: 'oxygen_outlet_pressure',
    headerName: '氧侧压力(MPa)',
    width: 140,
    type: 'numericColumn'
  },
  hydrogen_outlet_pressure: {
    field: 'hydrogen_outlet_pressure',
    headerName: '氢侧压力(MPa)',
    width: 140,
    type: 'numericColumn'
  },
  pressure_diff: {field: 'pressure_diff', headerName: '进出压差(MPa)', width: 140, type: 'numericColumn'},
  sep_pressure_diff: {field: 'sep_pressure_diff', headerName: '氢氧压差(MPa)', width: 140, type: 'numericColumn'},
  alkali_inlet_temp: {field: 'alkali_inlet_temp', headerName: '碱液温度(℃)', width: 130, type: 'numericColumn'},
  oxygen_outlet_temp: {field: 'oxygen_outlet_temp', headerName: '氧侧温度(℃)', width: 130, type: 'numericColumn'},
  hydrogen_outlet_temp: {field: 'hydrogen_outlet_temp', headerName: '氢气温度(℃)', width: 130, type: 'numericColumn'},
  hydrogen_gas_temp: {field: 'hydrogen_gas_temp', headerName: '氢气出温(℃)', width: 130, type: 'numericColumn'},
  hydrogen_flow_meter: {field: 'hydrogen_flow_meter', headerName: '氢气流量', width: 120, type: 'numericColumn'},
  oxygen_in_hydrogen: {field: 'oxygen_in_hydrogen', headerName: '氧中氢(ppm)', width: 120, type: 'numericColumn'},
  hydrogen_in_oxygen: {field: 'hydrogen_in_oxygen', headerName: '氢中氧(ppm)', width: 120, type: 'numericColumn'},
  alkali_flow_meter: {field: 'alkali_flow_meter', headerName: '碱液流量(L/min)', width: 140, type: 'numericColumn'},
  current_power: {field: 'current_power', headerName: '当前能耗', width: 120, type: 'numericColumn'},
}

// 根据选中字段计算列定义
const columnDefs = computed<ColDef[]>(() => {
  return selectedFields.value
      .map(fieldKey => allColumnDefsMap[fieldKey])
      .filter(col => col !== undefined)
})

// 默认列配置
const defaultColDef: ColDef = {
  sortable: true,
  filter: false,
  resizable: true,
}


const goBack = () => {
  router.push('/home')
}

// Grid Ready 事件
const onGridReady = (params: GridReadyEvent) => {
  gridApi.value = params.api
  fetchData()
}

// 获取数据
const fetchData = async () => {
  loading.value = true

  try {
    const params: any = {
      page: currentPage.value,
      size: pageSize.value,
    }

    // 添加筛选条件
    if (filters.value.machineName) {
      params.machine_name = filters.value.machineName
    }

    // 添加日期时间范围
    if (filters.value.dateTimeRange && filters.value.dateTimeRange.length === 2) {
      params.start_datetime = filters.value.dateTimeRange[0]
      params.end_datetime = filters.value.dateTimeRange[1]
    }

    const response = await axios.get('/api/home/table-data', {params})

    rowData.value = response.data.data
    totalRecords.value = response.data.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取数据失败')
    rowData.value = []
    totalRecords.value = 0
  } finally {
    loading.value = false
  }
}

// 筛选变化
const handleFilterChange = () => {
  // 筛选条件变化时，重置到第一页
  currentPage.value = 1
}

// 查询按钮
const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

// 重置按钮
const handleReset = () => {
  filters.value = {
    machineName: '',
    dateTimeRange: null,
  }
  currentPage.value = 1
  pageSize.value = 15
  fetchData()
}

// 分页变化
const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchData()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchData()
}

// 字段筛选处理函数
const handleFieldsChange = () => {
  // 字段变化时更新表格列
  if (gridApi.value) {
    gridApi.value.setGridOption('columnDefs', columnDefs.value)
  }
}

const selectAllFields = () => {
  selectedFields.value = [...allFieldKeys]
  handleFieldsChange()
}

const selectDefaultFields = () => {
  selectedFields.value = [
    'machine_name', 'machine_model', 'date', 'time', 'hours',
    'total_current', 'total_voltage',
    'max_voltage', 'min_voltage', 'avg_voltage', 'voltage_range', 'std_deviation',
    'pump_pressure', 'pump_opening', 'fan_opening',
    'specific_gravity', 'liquid_level',
    'inlet_pressure', 'oxygen_outlet_pressure', 'hydrogen_outlet_pressure', 'pressure_diff', 'sep_pressure_diff',
    'alkali_inlet_temp', 'oxygen_outlet_temp', 'hydrogen_outlet_temp', 'hydrogen_gas_temp',
    'hydrogen_flow_meter', 'oxygen_in_hydrogen', 'hydrogen_in_oxygen', 'alkali_flow_meter',
    'current_power'
  ]
  handleFieldsChange()
}

const clearAllFields = () => {
  selectedFields.value = []
  handleFieldsChange()
}

onMounted(() => {
  // Grid Ready 后会自动调用 fetchData
})
</script>

<style scoped>

</style>


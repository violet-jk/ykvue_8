<template>
  <div class="chart-skeleton">
    <!-- 标题骨架 -->
    <div class="skeleton-header">
      <div class="skeleton-bar title-bar"></div>
      <div class="skeleton-bar subtitle-bar"></div>
    </div>

    <!-- 图表区域 -->
    <div class="skeleton-chart-wrapper">
      <!-- Y轴 -->
      <div class="skeleton-y-axis">
        <div class="skeleton-bar y-label" v-for="i in 6" :key="i"></div>
      </div>

      <!-- 图表主体 -->
      <div class="skeleton-chart-area">
        <!-- 网格线 -->
        <div class="skeleton-grid">
          <div class="grid-line horizontal" v-for="i in 5" :key="'h' + i"></div>
          <div class="grid-line vertical" v-for="i in 8" :key="'v' + i"></div>
        </div>

        <!-- 模拟曲线 -->
        <svg class="skeleton-lines" viewBox="0 0 100 50" preserveAspectRatio="none">
          <path d="M0,40 Q25,30 50,25 T100,15"
                fill="none"
                stroke="#e0e0e0"
                stroke-width="0.5"/>
          <path d="M0,35 Q25,25 50,30 T100,20"
                fill="none"
                stroke="#e0e0e0"
                stroke-width="0.5"/>
          <path d="M0,30 Q25,35 50,35 T100,25"
                fill="none"
                stroke="#e0e0e0"
                stroke-width="0.5"/>
        </svg>
      </div>

      <!-- X轴 -->
      <div class="skeleton-x-axis">
        <div class="skeleton-bar x-label" v-for="i in 8" :key="i"></div>
      </div>
    </div>

    <!-- 底部信息 -->
    <div class="skeleton-footer">
      <div class="skeleton-bar footer-bar"></div>
    </div>

    <!-- 加载提示 -->
    <div class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">加载中...</div>
    </div>
  </div>
</template>

<script lang="ts" setup>
// 纯展示组件
</script>

<style scoped>
.chart-skeleton {
  width: 100%;
  height: 500px;
  background: #fafafa;
  border-radius: 4px;
  padding: 24px;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 骨架条 */
.skeleton-bar {
  background: #e0e0e0;
  border-radius: 4px;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* 标题区域 */
.skeleton-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.title-bar {
  width: 200px;
  height: 24px;
}

.subtitle-bar {
  width: 150px;
  height: 16px;
}

/* 图表区域 */
.skeleton-chart-wrapper {
  flex: 1;
  display: flex;
  gap: 12px;
  min-height: 0;
}

.skeleton-y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 8px;
  width: 50px;
  padding-top: 10px;
  padding-bottom: 10px;
}

.y-label {
  width: 40px;
  height: 12px;
}

.skeleton-chart-area {
  flex: 1;
  position: relative;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.skeleton-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.grid-line {
  background: #f5f5f5;
}

.grid-line.horizontal {
  width: 100%;
  height: 1px;
}

.skeleton-x-axis {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding-left: 62px;
}

.x-label {
  flex: 1;
  height: 12px;
  max-width: 60px;
}

.skeleton-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0.3;
}

/* 底部信息 */
.skeleton-footer {
  display: flex;
  justify-content: center;
}

.footer-bar {
  width: 300px;
  height: 14px;
}

/* 加载提示 */
.loading-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e0e0e0;
  border-top-color: #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  color: #909399;
  font-size: 14px;
}
</style>

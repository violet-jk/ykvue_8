<template>
  <div class="chart-skeleton">
    <!-- 背景装饰粒子 -->
    <div class="bg-decoration">
      <div class="particle" v-for="i in 20" :key="i" :style="getParticleStyle(i)"></div>
    </div>

    <!-- 标题骨架 -->
    <div class="skeleton-header">
      <div class="skeleton-bar title-bar">
        <div class="shimmer"></div>
      </div>
      <div class="skeleton-bar subtitle-bar">
        <div class="shimmer"></div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="skeleton-chart-wrapper">
      <!-- Y轴 -->
      <div class="skeleton-y-axis">
        <div class="skeleton-bar y-label" v-for="i in 6" :key="i" :style="{ animationDelay: `${i * 0.1}s` }">
          <div class="shimmer"></div>
        </div>
      </div>

      <!-- 图表主体 -->
      <div class="skeleton-chart-area">
        <!-- 背景网格 -->
        <div class="skeleton-grid">
          <div class="grid-line horizontal" v-for="i in 6" :key="'h' + i"></div>
          <div class="grid-line vertical" v-for="i in 12" :key="'v' + i"></div>
        </div>

        <!-- 装饰性渐变背景 -->
        <div class="gradient-overlay"></div>

        <!-- 动态曲线 -->
        <svg class="skeleton-lines" viewBox="0 0 100 50" preserveAspectRatio="none">
          <defs>
            <linearGradient id="lineGradient1" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:#667eea;stop-opacity:0.3" />
              <stop offset="50%" style="stop-color:#764ba2;stop-opacity:0.6" />
              <stop offset="100%" style="stop-color:#667eea;stop-opacity:0.3" />
            </linearGradient>
            <linearGradient id="lineGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:#f093fb;stop-opacity:0.3" />
              <stop offset="50%" style="stop-color:#f5576c;stop-opacity:0.6" />
              <stop offset="100%" style="stop-color:#f093fb;stop-opacity:0.3" />
            </linearGradient>
            <linearGradient id="lineGradient3" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:#4facfe;stop-opacity:0.3" />
              <stop offset="50%" style="stop-color:#00f2fe;stop-opacity:0.6" />
              <stop offset="100%" style="stop-color:#4facfe;stop-opacity:0.3" />
            </linearGradient>
            
            <filter id="glow">
              <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          
          <path class="animated-line line-1" d="M0,40 Q25,30 50,25 T100,15"
                fill="none"
                stroke="url(#lineGradient1)"
                stroke-width="1.5"
                filter="url(#glow)"/>
          <path class="animated-line line-2" d="M0,35 Q25,25 50,30 T100,20"
                fill="none"
                stroke="url(#lineGradient2)"
                stroke-width="1.5"
                filter="url(#glow)"/>
          <path class="animated-line line-3" d="M0,30 Q25,35 50,35 T100,25"
                fill="none"
                stroke="url(#lineGradient3)"
                stroke-width="1.5"
                filter="url(#glow)"/>
        </svg>

        <!-- 数据点装饰 -->
        <div class="data-points">
          <div class="data-point" v-for="i in 8" :key="i" :style="getDataPointStyle(i)"></div>
        </div>
      </div>

      <!-- X轴 -->
      <div class="skeleton-x-axis">
        <div class="skeleton-bar x-label" v-for="i in 8" :key="i" :style="{ animationDelay: `${i * 0.08}s` }">
          <div class="shimmer"></div>
        </div>
      </div>
    </div>

    <!-- 底部信息 -->
    <div class="skeleton-footer">
      <div class="skeleton-bar footer-bar">
        <div class="shimmer"></div>
      </div>
    </div>

    <!-- 加载提示 -->
    <div class="loading-overlay">
      <div class="loading-spinner-container">
        <div class="loading-spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
      </div>
      <div class="loading-text">
        <span class="loading-dot">.</span>
        <span class="loading-dot">.</span>
        <span class="loading-dot">.</span>
        数据加载中
        <span class="loading-dot">.</span>
        <span class="loading-dot">.</span>
        <span class="loading-dot">.</span>
      </div>
      <div class="loading-progress">
        <div class="progress-bar"></div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
// 生成粒子样式
const getParticleStyle = (_index: number) => {
  const size = Math.random() * 4 + 2;
  const left = Math.random() * 100;
  const delay = Math.random() * 5;
  const duration = Math.random() * 10 + 15;
  
  return {
    width: `${size}px`,
    height: `${size}px`,
    left: `${left}%`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`
  };
};

// 生成数据点样式
const getDataPointStyle = (index: number) => {
  const left = (index * 12) + Math.random() * 8;
  const top = Math.random() * 70 + 10;
  const delay = index * 0.2;
  
  return {
    left: `${left}%`,
    top: `${top}%`,
    animationDelay: `${delay}s`
  };
};
</script>

<style scoped>
.chart-skeleton {
  width: 100%;
  height: 500px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  border-radius: 16px;
  padding: 32px;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 24px;
  overflow: hidden;
  box-shadow: 
    0 10px 40px rgba(0, 0, 0, 0.08),
    0 2px 8px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}

.particle {
  position: absolute;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.4) 0%, transparent 70%);
  border-radius: 50%;
  animation: float-up linear infinite;
}

@keyframes float-up {
  0% {
    transform: translateY(100vh) scale(0);
    opacity: 0;
  }
  10% {
    opacity: 0.6;
  }
  90% {
    opacity: 0.6;
  }
  100% {
    transform: translateY(-100px) scale(1);
    opacity: 0;
  }
}

/* 骨架条基础样式 */
.skeleton-bar {
  position: relative;
  background: linear-gradient(90deg, 
    rgba(255, 255, 255, 0.6) 0%,
    rgba(255, 255, 255, 0.8) 50%,
    rgba(255, 255, 255, 0.6) 100%
  );
  border-radius: 8px;
  overflow: hidden;
  backdrop-filter: blur(10px);
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  animation: skeleton-pulse 2s ease-in-out infinite;
}

/* 流光效果 */
.shimmer {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.8) 50%,
    transparent 100%
  );
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% {
    left: -100%;
  }
  100% {
    left: 200%;
  }
}

@keyframes skeleton-pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.85;
    transform: scale(0.98);
  }
}

/* 标题区域 */
.skeleton-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  z-index: 1;
}

.title-bar {
  width: 240px;
  height: 32px;
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.15) 0%,
    rgba(118, 75, 162, 0.15) 100%
  );
}

.subtitle-bar {
  width: 180px;
  height: 20px;
  background: linear-gradient(135deg, 
    rgba(240, 147, 251, 0.12) 0%,
    rgba(245, 87, 108, 0.12) 100%
  );
}

/* 图表区域 */
.skeleton-chart-wrapper {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
  z-index: 1;
}

.skeleton-y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 12px;
  width: 60px;
  padding: 16px 0;
}

.y-label {
  width: 50px;
  height: 14px;
  background: linear-gradient(90deg, 
    rgba(255, 255, 255, 0.7) 0%,
    rgba(255, 255, 255, 0.5) 100%
  );
}

.skeleton-chart-area {
  flex: 1;
  position: relative;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.95) 0%,
    rgba(255, 255, 255, 0.85) 100%
  );
  border-radius: 12px;
  overflow: hidden;
  backdrop-filter: blur(20px);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 1),
    inset 0 -1px 0 rgba(0, 0, 0, 0.05);
}

.skeleton-grid {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: grid;
  grid-template-rows: repeat(6, 1fr);
  grid-template-columns: repeat(12, 1fr);
  z-index: 1;
}

.grid-line {
  background: rgba(102, 126, 234, 0.06);
}

.grid-line.horizontal {
  grid-column: 1 / -1;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%,
    rgba(102, 126, 234, 0.1) 50%,
    transparent 100%
  );
}

.grid-line.vertical {
  grid-row: 1 / -1;
  width: 1px;
  background: linear-gradient(180deg, 
    transparent 0%,
    rgba(102, 126, 234, 0.08) 50%,
    transparent 100%
  );
}

/* 渐变装饰层 */
.gradient-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: 
    radial-gradient(circle at 20% 30%, rgba(102, 126, 234, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(245, 87, 108, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 50% 50%, rgba(0, 242, 254, 0.05) 0%, transparent 60%);
  z-index: 2;
  pointer-events: none;
  animation: gradient-shift 8s ease-in-out infinite;
}

@keyframes gradient-shift {
  0%, 100% {
    opacity: 0.6;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

.skeleton-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 3;
  opacity: 0.9;
}

.animated-line {
  stroke-dasharray: 200;
  stroke-dashoffset: 200;
  animation: draw-line 3s ease-in-out infinite;
}

.line-1 {
  animation-delay: 0s;
}

.line-2 {
  animation-delay: 0.5s;
}

.line-3 {
  animation-delay: 1s;
}

@keyframes draw-line {
  0% {
    stroke-dashoffset: 200;
    opacity: 0;
  }
  20% {
    opacity: 1;
  }
  80% {
    opacity: 1;
  }
  100% {
    stroke-dashoffset: 0;
    opacity: 0.6;
  }
}

/* 数据点装饰 */
.data-points {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 4;
  pointer-events: none;
}

.data-point {
  position: absolute;
  width: 8px;
  height: 8px;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.6) 0%, transparent 70%);
  border-radius: 50%;
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% {
    transform: scale(1);
    opacity: 0.6;
  }
  50% {
    transform: scale(1.5);
    opacity: 1;
  }
}

.skeleton-x-axis {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding-left: 76px;
}

.x-label {
  flex: 1;
  height: 14px;
  max-width: 70px;
  background: linear-gradient(90deg, 
    rgba(255, 255, 255, 0.7) 0%,
    rgba(255, 255, 255, 0.5) 100%
  );
}

/* 底部信息 */
.skeleton-footer {
  display: flex;
  justify-content: center;
  z-index: 1;
}

.footer-bar {
  width: 320px;
  height: 16px;
  background: linear-gradient(135deg, 
    rgba(79, 172, 254, 0.12) 0%,
    rgba(0, 242, 254, 0.12) 100%
  );
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
  gap: 20px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.95);
  padding: 40px 60px;
  border-radius: 20px;
  backdrop-filter: blur(20px);
  box-shadow: 
    0 20px 60px rgba(0, 0, 0, 0.15),
    0 0 0 1px rgba(255, 255, 255, 0.8),
    inset 0 1px 0 rgba(255, 255, 255, 1);
}

.loading-spinner-container {
  position: relative;
  width: 80px;
  height: 80px;
}

.loading-spinner {
  position: relative;
  width: 100%;
  height: 100%;
}

.spinner-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  animation: spin-ring 2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}

.spinner-ring:nth-child(1) {
  width: 70px;
  height: 70px;
  border: 3px solid transparent;
  border-top-color: #667eea;
  animation-delay: 0s;
}

.spinner-ring:nth-child(2) {
  width: 55px;
  height: 55px;
  border: 3px solid transparent;
  border-top-color: #f5576c;
  animation-delay: -0.3s;
}

.spinner-ring:nth-child(3) {
  width: 40px;
  height: 40px;
  border: 3px solid transparent;
  border-top-color: #00f2fe;
  animation-delay: -0.6s;
}

@keyframes spin-ring {
  0% {
    transform: translate(-50%, -50%) rotate(0deg);
  }
  100% {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}

.loading-text {
  color: #667eea;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 2px;
}

.loading-dot {
  animation: bounce-dot 1.4s ease-in-out infinite;
  display: inline-block;
}

.loading-dot:nth-child(1) {
  animation-delay: 0s;
}

.loading-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dot:nth-child(3) {
  animation-delay: 0.4s;
}

.loading-dot:nth-child(5) {
  animation-delay: 0.6s;
}

.loading-dot:nth-child(6) {
  animation-delay: 0.8s;
}

.loading-dot:nth-child(7) {
  animation-delay: 1s;
}

@keyframes bounce-dot {
  0%, 80%, 100% {
    transform: translateY(0);
    opacity: 0.6;
  }
  40% {
    transform: translateY(-8px);
    opacity: 1;
  }
}

.loading-progress {
  width: 200px;
  height: 4px;
  background: rgba(102, 126, 234, 0.15);
  border-radius: 2px;
  overflow: hidden;
  position: relative;
}

.progress-bar {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 40%;
  background: linear-gradient(90deg, 
    #667eea 0%,
    #764ba2 50%,
    #667eea 100%
  );
  background-size: 200% 100%;
  border-radius: 2px;
  animation: progress-move 2s ease-in-out infinite;
  box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
}

@keyframes progress-move {
  0% {
    left: -40%;
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    left: 100%;
    background-position: 0% 50%;
  }
}
</style>

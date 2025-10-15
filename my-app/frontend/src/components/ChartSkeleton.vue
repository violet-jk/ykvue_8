<template>
  <div class="chart-skeleton">
    <!-- 玻璃态容器 -->
    <div class="glass-container">
      <!-- 标题骨架 -->
      <div class="skeleton-title">
        <div class="skeleton-line title-line">
          <div class="shimmer"></div>
        </div>
        <div class="skeleton-line subtitle-line">
          <div class="shimmer"></div>
        </div>
      </div>

      <!-- 图表区域骨架 -->
      <div class="skeleton-chart-area">
        <!-- Y轴标签骨架 -->
        <div class="skeleton-y-axis">
          <div class="skeleton-y-label" v-for="i in 6" :key="i">
            <div class="shimmer"></div>
          </div>
        </div>

        <!-- 图表主体骨架 -->
        <div class="skeleton-chart-main">
          <!-- 动态网格线骨架 -->
          <div class="skeleton-grid">
            <div class="skeleton-grid-line horizontal" v-for="i in 6" :key="'h' + i"></div>
            <div class="skeleton-grid-line vertical" v-for="i in 10" :key="'v' + i"></div>
          </div>

          <!-- 曲线骨架 - 增强版 -->
          <div class="skeleton-lines">
            <svg class="skeleton-line-chart" viewBox="0 0 400 200">
              <!-- 渐变定义 -->
              <defs>
                <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" style="stop-color:#5cadff;stop-opacity:1">
                    <animate attributeName="stop-color" values="#5cadff;#78b9ff;#92c7ff;#5cadff" dur="3s"
                             repeatCount="indefinite"/>
                  </stop>
                  <stop offset="100%" style="stop-color:#78b9ff;stop-opacity:1">
                    <animate attributeName="stop-color" values="#78b9ff;#92c7ff;#5cadff;#78b9ff" dur="3s"
                             repeatCount="indefinite"/>
                  </stop>
                </linearGradient>
                <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" style="stop-color:#78b9ff;stop-opacity:1">
                    <animate attributeName="stop-color" values="#78b9ff;#92c7ff;#a8daff;#78b9ff" dur="3.5s"
                             repeatCount="indefinite"/>
                  </stop>
                  <stop offset="100%" style="stop-color:#92c7ff;stop-opacity:1">
                    <animate attributeName="stop-color" values="#92c7ff;#a8daff;#78b9ff;#92c7ff" dur="3.5s"
                             repeatCount="indefinite"/>
                  </stop>
                </linearGradient>
                <linearGradient id="gradient3" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" style="stop-color:#409eff;stop-opacity:1">
                    <animate attributeName="stop-color" values="#409eff;#5cadff;#78b9ff;#409eff" dur="4s"
                             repeatCount="indefinite"/>
                  </stop>
                  <stop offset="100%" style="stop-color:#5cadff;stop-opacity:1">
                    <animate attributeName="stop-color" values="#5cadff;#78b9ff;#409eff;#5cadff" dur="4s"
                             repeatCount="indefinite"/>
                  </stop>
                </linearGradient>

                <!-- 发光滤镜 -->
                <filter id="glow">
                  <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
              </defs>

              <!-- 第一条曲线 - 稳定上升趋势 -->
              <path
                  class="skeleton-curve skeleton-curve-1"
                  d="M5,170 Q80,150 160,120 Q240,90 320,60 Q360,45 395,30"
                  fill="none"
                  stroke="url(#gradient1)"
                  stroke-width="3"
                  filter="url(#glow)"
              />
              <!-- 第二条曲线 - 波浪形趋势 -->
              <path
                  class="skeleton-curve skeleton-curve-2"
                  d="M5,140 Q60,100 120,90 Q180,80 240,100 Q300,120 360,110 Q380,105 395,100"
                  fill="none"
                  stroke="url(#gradient2)"
                  stroke-width="3"
                  filter="url(#glow)"
              />
              <!-- 第三条曲线 - 先降后升趋势 -->
              <path
                  class="skeleton-curve skeleton-curve-3"
                  d="M5,80 Q80,110 160,130 Q240,150 320,140 Q360,135 395,125"
                  fill="none"
                  stroke="url(#gradient3)"
                  stroke-width="3"
                  filter="url(#glow)"
              />
            </svg>
          </div>
        </div>
      </div>

      <!-- X轴标签骨架 -->
      <div class="skeleton-x-axis">
        <div class="skeleton-x-label" v-for="i in 8" :key="i">
          <div class="shimmer"></div>
        </div>
      </div>

      <!-- 图例骨架 -->
      <div class="skeleton-legend">
        <div class="skeleton-legend-item" v-for="i in 3" :key="i">
          <div class="skeleton-legend-color">
            <div class="pulse-ring"></div>
          </div>
          <div class="skeleton-legend-text">
            <div class="shimmer"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载动画效果 - 玻璃态 -->
    <div class="skeleton-overlay">
      <div class="glass-card">
        <div class="loading-icon">
          <div class="spinner">
            <div class="spinner-ring"></div>
            <div class="spinner-ring"></div>
            <div class="spinner-ring"></div>
          </div>
        </div>
        <div class="skeleton-loading-text">正在生成图表</div>
        <div class="skeleton-dots">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
// 无需额外逻辑，纯展示组件
</script>

<style scoped>
.chart-skeleton {
  width: 100%;
  height: 700px;
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 50%, #e1f5fe 100%);
  background-size: 200% 200%;
  animation: gradient-shift 10s ease infinite;
  border-radius: 16px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  padding: 0;
  box-sizing: border-box;
}

/* 背景渐变动画 */
@keyframes gradient-shift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}

/* 玻璃态容器 */
.glass-container {
  position: relative;
  z-index: 2;
  flex: 1;
  margin: 20px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 4px 20px 0 rgba(31, 38, 135, 0.15),
  inset 0 1px 0 0 rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
}

/* 标题骨架 */
.skeleton-title {
  text-align: center;
  margin-bottom: 20px;
}

.skeleton-line {
  position: relative;
  background: rgba(64, 158, 255, 0.35);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(64, 158, 255, 0.4);
}

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
  animation: shimmer-slide 2s infinite;
}

@keyframes shimmer-slide {
  0% {
    left: -100%;
  }
  100% {
    left: 200%;
  }
}

.title-line {
  height: 28px;
  width: 250px;
  margin: 0 auto 12px;
}

.subtitle-line {
  height: 18px;
  width: 180px;
  margin: 0 auto;
}

/* 图表区域骨架 */
.skeleton-chart-area {
  flex: 1;
  display: flex;
  position: relative;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 12px;
  padding: 10px;
  backdrop-filter: blur(10px);
}

.skeleton-y-axis {
  width: 40px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 10px 0;
}

.skeleton-y-label {
  height: 14px;
  width: 32px;
  position: relative;
  background: rgba(64, 158, 255, 0.35);
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.skeleton-chart-main {
  flex: 1;
  position: relative;
  margin: 0 10px;
}

/* 网格线骨架 - 动态效果 */
.skeleton-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.skeleton-grid-line {
  position: absolute;
  background: linear-gradient(90deg,
  rgba(64, 158, 255, 0.2) 0%,
  rgba(64, 158, 255, 0.4) 50%,
  rgba(64, 158, 255, 0.2) 100%
  );
  background-size: 200% 100%;
  animation: grid-shimmer 3s infinite linear;
}

@keyframes grid-shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.skeleton-grid-line.horizontal {
  width: 100%;
  height: 1px;
  left: 0;
}

.skeleton-grid-line.vertical {
  height: 100%;
  width: 1px;
  top: 0;
}

.skeleton-grid-line.horizontal:nth-child(1) {
  top: 0%;
  animation-delay: 0s;
}

.skeleton-grid-line.horizontal:nth-child(2) {
  top: 20%;
  animation-delay: 0.2s;
}

.skeleton-grid-line.horizontal:nth-child(3) {
  top: 40%;
  animation-delay: 0.4s;
}

.skeleton-grid-line.horizontal:nth-child(4) {
  top: 60%;
  animation-delay: 0.6s;
}

.skeleton-grid-line.horizontal:nth-child(5) {
  top: 80%;
  animation-delay: 0.8s;
}

.skeleton-grid-line.horizontal:nth-child(6) {
  top: 100%;
  animation-delay: 1s;
}

.skeleton-grid-line.vertical:nth-child(7) {
  left: 0%;
  animation-delay: 0.1s;
}

.skeleton-grid-line.vertical:nth-child(8) {
  left: 12.5%;
  animation-delay: 0.2s;
}

.skeleton-grid-line.vertical:nth-child(9) {
  left: 25%;
  animation-delay: 0.3s;
}

.skeleton-grid-line.vertical:nth-child(10) {
  left: 37.5%;
  animation-delay: 0.4s;
}

.skeleton-grid-line.vertical:nth-child(11) {
  left: 50%;
  animation-delay: 0.5s;
}

.skeleton-grid-line.vertical:nth-child(12) {
  left: 62.5%;
  animation-delay: 0.6s;
}

.skeleton-grid-line.vertical:nth-child(13) {
  left: 75%;
  animation-delay: 0.7s;
}

.skeleton-grid-line.vertical:nth-child(14) {
  left: 87.5%;
  animation-delay: 0.8s;
}

.skeleton-grid-line.vertical:nth-child(15) {
  left: 100%;
  animation-delay: 0.9s;
}

/* 曲线骨架 */
.skeleton-lines {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2;
}

.skeleton-line-chart {
  width: 100%;
  height: 100%;
}

.skeleton-curve {
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
  animation: draw-line 3s ease-out forwards, pulse-line 2s infinite ease-in-out;
}

@keyframes draw-line {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes pulse-line {
  0%, 100% {
    opacity: 0.7;
    filter: drop-shadow(0 0 2px currentColor);
  }
  50% {
    opacity: 1;
    filter: drop-shadow(0 0 8px currentColor);
  }
}

.skeleton-curve-1 {
  animation-delay: 0s, 0s;
}

.skeleton-curve-2 {
  animation-delay: 0.5s, 0.3s;
}

.skeleton-curve-3 {
  animation-delay: 1s, 0.6s;
}

/* X轴标签骨架 */
.skeleton-x-axis {
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
  padding: 0 50px;
}

.skeleton-x-label {
  height: 14px;
  width: 32px;
  position: relative;
  background: rgba(64, 158, 255, 0.35);
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* 图例骨架 */
.skeleton-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 20px;
}

.skeleton-legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
  border: 1px solid rgba(64, 158, 255, 0.4);
  backdrop-filter: blur(10px);
}

.skeleton-legend-color {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff, #5cadff);
  position: relative;
  box-shadow: 0 0 10px rgba(64, 158, 255, 0.5);
  animation: legend-pulse 2s infinite;
}

@keyframes legend-pulse {
  0%, 100% {
    box-shadow: 0 0 10px rgba(64, 158, 255, 0.5);
  }
  50% {
    box-shadow: 0 0 18px rgba(64, 158, 255, 0.7);
  }
}

.pulse-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  border: 2px solid rgba(64, 158, 255, 0.6);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: pulse-ring-expand 2s infinite;
}

@keyframes pulse-ring-expand {
  0% {
    width: 100%;
    height: 100%;
    opacity: 1;
  }
  100% {
    width: 200%;
    height: 200%;
    opacity: 0;
  }
}

.skeleton-legend-text {
  height: 14px;
  width: 70px;
  position: relative;
  background: rgba(64, 158, 255, 0.3);
  border-radius: 4px;
  overflow: hidden;
}

/* 加载覆盖层 - 玻璃态 */
.skeleton-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  animation: float-overlay 3s ease-in-out infinite;
}

@keyframes float-overlay {
  0%, 100% {
    transform: translate(-50%, -50%) translateY(0);
  }
  50% {
    transform: translate(-50%, -50%) translateY(-10px);
  }
}

.glass-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(30px);
  padding: 30px 40px;
  border-radius: 20px;
  box-shadow: 0 4px 20px 0 rgba(31, 38, 135, 0.2),
  inset 0 1px 0 0 rgba(255, 255, 255, 0.9),
  0 0 0 1px rgba(255, 255, 255, 0.6);
  text-align: center;
  border: 2px solid rgba(255, 255, 255, 0.7);
}

.loading-icon {
  margin-bottom: 20px;
  display: flex;
  justify-content: center;
}

.spinner {
  width: 60px;
  height: 60px;
  position: relative;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top-color: #409eff;
  border-radius: 50%;
  animation: spin 1.5s linear infinite;
}

.spinner-ring:nth-child(1) {
  border-top-color: #409eff;
  animation-duration: 1.5s;
}

.spinner-ring:nth-child(2) {
  border-top-color: #5cadff;
  animation-duration: 2s;
  animation-direction: reverse;
  width: 80%;
  height: 80%;
  top: 10%;
  left: 10%;
}

.spinner-ring:nth-child(3) {
  border-top-color: #78b9ff;
  animation-duration: 2.5s;
  width: 60%;
  height: 60%;
  top: 20%;
  left: 20%;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.skeleton-loading-text {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(90deg, #409eff, #5cadff, #78b9ff, #409eff);
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: text-gradient 3s linear infinite;
  margin-bottom: 12px;
  text-shadow: 0 0 15px rgba(64, 158, 255, 0.4);
}

@keyframes text-gradient {
  0% {
    background-position: 0% center;
  }
  100% {
    background-position: 200% center;
  }
}

.skeleton-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff, #5cadff);
  box-shadow: 0 0 15px rgba(64, 158, 255, 0.6);
  animation: bounce-dot 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
  background: linear-gradient(135deg, #409eff, #5cadff);
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
  background: linear-gradient(135deg, #5cadff, #78b9ff);
}

.dot:nth-child(3) {
  animation-delay: 0s;
  background: linear-gradient(135deg, #78b9ff, #92c7ff);
}

@keyframes bounce-dot {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1.3);
    opacity: 1;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chart-skeleton {
    padding: 0;
  }

  .glass-container {
    margin: 10px;
    padding: 15px;
  }

  .skeleton-legend {
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }

  .skeleton-x-axis {
    padding: 0 20px;
  }

  .glass-card {
    padding: 20px 30px;
  }
}
</style>

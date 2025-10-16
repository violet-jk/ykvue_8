<template>
  <el-container class="layout-container">
    <el-container>
      <el-main class="main-content">
        <router-view>
        </router-view>
        <!-- 返回顶部按钮 - 全局可用 -->
        <el-backtop :right="40" :bottom="40" :visibility-height="300" target=".main-content" class="custom-backtop">
          <div class="backtop-content">
            <el-icon size="30">
              <CaretTop />
            </el-icon>
          </div>
        </el-backtop>
      </el-main>
    </el-container>
  </el-container>
</template>

<script lang="ts" setup>
import {
  CaretTop,
} from '@element-plus/icons-vue'

</script>

<style scoped>
/* ========== 整体布局容器 ========== */
.layout-container {
  height: 98vh;
  animation: gradient-shift 15s ease infinite;
}

</style>

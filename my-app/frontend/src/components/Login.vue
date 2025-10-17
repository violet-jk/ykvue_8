<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <span>系统登录</span>
        </div>
      </template>

      <el-form
        :model="loginForm"
        :rules="rules"
        ref="loginFormRef"
        label-width="0"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="apiKey">
          <el-input
            v-model="loginForm.apiKey"
            type="password"
            placeholder="请输入API密钥"
            show-password
            size="large"
            clearable
            ref="apiKeyInputRef"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            style="width: 100%"
            size="large"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const loginFormRef = ref<FormInstance>()
const loading = ref(false)
const apiKeyInputRef = ref()

const loginForm = reactive({
  apiKey: ''
})

const rules = reactive<FormRules>({
  apiKey: [
    { required: true, message: '请输入API密钥', trigger: 'blur' }
  ]
})

const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ api_key: loginForm.apiKey })
        })

        const data = await response.json()

        if (response.ok && data.success) {
          // 保存token到localStorage
          localStorage.setItem('auth_token', data.token)
          ElMessage.success('登录成功！')

          // 跳转到首页
          router.push('/')
        } else {
          ElMessage.error(data.message || 'API密钥错误')
        }
      } catch (error) {
        console.error('登录失败:', error)
        ElMessage.error('登录失败，请检查网络连接')
      } finally {
        loading.value = false
      }
    }
  })
}

// 页面加载完成后自动聚焦到输入框
onMounted(() => {
  nextTick(() => {
    if (apiKeyInputRef.value) {
      apiKeyInputRef.value.focus()
    }
  })
})
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #0a9792 0%, #0270b6 100%);
}

.login-card {
  width: 400px;
  max-width: 90%;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.card-header {
  text-align: center;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

:deep(.el-card__header) {
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

:deep(.el-form-item) {
  margin-bottom: 24px;
}

:deep(.el-input__wrapper) {
  padding: 12px 15px;
}
</style>

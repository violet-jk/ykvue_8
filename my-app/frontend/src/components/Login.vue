<template>
  <div
    class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 p-4"
  >
    <!-- 背景装饰 -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div
        class="absolute -top-40 -right-40 w-80 h-80 bg-blue-400 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"
      ></div>
      <div
        class="absolute -bottom-40 -left-40 w-80 h-80 bg-indigo-400 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"
      ></div>
      <div
        class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-cyan-400 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"
      ></div>
    </div>

    <!-- 登录卡片 -->
    <div class="relative w-full max-w-md">
      <div
        class="bg-white/95 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20"
      >
        <!-- Logo 和标题 -->
        <div class="text-center mb-8">
          <div
            class="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl shadow-lg mb-4"
          >
            <svg
              class="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 10V3L4 14h7v7l9-11h-7z"
              ></path>
            </svg>
          </div>
          <h1 class="text-3xl font-bold text-slate-800 mb-2">电解槽监控系统</h1>
          <p class="text-slate-500 text-sm">请输入 API 密钥登录系统</p>
        </div>

        <!-- 登录表单 -->
        <form @submit.prevent="handleLogin" class="space-y-6">
          <!-- API密钥输入框 -->
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">
              API 密钥
            </label>
            <div class="relative">
              <div
                class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"
              >
                <svg
                  class="h-5 w-5 text-slate-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  ></path>
                </svg>
              </div>
              <input
                v-model="loginForm.apiKey"
                :type="showPassword ? 'text' : 'password'"
                ref="apiKeyInputRef"
                placeholder="请输入API密钥"
                class="block w-full pl-10 pr-12 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-slate-900 placeholder-slate-400"
                :class="{ 'border-red-300': errorMessage }"
                @input="errorMessage = ''"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 transition-colors"
              >
                <svg
                  v-if="!showPassword"
                  class="h-5 w-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  ></path>
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  ></path>
                </svg>
                <svg
                  v-else
                  class="h-5 w-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                  ></path>
                </svg>
              </button>
            </div>
            <p v-if="errorMessage" class="mt-2 text-sm text-red-600">
              {{ errorMessage }}
            </p>
          </div>

          <!-- 登录按钮 -->
          <button
            type="submit"
            :disabled="loading || !loginForm.apiKey"
            class="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-3 px-4 rounded-lg font-medium shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center gap-2"
          >
            <svg
              v-if="loading"
              class="animate-spin h-5 w-5 text-white"
              fill="none"
              viewBox="0 0 24 24"
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
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <span>{{ loading ? "登录中..." : "登录" }}</span>
          </button>
        </form>

        <!-- 底部提示 -->
        <div class="mt-6 text-center">
          <p class="text-xs text-slate-500">请联系管理员获取 API 密钥</p>
        </div>
      </div>

      <!-- 版权信息 -->
      <div class="text-center mt-6">
        <p class="text-white/80 text-sm">© 2025 电解槽电压监控系统</p>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, nextTick } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

const router = useRouter();
const loading = ref(false);
const apiKeyInputRef = ref();
const showPassword = ref(false);
const errorMessage = ref("");

const loginForm = reactive({
  apiKey: "",
});

const handleLogin = async () => {
  // 简单验证
  if (!loginForm.apiKey.trim()) {
    errorMessage.value = "请输入API密钥";
    return;
  }

  loading.value = true;
  errorMessage.value = "";

  try {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ api_key: loginForm.apiKey }),
    });

    const data = await response.json();

    if (response.ok && data.success) {
      // 保存token到localStorage
      localStorage.setItem("auth_token", data.token);
      ElMessage.success("登录成功！");

      // 跳转到首页
      router.push("/");
    } else {
      errorMessage.value = data.message || "API密钥错误";
      ElMessage.error(data.message || "API密钥错误");
    }
  } catch (error) {
    console.error("登录失败:", error);
    errorMessage.value = "登录失败，请检查网络连接";
    ElMessage.error("登录失败，请检查网络连接");
  } finally {
    loading.value = false;
  }
};

// 页面加载完成后自动聚焦到输入框
onMounted(() => {
  nextTick(() => {
    if (apiKeyInputRef.value) {
      apiKeyInputRef.value.focus();
    }
  });
});
</script>

<style scoped>
/* 背景动画 */
@keyframes blob {
  0% {
    transform: translate(0px, 0px) scale(1);
  }
  33% {
    transform: translate(30px, -50px) scale(1.1);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.9);
  }
  100% {
    transform: translate(0px, 0px) scale(1);
  }
}

.animate-blob {
  animation: blob 7s infinite;
}

.animation-delay-2000 {
  animation-delay: 2s;
}

.animation-delay-4000 {
  animation-delay: 4s;
}
</style>

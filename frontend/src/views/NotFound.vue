<template>
  <div class="not-found">
    <div class="code">404</div>
    <div class="msg">找不到这片青苗</div>
    <el-button type="primary" @click="$router.push('/login')">返回登录</el-button>
  </div>
</template>

<script setup lang="ts"></script>

<style lang="scss" scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  gap: 16px;
  background: #f5f7fa;
  .code {
    font-size: 96px;
    font-weight: 800;
    background: linear-gradient(135deg, #22c55e, #0ea5e9);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }
  .msg {
    color: #64748b;
    margin-bottom: 8px;
  }
}
</style>

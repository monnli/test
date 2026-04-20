<template>
  <el-dialog
    v-model="visible"
    title="紧急心理援助"
    width="520px"
    :close-on-click-modal="false"
    :show-close="true"
    align-center
  >
    <div class="crisis-content">
      <div class="alert-icon">
        <el-icon :size="48" color="#ef4444"><WarningFilled /></el-icon>
      </div>
      <h3>检测到高风险表达</h3>
      <p class="msg">
        系统检测到对话中出现高风险表达。请立即联系信任的成年人或专业心理援助热线。
      </p>

      <div class="hotline-grid">
        <div class="hotline-card primary">
          <div class="num">12320</div>
          <div class="desc">国家公共卫生热线<br />24 小时心理援助</div>
        </div>
        <div class="hotline-card">
          <div class="num">400-161-9995</div>
          <div class="desc">北京心理危机研究中心<br />24 小时</div>
        </div>
        <div class="hotline-card">
          <div class="num">021-64383562</div>
          <div class="desc">上海市心理援助热线<br />24 小时</div>
        </div>
      </div>

      <el-alert type="info" :closable="false" class="hint">
        <template #title>
          系统已自动通知本班心理老师与班主任。
        </template>
      </el-alert>

      <div class="actions">
        <el-button type="primary" size="large" @click="visible = false">我已知晓</el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { WarningFilled } from '@element-plus/icons-vue'

const visible = ref(false)

defineExpose({
  show: () => {
    visible.value = true
  },
})
</script>

<style lang="scss" scoped>
.crisis-content {
  text-align: center;
  .alert-icon {
    margin-bottom: 12px;
  }
  h3 {
    color: #ef4444;
    margin: 0 0 12px;
  }
  .msg {
    color: #475569;
    line-height: 1.6;
  }
}
.hotline-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin: 20px 0;
}
.hotline-card {
  padding: 16px 8px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  &.primary {
    border-color: #ef4444;
    background: linear-gradient(180deg, #fef2f2, #fff);
  }
  .num {
    font-size: 22px;
    font-weight: 700;
    color: #ef4444;
    letter-spacing: 1px;
  }
  .desc {
    margin-top: 6px;
    color: #64748b;
    font-size: 12px;
    line-height: 1.5;
  }
}
.hint {
  text-align: left;
}
.actions {
  margin-top: 20px;
}
</style>

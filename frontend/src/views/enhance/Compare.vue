<template>
  <div class="compare-page">
    <el-card shadow="never">
      <template #header>
        <span class="card-title">产品对比 · 我们与同类产品的差异</span>
      </template>

      <el-table :data="rows" stripe>
        <el-table-column prop="feature" label="能力维度" width="220" fixed>
          <template #default="{ row }">
            <strong>{{ row.feature }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="ours" label="青苗守护者">
          <template #default="{ row }">
            <span class="ours">{{ row.ours }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="a" label="商业产品 A" />
        <el-table-column prop="b" label="商业产品 B" />
        <el-table-column prop="c" label="校园 C" />
      </el-table>

      <el-divider>核心差异化亮点</el-divider>
      <el-row :gutter="16">
        <el-col :xs="24" :md="8" v-for="h in highlights" :key="h.title">
          <el-card shadow="hover" class="hl-card">
            <el-icon :size="32" color="#22c55e"><component :is="h.icon" /></el-icon>
            <h4>{{ h.title }}</h4>
            <p>{{ h.text }}</p>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { Aim, Lock, View } from '@element-plus/icons-vue'

const rows = [
  { feature: '多模态维度', ours: '✓ 5 维（视频+文本+量表+学业+对话）', a: '2 维', b: '3 维', c: '2 维' },
  { feature: '标准化心理量表', ours: '✓ 5 套（PHQ-9 / GAD-7 / SCARED / CES-DC / MHT）', a: '1 套', b: '2 套', c: '1 套' },
  { feature: '多维风险归因', ours: '✓ 可解释 AI，每条预警附原因清单', a: '✗ 黑盒', b: '⚠ 部分', c: '✗ 黑盒' },
  { feature: '本地化部署', ours: '✓ 支持，敏感数据可不出校门', a: '✗ 仅云端', b: '✓', c: '✓' },
  { feature: 'AI 心理对话', ours: '✓ 通义千问 + 风险词双保险', a: '✗', b: '✗', c: '✗' },
  { feature: '群体智能聚类', ours: '✓ K-Means 自动分群 + 画像', a: '✗', b: '✗', c: '✗' },
  { feature: '情绪趋势预测', ours: '✓ 7 天前瞻性预警', a: '✗', b: '⚠ 简单线性', c: '✗' },
  { feature: '干预闭环追踪', ours: '✓ 前后对比 + 时间轴', a: '✗', b: '✗', c: '✓' },
  { feature: '负责任 AI 设计', ours: '✓ 5 项原则 + 公开仪表盘', a: '✗', b: '✗', c: '✗' },
  { feature: '风险词库透明', ours: '✓ 完全公开', a: '✗', b: '✗', c: '✗' },
  { feature: '5 级精细 RBAC', ours: '✓ 数据范围按岗位严格隔离', a: '✓ 3 级', b: '✓ 4 级', c: '✓ 3 级' },
  { feature: '实时摄像头分析', ours: '✓ WebRTC + Canvas 叠加', a: '✗', b: '⚠', c: '✓' },
  { feature: 'PDF 报告 AI 生成', ours: '✓ 通义千问综合建议', a: '✓ 模板', b: '✓ 模板', c: '✗' },
  { feature: '危机干预热线联动', ours: '✓ 12320 一键展示', a: '✗', b: '✗', c: '✗' },
  { feature: '开源代码', ours: '✓ GitHub 公开', a: '✗', b: '✗', c: '✗' },
]

const highlights = [
  {
    icon: Aim,
    title: '可解释 AI',
    text: '业内首批做到「每条预警都附原因清单」的产品，告别黑盒。',
  },
  {
    icon: Lock,
    title: '负责任 AI',
    text: '5 项伦理原则 + 公开仪表盘，让评委、教师、家长都能审视我们的决策机制。',
  },
  {
    icon: View,
    title: '前瞻性预警',
    text: '基于 Holt 双参数指数平滑预测未来 7 天心理指数，从「事后处理」升级到「事前介入」。',
  },
]
</script>

<style lang="scss" scoped>
.compare-page {
  padding-bottom: 16px;
}
.card-title {
  font-weight: 600;
}
.ours {
  color: #22c55e;
  font-weight: 600;
}
.hl-card {
  margin-bottom: 16px;
  text-align: center;
  border-radius: 10px;
  border-top: 3px solid #22c55e;
  h4 {
    margin: 8px 0 4px;
    color: #0f172a;
  }
  p {
    color: #64748b;
    font-size: 13px;
    margin: 0;
    line-height: 1.6;
  }
}
</style>

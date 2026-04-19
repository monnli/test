<template>
  <el-card shadow="never">
    <el-alert
      type="info"
      :closable="false"
      title="角色为系统内置，权限规则在 M1 阶段固定。后续版本将支持权限点级别的可视化授权管理。"
      class="alert"
    />
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="角色名称" />
      <el-table-column prop="code" label="编码" />
      <el-table-column prop="description" label="说明" />
      <el-table-column prop="sort_order" label="排序" width="80" />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.is_builtin" type="success" effect="dark" size="small">内置</el-tag>
          <el-tag v-else type="info" size="small">自定义</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { listAllRoles, type RoleItem } from '@/api/users'

const items = ref<RoleItem[]>([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await listAllRoles()
    items.value = data.items
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
.alert {
  margin-bottom: 16px;
}
</style>

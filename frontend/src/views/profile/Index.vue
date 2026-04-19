<template>
  <div class="profile-page">
    <el-card shadow="never">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="基本信息" name="info">
          <div class="info-area">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="账号">{{ u?.username }}</el-descriptions-item>
              <el-descriptions-item label="姓名">{{ u?.real_name }}</el-descriptions-item>
              <el-descriptions-item label="角色">
                <el-tag
                  v-for="r in u?.roles"
                  :key="r.code"
                  size="small"
                  effect="plain"
                  class="role-tag"
                >
                  {{ r.name }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="所属学校 ID">{{ u?.school_id ?? '—' }}</el-descriptions-item>
              <el-descriptions-item label="手机">{{ u?.phone || '—' }}</el-descriptions-item>
              <el-descriptions-item label="邮箱">{{ u?.email || '—' }}</el-descriptions-item>
              <el-descriptions-item label="最后登录">{{ u?.last_login_at || '—' }}</el-descriptions-item>
              <el-descriptions-item label="账号状态">
                <el-tag :type="u?.is_active ? 'success' : 'danger'" effect="dark" size="small">
                  {{ u?.is_active ? '启用' : '禁用' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>

            <el-divider>数据可见范围</el-divider>
            <div class="scope-block" v-if="u?.data_scope">
              <el-tag v-if="u.data_scope.is_full" type="success" effect="dark" round>
                本校全部数据
              </el-tag>
              <template v-else>
                <div>可见学校：{{ u.data_scope.school_ids.join('、') || '—' }}</div>
                <div>可见年级：{{ (u.data_scope.grade_ids || []).join('、') || '—' }}</div>
                <div>可见班级：{{ (u.data_scope.class_ids || []).join('、') || '—' }}</div>
                <div>本班全科目：{{ u.data_scope.all_subjects_in_class_ids.join('、') || '—' }}</div>
                <div>
                  班级×科目精细授权：
                  <span v-if="!u.data_scope.subject_filters.length">—</span>
                  <el-tag
                    v-for="(t, idx) in u.data_scope.subject_filters"
                    :key="idx"
                    size="small"
                    effect="plain"
                    class="role-tag"
                  >
                    班级{{ t[0] }} × 科目{{ t[1] }}
                  </el-tag>
                </div>
              </template>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="修改密码" name="password">
          <el-form
            ref="pwdFormRef"
            :model="pwdForm"
            :rules="pwdRules"
            label-width="100px"
            style="max-width: 480px"
          >
            <el-form-item label="原密码" prop="old_password">
              <el-input v-model="pwdForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="pwdForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirm_password">
              <el-input v-model="pwdForm.confirm_password" type="password" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="submitting" @click="onChangePwd">
                提交
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

import { useUserStore } from '@/stores/user'
import { changePassword } from '@/api/auth'

const route = useRoute()
const userStore = useUserStore()
const u = computed(() => userStore.userInfo)

const activeTab = ref<string>((route.query.tab as string) || 'info')

const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})
const submitting = ref(false)
const pwdFormRef = ref<FormInstance>()

const pwdRules: FormRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, cb) =>
        value === pwdForm.new_password ? cb() : cb(new Error('两次输入不一致')),
      trigger: 'blur',
    },
  ],
}

async function onChangePwd() {
  if (!pwdFormRef.value) return
  await pwdFormRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await changePassword(pwdForm.old_password, pwdForm.new_password)
      ElMessage.success('密码已修改，请重新登录')
      await userStore.logout()
      window.location.href = '/login'
    } finally {
      submitting.value = false
    }
  })
}

onMounted(() => {
  if (!u.value) userStore.fetchMe()
})
</script>

<style lang="scss" scoped>
.profile-page {
  max-width: 1100px;
  margin: 0 auto;
}
.role-tag {
  margin-right: 6px;
  margin-bottom: 4px;
}
.scope-block > div {
  margin-bottom: 6px;
  color: #475569;
}
</style>

import { request } from './request'

export interface PageResult<T> {
  items: T[]
  total: number
  page?: number
  page_size?: number
}

export interface School {
  id: number
  name: string
  code: string | null
  address: string | null
  contact: string | null
  phone: string | null
  description: string | null
  created_at: string
}

export interface Grade {
  id: number
  school_id: number
  school_name: string | null
  name: string
  level: number
  class_count: number
}

export interface Clazz {
  id: number
  grade_id: number
  grade_name: string | null
  school_id: number | null
  name: string
  head_teacher_id: number | null
  head_teacher_name: string | null
  student_count: number
}

export interface Student {
  id: number
  student_no: string
  name: string
  gender: string
  birth_date: string | null
  avatar: string | null
  school_id: number
  grade_id: number
  class_id: number
  class_name: string | null
  parent_name: string | null
  parent_phone: string | null
  enrollment_date: string | null
  note: string | null
}

export interface Teacher {
  id: number
  user_id: number | null
  username: string | null
  teacher_no: string
  name: string
  gender: string
  school_id: number
  phone: string | null
  email: string | null
  title: string | null
  avatar: string | null
}

export interface Subject {
  id: number
  name: string
  code: string | null
  sort_order: number
}

export interface TeacherClassSubject {
  id: number
  teacher_id: number
  teacher_name: string | null
  class_id: number
  class_name: string | null
  grade_id: number | null
  grade_name: string | null
  subject_id: number
  subject_name: string | null
}

const list = <T>(url: string, params?: any) =>
  request<PageResult<T>>({ url, method: 'get', params })

// ---- 学校 ----
export const listSchools = (params?: any) => list<School>('/orgs/schools', params)
export const createSchool = (data: any) => request<School>({ url: '/orgs/schools', method: 'post', data })
export const updateSchool = (id: number, data: any) =>
  request<School>({ url: `/orgs/schools/${id}`, method: 'put', data })
export const deleteSchool = (id: number) =>
  request<void>({ url: `/orgs/schools/${id}`, method: 'delete' })

// ---- 年级 ----
export const listGrades = (params?: any) => list<Grade>('/orgs/grades', params)
export const createGrade = (data: any) => request<Grade>({ url: '/orgs/grades', method: 'post', data })
export const updateGrade = (id: number, data: any) =>
  request<Grade>({ url: `/orgs/grades/${id}`, method: 'put', data })
export const deleteGrade = (id: number) =>
  request<void>({ url: `/orgs/grades/${id}`, method: 'delete' })

// ---- 班级 ----
export const listClasses = (params?: any) => list<Clazz>('/orgs/classes', params)
export const createClass = (data: any) => request<Clazz>({ url: '/orgs/classes', method: 'post', data })
export const updateClass = (id: number, data: any) =>
  request<Clazz>({ url: `/orgs/classes/${id}`, method: 'put', data })
export const deleteClass = (id: number) =>
  request<void>({ url: `/orgs/classes/${id}`, method: 'delete' })

// ---- 学生 ----
export const listStudents = (params?: any) =>
  request<PageResult<Student>>({ url: '/orgs/students', method: 'get', params })
export const createStudent = (data: any) => request<Student>({ url: '/orgs/students', method: 'post', data })
export const updateStudent = (id: number, data: any) =>
  request<Student>({ url: `/orgs/students/${id}`, method: 'put', data })
export const deleteStudent = (id: number) =>
  request<void>({ url: `/orgs/students/${id}`, method: 'delete' })
export const getStudentDetail = (id: number) =>
  request<Student>({ url: `/orgs/students/${id}`, method: 'get' })

// ---- 教师 ----
export const listTeachers = (params?: any) => list<Teacher>('/orgs/teachers', params)
export const createTeacher = (data: any) => request<Teacher>({ url: '/orgs/teachers', method: 'post', data })
export const updateTeacher = (id: number, data: any) =>
  request<Teacher>({ url: `/orgs/teachers/${id}`, method: 'put', data })
export const deleteTeacher = (id: number) =>
  request<void>({ url: `/orgs/teachers/${id}`, method: 'delete' })

// ---- 科目 ----
export const listSubjects = () => list<Subject>('/orgs/subjects')
export const createSubject = (data: any) => request<Subject>({ url: '/orgs/subjects', method: 'post', data })
export const updateSubject = (id: number, data: any) =>
  request<Subject>({ url: `/orgs/subjects/${id}`, method: 'put', data })
export const deleteSubject = (id: number) =>
  request<void>({ url: `/orgs/subjects/${id}`, method: 'delete' })

// ---- 任课关系 ----
export const listTcs = (params?: any) => list<TeacherClassSubject>('/orgs/teacher-class-subjects', params)
export const createTcs = (data: any) =>
  request<TeacherClassSubject>({ url: '/orgs/teacher-class-subjects', method: 'post', data })
export const deleteTcs = (id: number) =>
  request<void>({ url: `/orgs/teacher-class-subjects/${id}`, method: 'delete' })

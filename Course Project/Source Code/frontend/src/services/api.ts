import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

// Auth
export const login = (email: string, password: string) =>
  api.post('/auth/token', new URLSearchParams({ username: email, password }), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })

export const register = (data: { name: string; email: string; password: string; role: string; course_ids?: number[] }) =>
  api.post('/auth/register', data)

export const getAvailableCourses = () => api.get('/auth/courses')

export const getMe = () => api.get('/auth/me')

export const changePassword = (current_password: string, new_password: string) =>
  api.post('/auth/change-password', { current_password, new_password })

// Courses
export const getCourses = () => api.get('/courses')
export const getCourseCatalog = () => api.get('/courses/catalog/all')
export const updateMyEnrollments = (course_ids: number[]) => api.post('/courses/my-enrollments', { course_ids })
export const getCourse = (id: number) => api.get(`/courses/${id}`)
export const createCourse = (data: { name: string; code: string; description: string }) =>
  api.post('/courses', data)
export const getStudents = (courseId: number) => api.get(`/courses/${courseId}/students`)
export const enrollStudents = (courseId: number, student_ids: number[]) =>
  api.post(`/courses/${courseId}/enroll`, { student_ids })
export const getGroups = (courseId: number) => api.get(`/courses/${courseId}/groups`)
export const createGroup = (courseId: number, data: { name: string; description: string; member_ids: number[] }) =>
  api.post(`/courses/${courseId}/groups`, data)

// Notes & Curriculum Hierarchy
export const getNotes = (courseId: number, unit?: string) =>
  api.get(`/notes/courses/${courseId}/notes`, { params: unit ? { unit } : {} })
export const getCourseCurriculum = (courseId: number) =>
  api.get(`/notes/courses/${courseId}/curriculum`)
export const uploadLessonPlan = (courseId: number, formData: FormData) =>
  api.post(`/notes/courses/${courseId}/lesson-plan`, formData)
export const downloadLessonPlan = (courseId: number) =>
  api.get(`/notes/courses/${courseId}/lesson-plan/download`, { responseType: 'blob' })
export const uploadLessonNote = (courseId: number, lessonId: number, formData: FormData) =>
  api.post(`/notes/courses/${courseId}/lessons/${lessonId}/notes`, formData)
export const uploadChapterNote = (courseId: number, chapterId: number, formData: FormData) =>
  api.post(`/notes/courses/${courseId}/chapters/${chapterId}/notes`, formData)
export const deleteNote = (noteId: number) =>
  api.delete(`/notes/notes/${noteId}`)
export const uploadNote = (courseId: number, formData: FormData) =>
  api.post(`/notes/courses/${courseId}/notes`, formData)
export const downloadNote = (noteId: number) =>
  api.get(`/notes/notes/${noteId}/download`, { responseType: 'blob' })
export const getNoteVersions = (noteId: number) => api.get(`/notes/notes/${noteId}/versions`)
export const restoreNoteVersion = (noteId: number) => api.post(`/notes/notes/${noteId}/restore`)

// Assignments
export const getAssignments = (courseId: number, status?: string) =>
  api.get(`/courses/${courseId}/assignments`, { params: status ? { status } : {} })
export const createAssignment = (courseId: number, data: object) =>
  api.post(`/courses/${courseId}/assignments`, data)
export const publishAssignment = (courseId: number, assignmentId: number) =>
  api.post(`/courses/${courseId}/assignments/${assignmentId}/publish`)
export const getReminders = (courseId: number) => api.get(`/courses/${courseId}/reminders`)

// Submissions
export const submitAssignment = (assignmentId: number, formData: FormData) =>
  api.post(`/assignments/${assignmentId}/submit`, formData)
export const getSubmissions = (assignmentId: number) =>
  api.get(`/assignments/${assignmentId}/submissions`)
export const downloadSubmission = (submissionId: number) =>
  api.get(`/submissions/${submissionId}/download`, { responseType: 'blob' })
export const getSubmissionContent = (submissionId: number) =>
  api.get(`/submissions/${submissionId}/content`)

// Grades
export const runGrading = (courseId: number, assignmentId: number) =>
  api.post(`/courses/${courseId}/assignments/${assignmentId}/run-grading`)
export const gradeSingleSubmission = (submissionId: number) =>
  api.post(`/submissions/${submissionId}/grade`)
export const getPendingGrades = (courseId: number) => api.get(`/courses/${courseId}/grades/pending`)
export const approveGrade = (gradeId: number, data: { final_marks?: number; final_feedback?: string }) =>
  api.post(`/grades/${gradeId}/approve`, data)
export const rollbackGrade = (gradeId: number) => api.post(`/grades/${gradeId}/rollback`)
export const bulkApprove = (grade_ids: number[]) => api.post('/grades/bulk-approve', { grade_ids })
export const getStudentGrades = (studentId: number) => api.get(`/students/${studentId}/grades`)
export const nlQuery = (courseId: number, question: string, history?: { role: string; content: string }[]) =>
  api.post(`/courses/${courseId}/query`, { question, history })

// Milestones
export const getMilestones = (courseId: number) => api.get(`/courses/${courseId}/milestones`)
export const createMilestone = (courseId: number, data: object) =>
  api.post(`/courses/${courseId}/milestones`, data)
export const deleteMilestone = (courseId: number, milestoneId: number) =>
  api.delete(`/courses/${courseId}/milestones/${milestoneId}`)
export const getMilestoneSummary = (courseId: number) => api.get(`/courses/${courseId}/milestones/summary`)
export const getMyMilestoneSummary = (courseId: number) => api.get(`/courses/${courseId}/milestones/my-summary`)
export const submitMilestoneProgress = (courseId: number, milestoneId: number, formData: FormData) =>
  api.post(`/courses/${courseId}/milestones/${milestoneId}/submit`, formData)
export const approveMilestoneProgress = (courseId: number, milestoneId: number, groupId: number) =>
  api.post(`/courses/${courseId}/milestones/${milestoneId}/approve-group`, { group_id: groupId, milestone_id: milestoneId })
export const submitProjectFeedback = (courseId: number, data: { group_id: number; milestone_id?: number | null; category: string; feedback_text: string }) =>
  api.post(`/courses/${courseId}/feedback`, data)
export const getProjectFeedback = (courseId: number, params?: { milestone_id?: number; category?: string }) =>
  api.get(`/courses/${courseId}/feedback`, { params })

// Audit
export const getAuditLog = (runId?: string) => api.get('/audit', { params: runId ? { run_id: runId } : {} })

// ============================================================================
// Labs 1 to 15 Interactive Workbench & Live Demonstration API
// ============================================================================

// Generic Runner for all 15 Lab Demos
export const getLabDemo = (labNumber: number) => api.get(`/lab${labNumber}/demo`)

// Lab 1: Planner Loop (Clarify -> Propose -> Revise -> Lock)
export const clarifyPlan = (request: string) => api.post('/lab1/clarify', { request })
export const proposePlan = (clarified_context: object, custom_title?: string) =>
  api.post('/lab1/propose', { clarified_context, custom_title })
export const revisePlan = (current_plan: object, feedback: string) =>
  api.post('/lab1/revise', { current_plan, feedback })
export const lockPlan = (plan: object) => api.post('/lab1/lock', { plan })

// Lab 2: Tool Execution
export const toolReadNotes = (courseId: number, unit?: string) =>
  api.get('/lab2/read-notes', { params: { course_id: courseId, unit } })
export const toolReadRubric = (assignmentId: number) =>
  api.get('/lab2/read-rubric', { params: { assignment_id: assignmentId } })
export const toolComputeDeadline = (submittedAt: string, dueDate: string) =>
  api.post('/lab2/compute-deadline', { submitted_at: submittedAt, due_date: dueDate })
export const toolVerifySimilarity = (score: number, threshold?: number) =>
  api.post('/lab2/verify-similarity', { similarity_score: score, threshold })

// Lab 3: Reusable Skills
export const executeCourseSkill = (skillName: string, inputs: object) =>
  api.post('/lab3/execute-skill', { skill_name: skillName, inputs })
export const executePolymorphicSkill = (skillName: string, courses: object[]) =>
  api.post('/lab3/execute-polymorphic', { skill_name: skillName, courses })

// Lab 4: Memory Architecture
export const runMemoryWorkflow = (runId: string, candidate: object, tags?: object) =>
  api.post('/lab4/run-workflow', { run_id: runId, candidate_submission: candidate, query_tags: tags })
export const retrieveSimilaritySearch = (codeSnippet: string, k?: number, threshold?: number) =>
  api.post('/lab4/similarity-search', { code_snippet: codeSnippet, k, threshold })

// Lab 5: FastMCP Connector
export const getMcpNotes = (courseId: number) => api.get('/lab5/notes', { params: { course_id: courseId } })
export const getMcpRubric = (assignmentId: number) => api.get(`/lab5/rubric/${assignmentId}`)
export const getMcpSubmissions = (assignmentId: number) => api.get(`/lab5/submissions/${assignmentId}`)

// Lab 7: LangGraph 9-Node Pipeline
export const runLab7Pipeline = (data: { course_id: number; assignment_id: number; rubric_criteria?: object }) =>
  api.post('/lab7/run', data)
export const facultyApproveLab7 = (execution_id: string, faculty_id: number, decision: string, notes?: string) =>
  api.post('/lab7/faculty-approve', { execution_id, faculty_id, decision, notes })
export const getLab7State = (execution_id: string) => api.get(`/lab7/state/${execution_id}`)

// Lab 8: Swarm Pipeline
export const runLab8Swarm = (courseId: number, assignmentId: number, parallelCount: number = 3) =>
  api.post('/lab8/run', { course_id: courseId, assignment_id: assignmentId, parallel_count: parallelCount })

// Lab 9: Self-Healing Diagnostic
export const runLab9Healing = (data: { run_id: string; trigger_defect?: boolean }) =>
  api.post('/lab9/run', data)

// Lab 10: Deep Research with Citations
export const runLab10Research = (data: { course_id: number; topic: string; max_iterations?: number }) =>
  api.post('/lab10/run', data)

// Lab 11: Budget & Rate Limiting Governance
export const runLab11Governance = (data: { token_allowance?: number; calls_per_minute?: number; test_spike?: boolean }) =>
  api.post('/lab11/run', data)

// Lab 12: SDLC Acceptance Factory (12/12 gates)
export const runLab12Factory = (data: { course_id: number; require_strict?: boolean }) =>
  api.post('/lab12/run', data)

// Lab 13: Domain Specialists
export const runLab13Specialists = (domain: string, itemType: string) =>
  api.post('/lab13/run', { domain, item_type: itemType })

// Lab 14: End-to-End Capstone
export const runCapstonePipeline = (course_id: number, faculty_id: number, request_text: string, domain?: string) =>
  api.post('/lab14/run', { course_id, faculty_id, request_text, domain })
export const approveCapstone = (session_id: string, faculty_id: number, faculty_name: string) =>
  api.post('/lab14/approve', { session_id, faculty_id, faculty_name })
export const publishCapstone = (session_id: string) =>
  api.post('/lab14/publish', { session_id })
export const rollbackCapstone = (session_id: string) =>
  api.post('/lab14/rollback', { session_id })

// Lab 15: Examiner Live Defense & Multi-Agent Stress Benchmark
export const getLab15Readiness = () => api.get('/lab15/readiness')
export const runLab15StressTest = (concurrency: number = 20, iterations: number = 2) =>
  api.post('/lab15/stress-test', { concurrency, iterations })
export const runLab15AdversarialDefense = (attack_index?: number) =>
  api.post('/lab15/adversarial-defense', { attack_index })
export const getLab15Certificate = () => api.get('/lab15/certificate')

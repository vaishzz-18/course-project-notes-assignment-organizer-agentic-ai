import React, { useState, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  BookOpen,
  Users,
  FileText,
  ClipboardCheck,
  Flag,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowRight,
  Send,
  RefreshCw,
  GitBranch,
  ExternalLink,
  GraduationCap,
  Calendar,
  AlertCircle,
  Check,
  X,
  BookPlus,
  RotateCcw
} from 'lucide-react'
import {
  getCourses,
  getCourseCatalog,
  updateMyEnrollments,
  getPendingGrades,
  getReminders,
  getNotes,
  getAssignments,
  getGroups,
  getMilestones,
  getMilestoneSummary,
  getStudentGrades,
  getStudents,
  nlQuery,
  approveGrade
} from '../services/api'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const role = (localStorage.getItem('role') || 'student').toLowerCase()
  const name = localStorage.getItem('name') || 'User'
  const userId = Number(localStorage.getItem('user_id') || '0')
  const qc = useQueryClient()
  const [activeCourseId, setActiveCourseId] = useState<number>(() => {
    return Number(localStorage.getItem('active_course_id')) || 0
  })

  // Natural Language Assistant conversational query state
  interface ChatMessage {
    id: string
    role: 'user' | 'assistant'
    content: string
    timestamp: string
  }
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [nlQuestion, setNlQuestion] = useState('')
  const [isQuerying, setIsQuerying] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  // Clear chat when active course switches
  useEffect(() => {
    setChatMessages([])
  }, [activeCourseId])

  // Auto-scroll to bottom of conversation
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages, isQuerying])

  // Semester Course Management Modal State
  const [showCourseModal, setShowCourseModal] = useState(false)
  const [selectedCatalogIds, setSelectedCatalogIds] = useState<number[]>([])
  const [isUpdatingCourses, setIsUpdatingCourses] = useState(false)
  const [courseUpdateSuccess, setCourseUpdateSuccess] = useState<string | null>(null)

  // Sync course selection with global layout event & listen to open-course-modal
  useEffect(() => {
    function onCourseChange() {
      const stored = Number(localStorage.getItem('active_course_id')) || 0
      setActiveCourseId(stored)
    }
    function onOpenModal() {
      setShowCourseModal(true)
    }
    window.addEventListener('course-changed', onCourseChange)
    window.addEventListener('open-course-modal', onOpenModal)
    return () => {
      window.removeEventListener('course-changed', onCourseChange)
      window.removeEventListener('open-course-modal', onOpenModal)
    }
  }, [])

  // Common Queries
  const { data: courses, isLoading: coursesLoading } = useQuery({
    queryKey: ['courses'],
    queryFn: () => getCourses().then((r) => {
      if (r.data && r.data.length > 0) {
        const stored = Number(localStorage.getItem('active_course_id'))
        if (!stored || !r.data.some((c: any) => c.id === stored)) {
          setActiveCourseId(r.data[0].id)
          localStorage.setItem('active_course_id', String(r.data[0].id))
        }
      }
      return r.data
    })
  })

  const currentCourse = courses?.find((c: any) => c.id === activeCourseId) || courses?.[0]

  const { data: notes } = useQuery({
    queryKey: ['notes', activeCourseId],
    queryFn: () => getNotes(activeCourseId).then((r) => r.data),
    enabled: !!activeCourseId
  })

  const { data: assignments } = useQuery({
    queryKey: ['assignments', activeCourseId],
    queryFn: () => getAssignments(activeCourseId).then((r) => r.data),
    enabled: !!activeCourseId
  })

  const { data: groups } = useQuery({
    queryKey: ['groups', activeCourseId],
    queryFn: () => getGroups(activeCourseId).then((r) => r.data),
    enabled: !!activeCourseId
  })

  const { data: milestones } = useQuery({
    queryKey: ['milestones', activeCourseId],
    queryFn: () => getMilestones(activeCourseId).then((r) => r.data),
    enabled: !!activeCourseId
  })

  // Faculty specific queries
  const { data: students } = useQuery({
    queryKey: ['students', activeCourseId],
    queryFn: () => getStudents(activeCourseId).then((r) => r.data),
    enabled: !!activeCourseId && role === 'faculty'
  })

  const { data: pending, refetch: refetchPending } = useQuery({
    queryKey: ['pending-grades', activeCourseId],
    queryFn: () => getPendingGrades(activeCourseId).then((r) => r.data),
    enabled: !!activeCourseId && role === 'faculty'
  })

  const { data: milestoneSummary } = useQuery({
    queryKey: ['milestone-summary', activeCourseId],
    queryFn: () => getMilestoneSummary(activeCourseId).then((r) => r.data),
    enabled: !!activeCourseId && role === 'faculty'
  })

  // Student specific queries
  const { data: studentGrades } = useQuery({
    queryKey: ['student-grades', userId],
    queryFn: () => getStudentGrades(userId).then((r) => r.data),
    enabled: !!userId && role === 'student'
  })

  // Course Catalog Query for managing semester courses
  const { data: catalog, isLoading: catalogLoading } = useQuery({
    queryKey: ['course-catalog'],
    queryFn: () =>
      getCourseCatalog().then((r) => {
        const enrolled = r.data.filter((c: any) => c.is_enrolled).map((c: any) => c.id)
        setSelectedCatalogIds(enrolled)
        return r.data
      }),
    enabled: showCourseModal
  })

  function toggleCatalogCourse(courseId: number) {
    setSelectedCatalogIds((prev) =>
      prev.includes(courseId) ? prev.filter((id) => id !== courseId) : [...prev, courseId]
    )
  }

  async function handleSaveEnrollments() {
    if (selectedCatalogIds.length === 0) {
      alert('Please select at least one active course for the semester.')
      return
    }
    setIsUpdatingCourses(true)
    try {
      const res = await updateMyEnrollments(selectedCatalogIds)
      qc.invalidateQueries({ queryKey: ['courses'] })
      qc.invalidateQueries({ queryKey: ['course-catalog'] })
      setCourseUpdateSuccess('Course enrollments updated successfully for the semester!')

      if (res.data && res.data.length > 0 && !selectedCatalogIds.includes(activeCourseId)) {
        setActiveCourseId(res.data[0].id)
        localStorage.setItem('active_course_id', String(res.data[0].id))
        window.dispatchEvent(new Event('course-changed'))
      }
      setTimeout(() => {
        setShowCourseModal(false)
        setCourseUpdateSuccess(null)
      }, 1500)
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update course enrollments.')
    } finally {
      setIsUpdatingCourses(false)
    }
  }

  // Send conversational message to assistant with history
  async function sendMessage(text: string) {
    if (!text.trim()) return
    const userText = text.trim()
    const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: userText,
      timestamp: nowTime,
    }

    const updatedMessages = [...chatMessages, userMsg]
    setChatMessages(updatedMessages)
    setNlQuestion('')
    setIsQuerying(true)

    // Build history from previous turns
    const history = updatedMessages.map(m => ({ role: m.role, content: m.content }))

    try {
      const res = await nlQuery(activeCourseId, userText, history)
      const replyText = res.data?.answer || res.data?.result || JSON.stringify(res.data)
      const assistantMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        role: 'assistant',
        content: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setChatMessages(prev => [...prev, assistantMsg])
    } catch (err: any) {
      const errorText = err.response?.data?.detail || 'Failed to process inquiry.'
      const errorMsg: ChatMessage = {
        id: `bot-err-${Date.now()}`,
        role: 'assistant',
        content: errorText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setChatMessages(prev => [...prev, errorMsg])
    } finally {
      setIsQuerying(false)
    }
  }

  function clearChat() {
    setChatMessages([])
  }

  async function handleAskPrompt(promptText: string) {
    await sendMessage(promptText)
  }

  async function handleNLQuery(e: React.FormEvent) {
    e.preventDefault()
    await sendMessage(nlQuestion)
  }

  // Quick Faculty Approval
  async function handleQuickApprove(gradeId: number) {
    try {
      await approveGrade(gradeId, {})
      refetchPending()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Approval failed')
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 font-sans">
      {/* Personalized Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-3 py-1 rounded-full border border-blue-200">
              {currentCourse ? `${currentCourse.code} — ${currentCourse.name}` : 'No Course Selected'}
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600 bg-slate-100 px-3 py-1 rounded-full">
              {role === 'faculty' ? 'Faculty Portal' : 'Student Portal'}
            </span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {role === 'faculty' ? `Welcome back, ${name}` : `Welcome to your courses, ${name}`}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            {role === 'faculty'
              ? `Manage curriculum, lecture materials, assignments, student submissions, and project GitHub repositories.`
              : `Access lecture notes, view upcoming assignment deadlines, check grades, and submit project GitHub repositories.`}
          </p>
        </div>

        {role === 'student' && (
          <button
            onClick={() => setShowCourseModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-md shadow-blue-500/20 transition-all flex-shrink-0"
          >
            <BookOpen className="w-4 h-4" />
            <span>Manage Semester Courses</span>
          </button>
        )}
      </div>

      {/* ==================================================================== */}
      {/* EMPTY COURSES STATE */}
      {/* ==================================================================== */}
      {!coursesLoading && (!courses || courses.length === 0) ? (
        <div className="bg-white p-12 rounded-2xl border border-dashed border-slate-300 text-center space-y-3">
          <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto">
            <BookOpen className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-900">No courses available yet</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            {role === 'faculty'
              ? 'You do not have any courses assigned or created yet. Once a course is created, you can manage curriculum materials, assignments, and student submissions here.'
              : 'You are not enrolled in any courses yet. Once courses are created in the catalog, you can enroll to view notes and assignments.'}
          </p>
        </div>
      ) : role === 'faculty' ? (
        <div className="space-y-8">
          {/* Key Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Enrolled Students
                </span>
                <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
                  <Users className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-black text-slate-900">{students?.length ?? 0}</div>
              <div className="text-xs text-slate-500 font-medium">{currentCourse ? `Registered in ${currentCourse.code}` : 'No course selected'}</div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Lecture Materials
                </span>
                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl">
                  <FileText className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-black text-slate-900">{notes?.length ?? 0}</div>
              <div className="text-xs text-slate-500 font-medium">Active multi-version notes</div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Course Assignments
                </span>
                <div className="p-2 bg-purple-50 text-purple-600 rounded-xl">
                  <ClipboardCheck className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-black text-slate-900">{assignments?.length ?? 0}</div>
              <div className="text-xs text-slate-500 font-medium">With 100-mark rubrics</div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-amber-200 shadow-sm space-y-1 bg-amber-50/20">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-amber-800">
                  Pending Approvals
                </span>
                <div className="p-2 bg-amber-100 text-amber-700 rounded-xl">
                  <Clock className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-black text-amber-700">{pending?.length ?? 0}</div>
              <div className="text-xs text-amber-800 font-medium">Submissions awaiting sign-off</div>
            </div>
          </div>

          {/* Two-Column Section: Pending Approvals & Course Projects with GitHub */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left Column (7 cols): Submissions Awaiting Faculty Review */}
            <div className="lg:col-span-7 space-y-6">
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                      <Clock className="w-4 h-4 text-amber-600" />
                      Submissions Awaiting Faculty Approval
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      AI evaluations are staged for your review. Approve scores to publish them to students.
                    </p>
                  </div>
                  <Link to="/grades" className="text-xs font-bold text-blue-600 hover:underline">
                    View All →
                  </Link>
                </div>

                <div className="space-y-3">
                  {pending && pending.length > 0 ? (
                    pending.slice(0, 5).map((g: any) => (
                      <div
                        key={g.grade_id}
                        className="p-4 bg-slate-50 rounded-xl border border-slate-200 hover:border-blue-200 transition-all space-y-3"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <span className="text-sm font-bold text-slate-900">{g.student_name}</span>
                            <div className="text-xs text-slate-500">{g.assignment_title}</div>
                          </div>
                          <div className="text-right">
                            <span className="text-sm font-extrabold text-blue-700">
                              {g.draft_marks} / {g.max_marks}
                            </span>
                            <div className="text-[10px] text-slate-400">Draft Score</div>
                          </div>
                        </div>

                        {g.draft_feedback && (
                          <div className="text-xs text-slate-600 bg-white p-2.5 rounded-lg border border-slate-200 leading-relaxed">
                            {g.draft_feedback}
                          </div>
                        )}

                        <div className="flex items-center justify-between pt-1">
                          <button
                            onClick={() => handleQuickApprove(g.grade_id)}
                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition-all shadow-sm flex items-center gap-1.5"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" /> Approve & Publish Grade
                          </button>
                          <Link to="/grades" className="text-xs font-semibold text-blue-600 hover:underline">
                            Inspect Rubric Trace →
                          </Link>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-8 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200 text-xs text-slate-500">
                      All student submissions have been reviewed and published for this course.
                    </div>
                  )}
                </div>
              </div>

              {/* Natural Language Course Assistant */}
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-blue-600" />
                    <h3 className="text-base font-bold text-slate-900">
                      Curriculum Assistant (Natural Language Query)
                    </h3>
                  </div>
                  <div className="flex items-center gap-2">
                    {chatMessages.length > 0 && (
                      <button
                        type="button"
                        onClick={clearChat}
                        className="text-[11px] font-semibold text-slate-400 hover:text-slate-600 flex items-center gap-1 transition-colors px-2 py-0.5 rounded-lg border border-slate-200 hover:bg-slate-50"
                        title="Clear conversation history"
                      >
                        <RotateCcw className="w-3 h-3" /> Reset Chat
                      </button>
                    )}
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                      Syllabus Grounded
                    </span>
                  </div>
                </div>
                <p className="text-xs text-slate-500">
                  Query lecture materials, rubric specifications, or assignment policies for {currentCourse?.code}. You can also ask follow-up questions and continue the conversation.
                </p>

                {/* Conversational message thread */}
                {chatMessages.length > 0 && (
                  <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                    {chatMessages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`p-3.5 rounded-xl text-xs space-y-1 ${msg.role === 'user'
                          ? 'bg-blue-50 border border-blue-100 text-blue-950 ml-6'
                          : 'bg-slate-50 border border-slate-200 text-slate-800 mr-6'
                          }`}
                      >
                        <div className="flex items-center justify-between text-[11px] font-bold mb-1">
                          <span className={msg.role === 'user' ? 'text-blue-700' : 'text-slate-700'}>
                            {msg.role === 'user' ? 'You' : 'Curriculum Assistant'}
                          </span>
                          <span className="text-[10px] text-slate-400">{msg.timestamp}</span>
                        </div>
                        <div className="leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                      </div>
                    ))}
                    {isQuerying && (
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-500 flex items-center gap-2 mr-6">
                        <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-600" />
                        <span>Curriculum Assistant is thinking...</span>
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>
                )}

                <form onSubmit={handleNLQuery} className="flex gap-2">
                  <input
                    type="text"
                    value={nlQuestion}
                    onChange={(e) => setNlQuestion(e.target.value)}
                    placeholder={chatMessages.length > 0 ? "Ask a follow-up or choose an option..." : "e.g. 'What are the criteria for Assignment 1?' or 'Summarize Unit 2 topics'"}
                    className="flex-1 text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    type="submit"
                    disabled={isQuerying || !nlQuestion.trim()}
                    className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 flex-shrink-0"
                  >
                    {isQuerying ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                    {chatMessages.length > 0 ? 'Send' : 'Ask'}
                  </button>
                </form>

                {/* Suggested prompt chips */}
                <div className="flex items-center gap-1.5 flex-wrap pt-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Try asking:</span>
                  {[
                    "What are the rubrics for Assignment 1?",
                    "Summarize Unit 1 topics",
                    "Student submission analytics",
                    "Project milestone schedule"
                  ].map((chip) => (
                    <button
                      key={chip}
                      type="button"
                      onClick={() => handleAskPrompt(chip)}
                      className="text-[11px] font-semibold text-slate-600 bg-slate-100 hover:bg-blue-50 hover:text-blue-700 px-2.5 py-1 rounded-lg border border-slate-200 transition-colors"
                    >
                      {chip}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column (5 cols): Course Projects with Linked GitHub Repos */}
            <div className="lg:col-span-5 space-y-6">
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <GitBranch className="w-4 h-4 text-indigo-600" />
                    Course Projects & GitHub Repos
                  </h3>
                  <Link to="/milestones" className="text-xs font-bold text-blue-600 hover:underline">
                    Manage →
                  </Link>
                </div>
                <p className="text-xs text-slate-500">
                  Student teams host major project files on GitHub. Inspect repositories and monitor milestone checkpoints.
                </p>

                <div className="space-y-3">
                  {groups && groups.length > 0 ? (
                    groups.slice(0, 5).map((grp: any) => {
                      const groupGh = grp.github_url || milestoneSummary?.find((s: any) => s.group_id === grp.id && s.github_url)?.github_url || null
                      return (
                        <div
                          key={grp.id}
                          className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 space-y-2 hover:border-indigo-300 transition-all"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-slate-900">{grp.name}</span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
                              Team #{grp.id}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 line-clamp-2">{grp.description}</p>

                          <div className="pt-1 flex items-center justify-between">
                            {groupGh ? (
                              <a
                                href={groupGh}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-800 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-200 transition-colors"
                              >
                                <GitBranch className="w-3.5 h-3.5" />
                                <span>View GitHub Repo</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            ) : (
                              <span className="text-[11px] text-slate-400 italic">No GitHub repo linked yet</span>
                            )}

                            <Link
                              to="/milestones"
                              className="text-xs font-semibold text-slate-600 hover:text-slate-900"
                            >
                              Milestones →
                            </Link>
                          </div>
                        </div>
                      )
                    })
                  ) : (
                    <div className="p-6 text-center text-xs text-slate-400 bg-slate-50 rounded-xl">
                      No project groups formed for this course yet.
                    </div>
                  )}
                </div>
              </div>

              {/* Quick Course Actions */}
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Quick Management Actions
                </h4>
                <div className="grid grid-cols-1 gap-2">
                  <Link
                    to="/notes"
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-800 transition-colors"
                  >
                    <span className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-blue-600" />
                      Upload Lecture Notes & Materials
                    </span>
                    <ArrowRight className="w-4 h-4 text-slate-400" />
                  </Link>

                  <Link
                    to="/assignments"
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-800 transition-colors"
                  >
                    <span className="flex items-center gap-2">
                      <ClipboardCheck className="w-4 h-4 text-purple-600" />
                      Create New 100-Mark Assignment
                    </span>
                    <ArrowRight className="w-4 h-4 text-slate-400" />
                  </Link>

                  <Link
                    to="/milestones"
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-800 transition-colors"
                  >
                    <span className="flex items-center gap-2">
                      <GitBranch className="w-4 h-4 text-indigo-600" />
                      Review Milestone Submissions & GitHub
                    </span>
                    <ArrowRight className="w-4 h-4 text-slate-400" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* ==================================================================== */
        /* STUDENT DASHBOARD VIEW */
        /* ==================================================================== */
        <div className="space-y-8">
          {/* Student Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Enrolled Courses
                </span>
                <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
                  <GraduationCap className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-black text-slate-900">{courses?.length ?? 0}</div>
              <div className="text-xs text-slate-500 font-medium">Active academic courses</div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Active Assignments
                </span>
                <div className="p-2 bg-purple-50 text-purple-600 rounded-xl">
                  <ClipboardCheck className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-black text-slate-900">{assignments?.length ?? 0}</div>
              <div className="text-xs text-slate-500 font-medium">In {currentCourse?.code}</div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Course Notes
                </span>
                <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
                  <FileText className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-black text-slate-900">{notes?.length ?? 0}</div>
              <div className="text-xs text-slate-500 font-medium">Available for download</div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Completed Grades
                </span>
                <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
              </div>
              <div className="text-3xl font-black text-indigo-700">
                {studentGrades?.length ?? 0}
              </div>
              <div className="text-xs text-slate-500 font-medium">Evaluations published</div>
            </div>
          </div>

          {/* Two-Column Section for Student: Upcoming Assignments & My Project GitHub Link */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left Column (7 cols): My Course Assignments */}
            <div className="lg:col-span-7 space-y-6">
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <ClipboardCheck className="w-4 h-4 text-purple-600" />
                    Course Assignments ({currentCourse?.code})
                  </h3>
                  <Link to="/assignments" className="text-xs font-bold text-blue-600 hover:underline">
                    View & Submit →
                  </Link>
                </div>

                <div className="space-y-3">
                  {assignments && assignments.length > 0 ? (
                    assignments.map((asgn: any) => (
                      <div
                        key={asgn.id}
                        className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 hover:border-blue-200 transition-all"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-bold text-slate-900">{asgn.title}</span>
                          <span className="text-xs font-extrabold px-2 py-0.5 rounded-full bg-purple-100 text-purple-800">
                            {asgn.max_marks} Marks
                          </span>
                        </div>
                        <p className="text-xs text-slate-600 line-clamp-2">{asgn.description}</p>
                        <div className="flex items-center justify-between pt-2 border-t border-slate-200/60 text-xs text-slate-500">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3.5 h-3.5 text-slate-400" />
                            Due: {new Date(asgn.due_date).toLocaleDateString()}
                          </span>
                          <Link
                            to="/assignments"
                            className="text-xs font-bold text-blue-600 hover:underline"
                          >
                            Submit Code →
                          </Link>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-6 text-center text-xs text-slate-400 bg-slate-50 rounded-xl">
                      No assignments published for this course yet.
                    </div>
                  )}
                </div>
              </div>

              {/* Student Question Assistant */}
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-blue-600" />
                    <h3 className="text-base font-bold text-slate-900">
                      Course Assistant
                    </h3>
                  </div>
                  <div className="flex items-center gap-2">
                    {chatMessages.length > 0 && (
                      <button
                        type="button"
                        onClick={clearChat}
                        className="text-[11px] font-semibold text-slate-400 hover:text-slate-600 flex items-center gap-1 transition-colors px-2 py-0.5 rounded-lg border border-slate-200 hover:bg-slate-50"
                        title="Clear conversation history"
                      >
                        <RotateCcw className="w-3 h-3" /> Reset Chat
                      </button>
                    )}
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">
                      Notes & Syllabus
                    </span>
                  </div>
                </div>
                <p className="text-xs text-slate-500">
                  Ask questions about lecture concepts, exam requirements, or assignment rubrics for {currentCourse?.code}. You can also ask follow-up questions and continue the conversation.
                </p>

                {/* Conversational message thread */}
                {chatMessages.length > 0 && (
                  <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                    {chatMessages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`p-3.5 rounded-xl text-xs space-y-1 ${msg.role === 'user'
                          ? 'bg-blue-50 border border-blue-100 text-blue-950 ml-6'
                          : 'bg-slate-50 border border-slate-200 text-slate-800 mr-6'
                          }`}
                      >
                        <div className="flex items-center justify-between text-[11px] font-bold mb-1">
                          <span className={msg.role === 'user' ? 'text-blue-700' : 'text-slate-700'}>
                            {msg.role === 'user' ? 'You' : 'Course Assistant'}
                          </span>
                          <span className="text-[10px] text-slate-400">{msg.timestamp}</span>
                        </div>
                        <div className="leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                      </div>
                    ))}
                    {isQuerying && (
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-500 flex items-center gap-2 mr-6">
                        <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-600" />
                        <span>Course Assistant is thinking...</span>
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>
                )}

                <form onSubmit={handleNLQuery} className="flex gap-2">
                  <input
                    type="text"
                    value={nlQuestion}
                    onChange={(e) => setNlQuestion(e.target.value)}
                    placeholder={chatMessages.length > 0 ? "Ask a follow-up or choose an option..." : "e.g. 'What is covered in Unit 1?' or 'What are the rubric marks for Assignment 1?'"}
                    className="flex-1 text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    type="submit"
                    disabled={isQuerying || !nlQuestion.trim()}
                    className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 flex-shrink-0"
                  >
                    {isQuerying ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                    {chatMessages.length > 0 ? 'Send' : 'Ask'}
                  </button>
                </form>

                {/* Suggested prompt chips */}
                <div className="flex items-center gap-1.5 flex-wrap pt-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Try asking:</span>
                  {[
                    "What are the rubrics for Assignment 1?",
                    "Summarize Unit 1 lecture notes",
                    "What is my team's project milestone schedule?",
                    "What are my grades for this course?"
                  ].map((chip) => (
                    <button
                      key={chip}
                      type="button"
                      onClick={() => handleAskPrompt(chip)}
                      className="text-[11px] font-semibold text-slate-600 bg-slate-100 hover:bg-blue-50 hover:text-blue-700 px-2.5 py-1 rounded-lg border border-slate-200 transition-colors"
                    >
                      {chip}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column (5 cols): Course Project & GitHub Repository Link */}
            <div className="lg:col-span-5 space-y-6">
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <GitBranch className="w-4 h-4 text-indigo-600" />
                    Course Project & GitHub Submission
                  </h3>
                  <Link to="/milestones" className="text-xs font-bold text-blue-600 hover:underline">
                    Milestones →
                  </Link>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Upload your course project code to GitHub. Faculty can access your repository link directly to review your codebase and mark your project as completed.
                </p>

                <div className="p-4 bg-indigo-50/50 border border-indigo-200 rounded-xl space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-indigo-950">Project Repository</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                      Linked
                    </span>
                  </div>
                  <div className="p-3 bg-white border border-indigo-100 rounded-lg text-xs font-mono text-slate-700 truncate">
                    https://github.com/alexchen/agentic-ai-literature-synthesis
                  </div>
                  <div className="flex items-center justify-between pt-1">
                    <a
                      href="https://github.com/alexchen/agentic-ai-literature-synthesis"
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 px-3 py-1.5 rounded-lg shadow-sm transition-all"
                    >
                      <GitBranch className="w-3.5 h-3.5" />
                      <span>Open on GitHub</span>
                      <ExternalLink className="w-3 h-3 text-slate-400" />
                    </a>
                    <Link
                      to="/milestones"
                      className="text-xs font-bold text-indigo-600 hover:underline"
                    >
                      Update Link / Checkpoints →
                    </Link>
                  </div>
                </div>

                {/* Milestone Checkpoints Summary */}
                <div className="space-y-2 pt-2">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Project Checkpoint Schedule
                  </div>
                  {milestones && milestones.length > 0 ? (
                    milestones.map((m: any) => (
                      <div
                        key={m.id}
                        className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs"
                      >
                        <div>
                          <div className="font-bold text-slate-800">
                            Checkpoint {m.checkpoint_number}: {m.title}
                          </div>
                          <div className="text-[11px] text-slate-400">
                            Due: {new Date(m.due_date).toLocaleDateString()}
                          </div>
                        </div>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                          Active
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-slate-400 text-center py-2">
                      No milestones scheduled yet.
                    </div>
                  )}
                </div>
              </div>

              {/* Lecture Notes Quick Download */}
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Latest Course Notes ({currentCourse?.code})
                  </h4>
                  <Link to="/notes" className="text-xs font-bold text-blue-600 hover:underline">
                    View All →
                  </Link>
                </div>

                <div className="space-y-2">
                  {notes && notes.length > 0 ? (
                    notes.slice(0, 3).map((n: any) => (
                      <div
                        key={n.id}
                        className="p-2.5 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-xs"
                      >
                        <div className="min-w-0 pr-2">
                          <div className="font-bold text-slate-800 truncate">{n.title}</div>
                          <div className="text-[10px] text-slate-400">{n.unit} — Version {n.version}</div>
                        </div>
                        <Link
                          to="/notes"
                          className="text-xs font-semibold text-blue-600 hover:underline flex-shrink-0"
                        >
                          Download
                        </Link>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-slate-400 text-center py-2">
                      No notes available for this course yet.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Course Enrollment & Next Semester Management Modal */}
      {showCourseModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl shadow-2xl max-w-2xl w-full overflow-hidden border border-slate-200">
            {/* Modal Header */}
            <div className="px-6 py-5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-blue-600 rounded-2xl text-white shadow-md shadow-blue-500/20">
                  <GraduationCap className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-extrabold text-slate-900 text-lg">
                    {role === 'faculty' ? 'Manage Teaching Assignments' : 'Manage Semester Courses'}
                  </h3>
                  <p className="text-xs text-slate-500">
                    {role === 'faculty'
                      ? 'Add, change, or take on new courses across academic semesters.'
                      : 'Enroll in next semester courses, change active subjects, or update your academic curriculum.'}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowCourseModal(false)}
                className="text-slate-400 hover:text-slate-700 p-1.5 rounded-xl hover:bg-slate-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-4 max-h-[65vh] overflow-y-auto">
              {courseUpdateSuccess && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span>{courseUpdateSuccess}</span>
                </div>
              )}

              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Select Active Courses for Upcoming Term
                </span>
                <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-200">
                  {selectedCatalogIds.length} course{selectedCatalogIds.length === 1 ? '' : 's'} selected
                </span>
              </div>

              {catalogLoading ? (
                <div className="p-8 text-center text-slate-400 text-xs">Loading course catalog…</div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {catalog?.map((c: any) => {
                    const isSelected = selectedCatalogIds.includes(c.id)
                    return (
                      <div
                        key={c.id}
                        onClick={() => toggleCatalogCourse(c.id)}
                        className={`cursor-pointer rounded-2xl p-4 border transition-all flex items-start gap-3 ${isSelected
                          ? 'border-blue-600 bg-blue-50/70 shadow-sm'
                          : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                          }`}
                      >
                        <div
                          className={`w-4 h-4 rounded-md mt-0.5 flex items-center justify-center flex-shrink-0 border transition-all ${isSelected ? 'bg-blue-600 border-blue-600 text-white' : 'border-slate-300 bg-white'
                            }`}
                        >
                          {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-black px-2 py-0.5 rounded bg-slate-200 text-slate-800">
                              {c.code}
                            </span>
                            {c.is_enrolled && (
                              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                                Current
                              </span>
                            )}
                          </div>
                          <div className="text-xs font-bold text-slate-900 mt-1 truncate">{c.name}</div>
                          <p className="text-[11px] text-slate-500 mt-1 line-clamp-2">{c.description}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                Course changes will take effect immediately across all dashboard views.
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowCourseModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveEnrollments}
                  disabled={isUpdatingCourses}
                  className="px-5 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-xl shadow-md shadow-blue-500/20 transition-all flex items-center gap-1.5"
                >
                  {isUpdatingCourses ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                  Save Course Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

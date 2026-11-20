import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Flag,
  Plus,
  CheckCircle2,
  Clock,
  AlertTriangle,
  GitBranch,
  ExternalLink,
  Send,
  Check,
  FolderGit2,
  UploadCloud,
  FileText,
  Users,
  Trash2,
  MessageSquare,
  Edit3,
  X,
  User,
  Search,
  Filter
} from 'lucide-react'
import {
  getCourses,
  getMilestones,
  createMilestone,
  deleteMilestone,
  getMilestoneSummary,
  getMyMilestoneSummary,
  getGroups,
  submitMilestoneProgress,
  approveMilestoneProgress,
  submitProjectFeedback,
  getProjectFeedback
} from '../services/api'
import { format } from 'date-fns'

function HealthBadge({ health }: { health: string }) {
  if (health === 'green') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
        On track
      </span>
    )
  }
  if (health === 'amber') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
        <Clock className="w-3.5 h-3.5 text-amber-600" />
        At risk
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800">
      <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
      Overdue
    </span>
  )
}

interface FeedbackData {
  id: number
  feedback_text: string
  category: string
  faculty_id: number
  faculty_name: string
  created_at: string
  updated_at: string
}

interface FeedbackSectionProps {
  groupId: number
  groupName: string
  milestoneId?: number | null
  milestoneTitle?: string
  category: 'checkpoint' | 'github'
  feedback: FeedbackData | null
  role: string
  editingKey: string | null
  feedbackInput: string
  isSaving: boolean
  onStartEdit: (key: string, initialText: string) => void
  onCancelEdit: () => void
  onChangeText: (text: string) => void
  onSave: (groupId: number, milestoneId: number | null | undefined, category: string) => void
}

function FeedbackSection({
  groupId,
  groupName,
  milestoneId,
  category,
  feedback,
  role,
  editingKey,
  feedbackInput,
  isSaving,
  onStartEdit,
  onCancelEdit,
  onChangeText,
  onSave
}: FeedbackSectionProps) {
  const currentKey = `${category}-${groupId}-${milestoneId ?? 'repo'}`
  const isEditing = editingKey === currentKey

  return (
    <div className="mt-3 pt-3 border-t border-slate-200/80">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-3.5 h-3.5 text-indigo-600" />
          <span className="text-xs font-bold text-slate-800">
            {category === 'github' ? 'Faculty GitHub Feedback & Review' : 'Faculty Checkpoint Feedback & Comments'}
          </span>
        </div>

        {/* Feedback Status Badge */}
        {feedback ? (
          <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Feedback provided
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800">
            <Clock className="w-3 h-3 text-amber-600" /> Feedback pending
          </span>
        )}
      </div>

      {/* Existing Feedback Display */}
      {feedback && !isEditing && (
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 space-y-2 shadow-xs">
          <div className="flex items-center justify-between text-[11px] text-slate-500">
            <span className="font-semibold text-slate-800 flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-slate-400" />
              <span>{feedback.faculty_name || 'Faculty'}</span>
            </span>
            <span title={feedback.updated_at}>
              {feedback.updated_at ? format(new Date(feedback.updated_at), 'PPP p') : ''}
              {feedback.updated_at && feedback.created_at && feedback.updated_at !== feedback.created_at && ' (edited)'}
            </span>
          </div>
          <p className="text-xs text-slate-700 whitespace-pre-wrap leading-relaxed">
            {feedback.feedback_text}
          </p>
          {role === 'faculty' && (
            <div className="pt-1 flex justify-end">
              <button
                type="button"
                onClick={() => onStartEdit(currentKey, feedback.feedback_text)}
                className="text-[11px] font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1 hover:underline"
              >
                <Edit3 className="w-3 h-3" /> Edit Feedback
              </button>
            </div>
          )}
        </div>
      )}

      {/* No Feedback Yet */}
      {!feedback && !isEditing && (
        <div className="text-xs text-slate-500 italic bg-white/80 p-2.5 rounded-lg border border-slate-200 flex items-center justify-between">
          <span>
            {role === 'faculty'
              ? category === 'github'
                ? 'No feedback recorded for this team\'s GitHub repository yet.'
                : 'No feedback recorded for this team\'s checkpoint yet.'
              : category === 'github'
                ? 'Awaiting faculty review on your team\'s GitHub repository.'
                : 'Awaiting faculty review on this milestone checkpoint.'}
          </span>
          {role === 'faculty' && (
            <button
              type="button"
              onClick={() => onStartEdit(currentKey, '')}
              className="text-xs font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1 not-italic hover:underline"
            >
              <Plus className="w-3.5 h-3.5" /> Write Feedback
            </button>
          )}
        </div>
      )}

      {/* Faculty Feedback Edit / Input Box */}
      {role === 'faculty' && isEditing && (
        <div className="bg-white p-4 rounded-xl border border-blue-200 space-y-3 shadow-sm mt-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800">
              {feedback ? 'Edit Faculty Feedback' : 'Write Faculty Feedback'} for {groupName}
            </span>
            <button
              type="button"
              onClick={onCancelEdit}
              className="text-slate-400 hover:text-slate-600 p-0.5 rounded hover:bg-slate-100"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <textarea
            rows={3}
            value={feedbackInput}
            onChange={(e) => onChangeText(e.target.value)}
            placeholder={
              category === 'github'
                ? "Enter comments on the team's repository architecture, commits, documentation, or code quality..."
                : "Enter constructive feedback on this milestone's deliverables and checkpoint progress..."
            }
            className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 font-sans"
            autoFocus
          />
          <div className="flex items-center justify-between pt-1">
            <span className="text-[11px] text-slate-400">
              Visible to all students in {groupName}.
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onCancelEdit}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => onSave(groupId, milestoneId, category)}
                disabled={isSaving}
                className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-xs flex items-center gap-1.5"
              >
                {isSaving ? <Clock className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                Submit Feedback
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function MilestonesPage() {
  const role = (localStorage.getItem('role') || 'student').toLowerCase()
  const name = localStorage.getItem('name') || 'User'
  const qc = useQueryClient()

  const [activeTab, setActiveTab] = useState<'checkpoints' | 'github'>('checkpoints')

  const [selectedCourse, setSelectedCourse] = useState<number | null>(() => {
    return Number(localStorage.getItem('active_course_id')) || null
  })
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ title: '', description: '', due_date: '', checkpoint_number: 1 })

  // Student GitHub Submission Form State
  const [githubUrl, setGithubUrl] = useState('')
  const [submissionNotes, setSubmissionNotes] = useState('')
  const [selectedMilestoneId, setSelectedMilestoneId] = useState<number | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitMessage, setSubmitMessage] = useState<string | null>(null)

  // Feedback Editing State
  const [editingFeedbackKey, setEditingFeedbackKey] = useState<string | null>(null)
  const [feedbackInput, setFeedbackInput] = useState<string>('')
  const [savingKey, setSavingKey] = useState<string | null>(null)

  // GitHub Tab Filter & Search State
  const [githubSearch, setGithubSearch] = useState('')
  const [feedbackFilter, setFeedbackFilter] = useState<'all' | 'provided' | 'pending'>('all')

  const { data: courses } = useQuery({
    queryKey: ['courses'],
    queryFn: () =>
      getCourses().then((r) => {
        if (!selectedCourse && r.data?.length > 0) {
          setSelectedCourse(r.data[0].id)
        }
        return r.data
      })
  })

  const { data: milestones } = useQuery({
    queryKey: ['milestones', selectedCourse],
    queryFn: () => getMilestones(selectedCourse!).then((r) => r.data),
    enabled: !!selectedCourse
  })

  // Faculty: load all groups and full summary
  const { data: groups } = useQuery({
    queryKey: ['groups', selectedCourse],
    queryFn: () => getGroups(selectedCourse!).then((r) => r.data),
    enabled: !!selectedCourse && role === 'faculty'
  })

  const { data: summary, isLoading: summaryLoading, refetch: refetchSummary } = useQuery({
    queryKey: ['milestone-summary', selectedCourse],
    queryFn: () => getMilestoneSummary(selectedCourse!).then((r) => r.data),
    enabled: !!selectedCourse && role === 'faculty',
    refetchInterval: 30_000
  })

  // Student: load only my team's summary
  const { data: mySummaryData, isLoading: myLoading, refetch: refetchMySummary } = useQuery({
    queryKey: ['my-milestone-summary', selectedCourse],
    queryFn: () => getMyMilestoneSummary(selectedCourse!).then((r) => r.data),
    enabled: !!selectedCourse && role === 'student',
    refetchInterval: 30_000
  })

  // Fetch direct feedback records for this course
  const { data: feedbackList, refetch: refetchFeedback } = useQuery({
    queryKey: ['project-feedback', selectedCourse],
    queryFn: () => getProjectFeedback(selectedCourse!).then((r) => r.data),
    enabled: !!selectedCourse
  })

  const myGroup = mySummaryData?.group
  const myMilestones = mySummaryData?.milestones || []

  // Create Milestone Mutation
  const createMutation = useMutation({
    mutationFn: () =>
      createMilestone(selectedCourse!, {
        ...form,
        checkpoint_number: Number(form.checkpoint_number)
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['milestone-summary'] })
      qc.invalidateQueries({ queryKey: ['milestones'] })
      qc.invalidateQueries({ queryKey: ['my-milestone-summary'] })
      setShowCreate(false)
      setForm({ title: '', description: '', due_date: '', checkpoint_number: 1 })
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to create milestone checkpoint.')
    }
  })

  // Delete Milestone Mutation
  const deleteMutation = useMutation({
    mutationFn: (milestoneId: number) => deleteMilestone(selectedCourse!, milestoneId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['milestone-summary'] })
      qc.invalidateQueries({ queryKey: ['milestones'] })
      qc.invalidateQueries({ queryKey: ['my-milestone-summary'] })
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to delete milestone.')
    }
  })

  // Feedback Submit / Update Mutation
  const feedbackMutation = useMutation({
    mutationFn: (data: { group_id: number; milestone_id?: number | null; category: string; feedback_text: string }) =>
      submitProjectFeedback(selectedCourse!, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['milestone-summary', selectedCourse] })
      qc.invalidateQueries({ queryKey: ['my-milestone-summary', selectedCourse] })
      qc.invalidateQueries({ queryKey: ['project-feedback', selectedCourse] })
      setEditingFeedbackKey(null)
      setFeedbackInput('')
      setSavingKey(null)
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to submit feedback.')
      setSavingKey(null)
    }
  })

  function handleCreateSubmit() {
    if (!selectedCourse) {
      alert('Please select a course first.')
      return
    }
    if (!form.title.trim()) {
      alert('Please enter a Checkpoint Title.')
      return
    }
    if (!form.due_date) {
      alert('Please select a Due Date for this checkpoint.')
      return
    }
    createMutation.mutate()
  }

  // Handle Student GitHub Submission (auto-resolve group from myGroup)
  async function handleStudentGithubSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedCourse || !selectedMilestoneId || !myGroup) {
      alert('Please select a milestone checkpoint. You must be assigned to a project team.')
      return
    }

    setIsSubmitting(true)
    setSubmitMessage(null)

    try {
      const fd = new FormData()
      fd.append('group_id', String(myGroup.id))
      fd.append('notes', submissionNotes)
      if (githubUrl.trim()) {
        fd.append('github_url', githubUrl.trim())
      }

      await submitMilestoneProgress(selectedCourse, selectedMilestoneId, fd)
      setSubmitMessage('Project GitHub repository & milestone notes successfully submitted!')
      setGithubUrl('')
      setSubmissionNotes('')
      refetchMySummary()
      refetchFeedback()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Submission failed.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Handle Faculty 1-Click Approval
  async function handleApproveGroup(milestoneId: number, groupId: number) {
    if (!selectedCourse) return
    try {
      await approveMilestoneProgress(selectedCourse, milestoneId, groupId)
      refetchSummary()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve progress.')
    }
  }

  // Handle Feedback Submission
  function handleSaveFeedback(groupId: number, milestoneId: number | null | undefined, category: string) {
    if (!selectedCourse) return
    if (!feedbackInput.trim()) {
      alert('Feedback text cannot be empty.')
      return
    }
    setSavingKey(`${category}-${groupId}-${milestoneId ?? 'repo'}`)
    feedbackMutation.mutate({
      group_id: groupId,
      milestone_id: milestoneId,
      category: category,
      feedback_text: feedbackInput.trim()
    })
  }

  // Build feedback lookup from feedbackList: key -> feedback item
  const feedbackMap: Record<string, FeedbackData> = {}
  if (feedbackList && Array.isArray(feedbackList)) {
    feedbackList.forEach((fb: any) => {
      const key = `${fb.category}-${fb.group_id}-${fb.milestone_id ?? 'repo'}`
      feedbackMap[key] = fb
    })
  }

  // Faculty: Group summary by milestone - initialize with all course milestones
  const byMilestone: Record<number, { id: number; title: string; due: string; checkpoint: number; description?: string; groups: any[] }> = {}
  if (milestones && Array.isArray(milestones)) {
    milestones.forEach((m: any) => {
      byMilestone[m.id] = {
        id: m.id,
        title: m.title,
        due: m.due_date,
        checkpoint: m.checkpoint_number,
        description: m.description,
        groups: []
      }
    })
  }
  if (role === 'faculty' && summary && Array.isArray(summary)) {
    summary.forEach((row: any) => {
      if (row.group_id) {
        if (!byMilestone[row.milestone_id]) {
          byMilestone[row.milestone_id] = {
            id: row.milestone_id,
            title: row.milestone_title,
            due: row.due_date,
            checkpoint: row.checkpoint_number,
            description: '',
            groups: []
          }
        }
        byMilestone[row.milestone_id].groups.push(row)
      }
    })
  }

  // Compute stats for GitHub tab
  const allGroups = groups || []
  const teamsWithGithub = allGroups.filter((g: any) => {
    // Check if team has github_url in group or in any milestone progress
    if (g.github_url) return true
    const hasInProg = summary?.some((s: any) => s.group_id === g.id && s.github_url)
    return Boolean(hasInProg)
  })

  const teamsWithFeedback = allGroups.filter((g: any) => {
    return Boolean(
      feedbackMap[`github-${g.id}-repo`] ||
      summary?.some((s: any) => s.group_id === g.id && s.github_feedback)
    )
  })

  // Filtered teams list for GitHub tab
  const filteredTeams = allGroups.filter((g: any) => {
    const matchesSearch = !githubSearch.trim() || g.name.toLowerCase().includes(githubSearch.toLowerCase())
    const hasFeedback = Boolean(
      feedbackMap[`github-${g.id}-repo`] ||
      summary?.some((s: any) => s.group_id === g.id && s.github_feedback)
    )

    if (feedbackFilter === 'provided' && !hasFeedback) return false
    if (feedbackFilter === 'pending' && hasFeedback) return false
    return matchesSearch
  })

  const healthCounts = summary?.reduce(
    (acc: any, r: any) => {
      acc[r.health] = (acc[r.health] || 0) + 1
      return acc
    },
    { green: 0, amber: 0, red: 0 }
  ) ?? { green: 0, amber: 0, red: 0 }

  const isLoading = role === 'faculty' ? summaryLoading : myLoading

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-200 flex items-center gap-1.5">
              <FolderGit2 className="w-3.5 h-3.5" /> Course Projects
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600 bg-slate-100 px-3 py-1 rounded-full">
              GitHub Integrated
            </span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {role === 'faculty' ? 'Course Projects & Milestone Checkpoints' : 'My Project & Milestone Progress'}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            {role === 'faculty'
              ? 'Monitor group progress, review student GitHub codebases, provide written feedback, and approve milestones.'
              : 'View your team\'s project progress, link your GitHub repository, submit milestone updates, and view faculty feedback.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedCourse ?? ''}
            onChange={(e) => {
              const val = Number(e.target.value)
              setSelectedCourse(val)
              localStorage.setItem('active_course_id', String(val))
            }}
            className="text-xs font-bold text-slate-900 bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
          >
            <option value="">Select course…</option>
            {courses?.map((c: any) => (
              <option key={c.id} value={c.id}>
                {c.code} — {c.name}
              </option>
            ))}
          </select>

          {role === 'faculty' && selectedCourse && activeTab === 'checkpoints' && (
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-md transition-all flex-shrink-0"
            >
              <Plus className="w-4 h-4" />
              <span>New Milestone</span>
            </button>
          )}
        </div>
      </div>

      {/* Tabs Navigation: Checkpoint Submissions vs GitHub Tab */}
      <div className="flex items-center gap-3 border-b border-slate-200">
        <button
          type="button"
          onClick={() => setActiveTab('checkpoints')}
          className={`px-5 py-3 text-xs font-bold border-b-2 flex items-center gap-2 transition-all ${
            activeTab === 'checkpoints'
              ? 'border-blue-600 text-blue-700 bg-blue-50/40 rounded-t-lg'
              : 'border-transparent text-slate-500 hover:text-slate-900 hover:border-slate-300'
          }`}
        >
          <Flag className="w-4 h-4" />
          <span>Checkpoint Submissions</span>
          {summary && (
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold">
              {milestones?.length ?? 0} Checkpoints
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('github')}
          className={`px-5 py-3 text-xs font-bold border-b-2 flex items-center gap-2 transition-all ${
            activeTab === 'github'
              ? 'border-indigo-600 text-indigo-700 bg-indigo-50/40 rounded-t-lg'
              : 'border-transparent text-slate-500 hover:text-slate-900 hover:border-slate-300'
          }`}
        >
          <GitBranch className="w-4 h-4" />
          <span>GitHub Submissions & Repositories</span>
          {role === 'faculty' && allGroups.length > 0 && (
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold">
              {allGroups.length} Teams
            </span>
          )}
        </button>
      </div>

      {/* ================================================================== */}
      {/* TAB 1: REGULAR CHECKPOINT SUBMISSIONS                              */}
      {/* ================================================================== */}
      {activeTab === 'checkpoints' && (
        <div className="space-y-6">
          {/* Faculty: Health Overview Stat Cards */}
          {role === 'faculty' && selectedCourse && summary && (
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
                <div className="text-3xl font-black text-emerald-600">{healthCounts.green}</div>
                <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mt-1">On Track</div>
              </div>
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
                <div className="text-3xl font-black text-amber-600">{healthCounts.amber}</div>
                <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mt-1">At Risk</div>
              </div>
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
                <div className="text-3xl font-black text-rose-600">{healthCounts.red}</div>
                <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mt-1">Overdue / Needs Help</div>
              </div>
            </div>
          )}

          {/* Student: My Team Info Card */}
          {role === 'student' && selectedCourse && myGroup && (
            <div className="bg-white rounded-2xl border border-indigo-200 p-6 shadow-sm space-y-4 bg-gradient-to-br from-white to-indigo-50/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-indigo-100 text-indigo-700 rounded-xl">
                    <Users className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900">{myGroup.name}</h3>
                    <p className="text-xs text-slate-500">{myGroup.description}</p>
                  </div>
                </div>
                {myGroup.github_url && (
                  <a
                    href={myGroup.github_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition-all shadow-sm"
                  >
                    <GitBranch className="w-3.5 h-3.5 text-slate-200" />
                    <span>View on GitHub</span>
                    <ExternalLink className="w-3 h-3 text-slate-400" />
                  </a>
                )}
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-600">
                <Users className="w-3.5 h-3.5 text-slate-400" />
                <span className="font-semibold text-slate-800">Team Members:</span>
                <span>{myGroup.members?.join(', ') || 'No members assigned'}</span>
              </div>
            </div>
          )}

          {/* Student: Submit Progress Form */}
          {role === 'student' && selectedCourse && myGroup && (
            <div className="bg-white rounded-2xl border border-indigo-200 p-6 shadow-sm space-y-4 bg-gradient-to-br from-white to-indigo-50/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-2 bg-indigo-100 text-indigo-700 rounded-xl">
                    <Flag className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900">
                      Submit Milestone Checkpoint Work
                    </h3>
                    <p className="text-xs text-slate-500">
                      Update your team&apos;s milestone notes and link codebase for faculty review.
                    </p>
                  </div>
                </div>
                <span className="text-[11px] font-bold px-2.5 py-1 bg-indigo-100 text-indigo-800 rounded-full">
                  {myGroup.name}
                </span>
              </div>

              {submitMessage && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span>{submitMessage}</span>
                </div>
              )}

              <form onSubmit={handleStudentGithubSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Select Milestone Checkpoint</label>
                  <select
                    value={selectedMilestoneId ?? ''}
                    onChange={(e) => setSelectedMilestoneId(Number(e.target.value))}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                    required
                  >
                    <option value="">Choose checkpoint…</option>
                    {milestones?.map((m: any) => (
                      <option key={m.id} value={m.id}>
                        Checkpoint {m.checkpoint_number}: {m.title}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    GitHub Repository URL (Optional)
                  </label>
                  <div className="relative">
                    <GitBranch className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="url"
                      value={githubUrl}
                      onChange={(e) => setGithubUrl(e.target.value)}
                      placeholder="https://github.com/username/project-repo"
                      className="w-full text-xs pl-9 pr-3 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Milestone Progress Notes / Work Completed
                  </label>
                  <textarea
                    rows={3}
                    value={submissionNotes}
                    onChange={(e) => setSubmissionNotes(e.target.value)}
                    placeholder="Describe what was accomplished in this checkpoint, main branch status, or instructions for the faculty to run the codebase..."
                    className="w-full text-xs p-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between pt-1">
                  <span className="text-xs text-slate-400">
                    Faculty will review your deliverables and record written feedback.
                  </span>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition-all shadow-md flex items-center gap-1.5"
                  >
                    {isSubmitting ? <Clock className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                    Submit Milestone Progress
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Create Milestone Modal/Form for Faculty */}
          {showCreate && role === 'faculty' && (
            <div className="bg-white rounded-2xl border border-blue-200 p-6 shadow-sm space-y-4">
              <h3 className="font-bold text-slate-900 text-sm">Create New Milestone Checkpoint</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-slate-600 block mb-1">Checkpoint Title</label>
                  <input
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g. Checkpoint 2: Prototype Architecture & API"
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600 block mb-1">Checkpoint #</label>
                  <input
                    type="number"
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500"
                    value={form.checkpoint_number}
                    onChange={(e) => setForm({ ...form, checkpoint_number: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600 block mb-1">Due Date</label>
                  <input
                    type="datetime-local"
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500"
                    value={form.due_date}
                    onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600 block mb-1">Description</label>
                  <input
                    className="w-full border border-slate-300 rounded-xl px-3 py-2 text-xs focus:ring-2 focus:ring-blue-500"
                    placeholder="Deliverables expected from students..."
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                  />
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  onClick={handleCreateSubmit}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-sm"
                  disabled={createMutation.isPending}
                >
                  {createMutation.isPending ? 'Creating…' : 'Create Checkpoint'}
                </button>
                <button
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* STUDENT VIEW: Only own team's milestones */}
          {role === 'student' && selectedCourse && myGroup && myMilestones.length > 0 && (
            <div className="space-y-6">
              {myMilestones.map((ms: any) => {
                const cpFeedback = ms.checkpoint_feedback || feedbackMap[`checkpoint-${myGroup.id}-${ms.milestone_id}`] || null

                return (
                  <div key={ms.milestone_id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
                    {/* Checkpoint Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="px-2.5 py-0.5 rounded-md bg-blue-100 text-blue-800 text-xs font-extrabold">
                            Checkpoint #{ms.checkpoint_number}
                          </span>
                          <h3 className="font-bold text-slate-900 text-base">{ms.milestone_title}</h3>
                        </div>
                        <div className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5 text-slate-400" />
                          <span>Due: {format(new Date(ms.due_date), 'PPP')}</span>
                        </div>
                      </div>
                    </div>

                    {/* Team Progress Card */}
                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <HealthBadge health={ms.health} />
                          <div>
                            <div className="text-sm font-bold text-slate-900">{ms.group_name}</div>
                            <div className="text-xs text-slate-400">
                              Status: <span className="capitalize font-semibold text-slate-700">{ms.status.replace('_', ' ')}</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 flex-wrap">
                          {ms.github_url && (
                            <a
                              href={ms.github_url}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition-all shadow-sm"
                              title="Inspect code on GitHub"
                            >
                              <GitBranch className="w-3.5 h-3.5 text-slate-200" />
                              <span>View on GitHub</span>
                              <ExternalLink className="w-3 h-3 text-slate-400" />
                            </a>
                          )}
                          {ms.status === 'approved' && (
                            <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200 flex items-center gap-1">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Completed
                            </span>
                          )}
                        </div>
                      </div>

                      {ms.notes && (
                        <div className="text-xs text-slate-600 bg-white p-2.5 rounded-lg border border-slate-200 leading-relaxed">
                          <span className="font-semibold text-slate-800">Team Progress Notes: </span>
                          {ms.notes}
                        </div>
                      )}

                      {ms.submitted_at && (
                        <div className="text-xs text-slate-400">
                          Last submitted: {format(new Date(ms.submitted_at), 'PPp')}
                        </div>
                      )}

                      {/* Faculty Feedback Section */}
                      <FeedbackSection
                        groupId={myGroup.id}
                        groupName={myGroup.name}
                        milestoneId={ms.milestone_id}
                        milestoneTitle={ms.milestone_title}
                        category="checkpoint"
                        feedback={cpFeedback}
                        role={role}
                        editingKey={editingFeedbackKey}
                        feedbackInput={feedbackInput}
                        isSaving={savingKey === `checkpoint-${myGroup.id}-${ms.milestone_id}`}
                        onStartEdit={(key, text) => {
                          setEditingFeedbackKey(key)
                          setFeedbackInput(text)
                        }}
                        onCancelEdit={() => {
                          setEditingFeedbackKey(null)
                          setFeedbackInput('')
                        }}
                        onChangeText={setFeedbackInput}
                        onSave={handleSaveFeedback}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* FACULTY VIEW: Checkpoints & Team Rows */}
          {role === 'faculty' && selectedCourse && (!milestones || milestones.length === 0) && (
            <div className="p-8 text-center bg-white rounded-2xl border border-slate-200 text-slate-500 text-sm">
              No project milestones found for this course yet. Click <span className="font-semibold text-blue-600">+ New Milestone</span> above to create one.
            </div>
          )}

          {role === 'faculty' && milestones && milestones.length > 0 && (
            <div className="space-y-6">
              {Object.values(byMilestone)
                .sort((a, b) => a.checkpoint - b.checkpoint)
                .map((ms) => (
                  <div key={ms.id || ms.title} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
                    {/* Checkpoint Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="px-2.5 py-0.5 rounded-md bg-blue-100 text-blue-800 text-xs font-extrabold">
                            Checkpoint #{ms.checkpoint}
                          </span>
                          <h3 className="font-bold text-slate-900 text-base">{ms.title}</h3>
                        </div>
                        {ms.description && (
                          <p className="text-xs text-slate-600 mt-1">{ms.description}</p>
                        )}
                        <div className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5 text-slate-400" />
                          <span>Due: {format(new Date(ms.due), 'PPP')}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 text-xs">
                          <span className="text-emerald-700 font-semibold px-2 py-0.5 rounded-full bg-emerald-50">
                            {ms.groups.filter((g) => g.health === 'green').length} On track
                          </span>
                          <span className="text-amber-700 font-semibold px-2 py-0.5 rounded-full bg-amber-50">
                            {ms.groups.filter((g) => g.health === 'amber').length} At risk
                          </span>
                          <span className="text-rose-700 font-semibold px-2 py-0.5 rounded-full bg-rose-50">
                            {ms.groups.filter((g) => g.health === 'red').length} Overdue
                          </span>
                        </div>

                        <button
                          onClick={() => {
                            if (window.confirm(`Are you sure you want to delete Checkpoint #${ms.checkpoint}: ${ms.title}?`)) {
                              deleteMutation.mutate(ms.id)
                            }
                          }}
                          title="Delete checkpoint"
                          className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* Groups Progress Rows */}
                    {ms.groups.length === 0 ? (
                      <div className="p-4 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-xs text-slate-500">
                        No student project groups formed for this course yet. Checkpoint is scheduled and awaiting student group submissions.
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {ms.groups.map((g: any) => {
                          const cpFeedback = g.checkpoint_feedback || feedbackMap[`checkpoint-${g.group_id}-${ms.id}`] || null

                          return (
                            <div
                              key={`${g.group_id}-${g.milestone_id}`}
                              className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3 hover:border-slate-300 transition-all"
                            >
                              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                <div className="flex items-center gap-3">
                                  <HealthBadge health={g.health} />
                                  <div>
                                    <div className="text-sm font-bold text-slate-900">{g.group_name}</div>
                                    <div className="text-xs text-slate-400">
                                      Status: <span className="capitalize font-semibold text-slate-700">{g.status.replace('_', ' ')}</span>
                                    </div>
                                  </div>
                                </div>

                                {/* GitHub Link & Faculty Action */}
                                <div className="flex items-center gap-3 flex-wrap">
                                  {g.github_url && (
                                    <a
                                      href={g.github_url}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition-all shadow-sm"
                                      title="Inspect code on GitHub"
                                    >
                                      <GitBranch className="w-3.5 h-3.5 text-slate-200" />
                                      <span>View on GitHub</span>
                                      <ExternalLink className="w-3 h-3 text-slate-400" />
                                    </a>
                                  )}

                                  {g.status !== 'approved' && (
                                    <button
                                      onClick={() => handleApproveGroup(g.milestone_id, g.group_id)}
                                      className="inline-flex items-center gap-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition-all shadow-sm"
                                    >
                                      <Check className="w-3.5 h-3.5" />
                                      <span>Approve & Complete</span>
                                    </button>
                                  )}

                                  {g.status === 'approved' && (
                                    <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200 flex items-center gap-1">
                                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Completed
                                    </span>
                                  )}
                                </div>
                              </div>

                              {/* Progress Notes */}
                              {g.notes && (
                                <div className="text-xs text-slate-600 bg-white p-2.5 rounded-lg border border-slate-200 leading-relaxed">
                                  <span className="font-semibold text-slate-800">Team Notes: </span>
                                  {g.notes}
                                </div>
                              )}

                              {/* Faculty Feedback Section */}
                              <FeedbackSection
                                groupId={g.group_id}
                                groupName={g.group_name}
                                milestoneId={ms.id}
                                milestoneTitle={ms.title}
                                category="checkpoint"
                                feedback={cpFeedback}
                                role={role}
                                editingKey={editingFeedbackKey}
                                feedbackInput={feedbackInput}
                                isSaving={savingKey === `checkpoint-${g.group_id}-${ms.id}`}
                                onStartEdit={(key, text) => {
                                  setEditingFeedbackKey(key)
                                  setFeedbackInput(text)
                                }}
                                onCancelEdit={() => {
                                  setEditingFeedbackKey(null)
                                  setFeedbackInput('')
                                }}
                                onChangeText={setFeedbackInput}
                                onSave={handleSaveFeedback}
                              />
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                ))}
            </div>
          )}
        </div>
      )}

      {/* ================================================================== */}
      {/* TAB 2: GITHUB SUBMISSIONS & REPOSITORIES TAB                       */}
      {/* ================================================================== */}
      {activeTab === 'github' && (
        <div className="space-y-6">
          {/* Faculty GitHub Management Header & Stats */}
          {role === 'faculty' && selectedCourse && (
            <div className="space-y-6">
              {/* GitHub Overview Stat Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
                  <div className="text-3xl font-black text-slate-900">{allGroups.length}</div>
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mt-1">Total Teams</div>
                </div>
                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
                  <div className="text-3xl font-black text-indigo-600">{teamsWithGithub.length}</div>
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mt-1">Repos Linked</div>
                </div>
                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
                  <div className="text-3xl font-black text-emerald-600">{teamsWithFeedback.length}</div>
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mt-1">Feedback Provided</div>
                </div>
                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm text-center">
                  <div className="text-3xl font-black text-amber-600">{allGroups.length - teamsWithFeedback.length}</div>
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-500 mt-1">Feedback Pending</div>
                </div>
              </div>

              {/* Search & Filter Bar */}
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200">
                <div className="relative w-full sm:w-72">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    value={githubSearch}
                    onChange={(e) => setGithubSearch(e.target.value)}
                    placeholder="Search by team name…"
                    className="w-full text-xs pl-9 pr-3 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="flex items-center gap-2 self-end sm:self-auto">
                  <span className="text-xs font-semibold text-slate-600 flex items-center gap-1">
                    <Filter className="w-3.5 h-3.5" /> Filter:
                  </span>
                  <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50 text-xs font-semibold">
                    <button
                      onClick={() => setFeedbackFilter('all')}
                      className={`px-3 py-1 rounded-md transition-all ${feedbackFilter === 'all' ? 'bg-white shadow-xs text-indigo-700' : 'text-slate-600'}`}
                    >
                      All ({allGroups.length})
                    </button>
                    <button
                      onClick={() => setFeedbackFilter('provided')}
                      className={`px-3 py-1 rounded-md transition-all ${feedbackFilter === 'provided' ? 'bg-white shadow-xs text-emerald-700' : 'text-slate-600'}`}
                    >
                      Feedback Provided ({teamsWithFeedback.length})
                    </button>
                    <button
                      onClick={() => setFeedbackFilter('pending')}
                      className={`px-3 py-1 rounded-md transition-all ${feedbackFilter === 'pending' ? 'bg-white shadow-xs text-amber-700' : 'text-slate-600'}`}
                    >
                      Pending ({allGroups.length - teamsWithFeedback.length})
                    </button>
                  </div>
                </div>
              </div>

              {/* Teams GitHub Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {filteredTeams.map((team: any) => {
                  // Find team's github URL (either from group or latest milestone progress)
                  const progWithGh = summary?.find((s: any) => s.group_id === team.id && s.github_url)
                  const teamGithub = team.github_url || progWithGh?.github_url || null
                  const teamNotes = progWithGh?.notes || null
                  const ghFeedback = feedbackMap[`github-${team.id}-repo`] || null

                  return (
                    <div
                      key={team.id}
                      className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4 hover:border-slate-300 transition-all flex flex-col justify-between"
                    >
                      <div className="space-y-3">
                        {/* Team Header */}
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="px-2.5 py-0.5 rounded-md bg-indigo-50 text-indigo-800 text-xs font-extrabold border border-indigo-200">
                                {team.name}
                              </span>
                            </div>
                            {team.members && team.members.length > 0 && (
                              <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                                <Users className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                                <span className="line-clamp-1">{team.members.join(', ')}</span>
                              </p>
                            )}
                          </div>

                          {/* GitHub Status Badge */}
                          {teamGithub ? (
                            <span className="text-[11px] font-bold text-slate-800 bg-slate-100 px-2.5 py-1 rounded-full flex items-center gap-1 border border-slate-200">
                              <GitBranch className="w-3 h-3 text-slate-700" /> Repo Linked
                            </span>
                          ) : (
                            <span className="text-[11px] font-semibold text-slate-400 bg-slate-50 px-2 py-0.5 rounded-full border border-slate-200">
                              No Repo Yet
                            </span>
                          )}
                        </div>

                        {/* GitHub Repository Link */}
                        {teamGithub ? (
                          <div className="p-3 bg-slate-900 text-white rounded-xl flex items-center justify-between gap-3 shadow-sm">
                            <div className="flex items-center gap-2 min-w-0">
                              <GitBranch className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                              <span className="text-xs font-mono truncate text-slate-200">{teamGithub}</span>
                            </div>
                            <a
                              href={teamGithub}
                              target="_blank"
                              rel="noreferrer"
                              className="px-2.5 py-1 bg-white/10 hover:bg-white/20 text-white text-[11px] font-bold rounded-lg flex items-center gap-1 flex-shrink-0 transition-colors"
                            >
                              <span>Open</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          </div>
                        ) : (
                          <div className="p-3 bg-slate-50 text-slate-400 rounded-xl text-xs border border-dashed border-slate-200 italic">
                            Students have not submitted a GitHub repository link for this project yet.
                          </div>
                        )}

                        {/* Latest Milestone Notes */}
                        {teamNotes && (
                          <div className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-200 leading-relaxed">
                            <span className="font-semibold text-slate-800">Latest Submission Notes: </span>
                            {teamNotes}
                          </div>
                        )}
                      </div>

                      {/* GitHub Feedback Section */}
                      <FeedbackSection
                        groupId={team.id}
                        groupName={team.name}
                        milestoneId={null}
                        category="github"
                        feedback={ghFeedback}
                        role={role}
                        editingKey={editingFeedbackKey}
                        feedbackInput={feedbackInput}
                        isSaving={savingKey === `github-${team.id}-repo`}
                        onStartEdit={(key, text) => {
                          setEditingFeedbackKey(key)
                          setFeedbackInput(text)
                        }}
                        onCancelEdit={() => {
                          setEditingFeedbackKey(null)
                          setFeedbackInput('')
                        }}
                        onChangeText={setFeedbackInput}
                        onSave={handleSaveFeedback}
                      />
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Student: My Team GitHub Tab View */}
          {role === 'student' && selectedCourse && myGroup && (
            <div className="space-y-6">
              {/* My Team GitHub Card */}
              <div className="bg-white rounded-2xl border border-indigo-200 p-6 shadow-sm space-y-5 bg-gradient-to-br from-white to-indigo-50/20">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <span className="px-3 py-1 rounded-full bg-indigo-100 text-indigo-800 text-xs font-bold uppercase tracking-wider">
                      {myGroup.name}
                    </span>
                    <h3 className="text-xl font-bold text-slate-900 mt-2">
                      Course Project GitHub Repository
                    </h3>
                    <p className="text-xs text-slate-500 mt-1">
                      Repository details, commits, and faculty codebase feedback for your team.
                    </p>
                  </div>

                  {myGroup.github_url && (
                    <a
                      href={myGroup.github_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition-all shadow-md"
                    >
                      <GitBranch className="w-4 h-4 text-emerald-400" />
                      <span>Open on GitHub</span>
                      <ExternalLink className="w-3 h-3 text-slate-400" />
                    </a>
                  )}
                </div>

                {/* Team Members */}
                <div className="p-3 bg-white rounded-xl border border-slate-200 text-xs text-slate-600 flex items-center gap-2">
                  <Users className="w-4 h-4 text-slate-400 flex-shrink-0" />
                  <span className="font-semibold text-slate-800">Team Members:</span>
                  <span>{myGroup.members?.join(', ') || 'No members assigned'}</span>
                </div>

                {/* GitHub Submission Form / Link Status */}
                {myGroup.github_url ? (
                  <div className="p-4 bg-slate-900 text-white rounded-xl space-y-2">
                    <div className="text-xs text-slate-400 uppercase font-bold tracking-wider">Linked Repository</div>
                    <div className="text-sm font-mono text-emerald-400 break-all">{myGroup.github_url}</div>
                  </div>
                ) : (
                  <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                    <span>No GitHub repository URL submitted yet. Use the submission form under Checkpoint Submissions to submit your project repo.</span>
                  </div>
                )}

                {/* Faculty GitHub Feedback for Student's Team */}
                <FeedbackSection
                  groupId={myGroup.id}
                  groupName={myGroup.name}
                  milestoneId={null}
                  category="github"
                  feedback={feedbackMap[`github-${myGroup.id}-repo`] || myGroup.github_feedback || null}
                  role={role}
                  editingKey={editingFeedbackKey}
                  feedbackInput={feedbackInput}
                  isSaving={savingKey === `github-${myGroup.id}-repo`}
                  onStartEdit={(key, text) => {
                    setEditingFeedbackKey(key)
                    setFeedbackInput(text)
                  }}
                  onCancelEdit={() => {
                    setEditingFeedbackKey(null)
                    setFeedbackInput('')
                  }}
                  onChangeText={setFeedbackInput}
                  onSave={handleSaveFeedback}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* No course selected */}
      {!selectedCourse && (
        <div className="p-8 text-center bg-white rounded-2xl border border-slate-200 text-slate-500 text-sm">
          Please select an active course above to view projects and milestones.
        </div>
      )}

      {isLoading && <p className="text-slate-400 text-sm">Loading project checkpoints…</p>}
    </div>
  )
}

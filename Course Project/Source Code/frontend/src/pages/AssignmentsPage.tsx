import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ClipboardCheck, Plus, Upload, Clock, CheckCircle, XCircle, Send, Eye, Download, AlertTriangle, FileCode, Brain, ExternalLink, X, Copy, Check, Sparkles, Loader2 } from 'lucide-react'
import { getCourses, getAssignments, createAssignment, publishAssignment, getSubmissions, submitAssignment, downloadSubmission, getSubmissionContent, runGrading, gradeSingleSubmission, approveGrade } from '../services/api'
import { format } from 'date-fns'

export default function AssignmentsPage() {
  const role = localStorage.getItem('role') || 'student'
  const qc = useQueryClient()
  const [selectedCourse, setSelectedCourse] = useState<number | null>(() => {
    return Number(localStorage.getItem('active_course_id')) || null
  })
  const [showCreate, setShowCreate] = useState(false)
  const [viewSubs, setViewSubs] = useState<number | null>(null)
  const [submitFile, setSubmitFile] = useState<{ id: number; file: File | null }>({ id: 0, file: null })
  const [form, setForm] = useState({ title: '', description: '', max_marks: 100, due_date: '', rubric: '{}' })

  // Active submission inspection modal state
  const [inspectingSubId, setInspectingSubId] = useState<number | null>(null)
  const [copiedCode, setCopiedCode] = useState(false)
  const [overrideMarks, setOverrideMarks] = useState<number | null>(null)
  const [overrideFeedback, setOverrideFeedback] = useState<string>('')

  // Per-assignment grading in-progress state (keyed by assignment ID)
  const [gradingInProgress, setGradingInProgress] = useState<Record<number, boolean>>({})
  const [gradingSubId, setGradingSubId] = useState<number | null>(null)

  const { data: courses } = useQuery({
    queryKey: ['courses'],
    queryFn: () => getCourses().then(r => {
      if (!selectedCourse && r.data?.length > 0) {
        setSelectedCourse(r.data[0].id)
      }
      return r.data
    })
  })

  const { data: assignments, isLoading } = useQuery({
    queryKey: ['assignments', selectedCourse],
    queryFn: () => getAssignments(selectedCourse!).then(r => r.data),
    enabled: !!selectedCourse,
  })

  const { data: submissions, isLoading: subsLoading } = useQuery({
    queryKey: ['submissions', viewSubs],
    queryFn: () => getSubmissions(viewSubs!).then(r => r.data),
    enabled: !!viewSubs,
  })

  const { data: activeSubContent, isLoading: subContentLoading } = useQuery({
    queryKey: ['submission-content', inspectingSubId],
    queryFn: () => getSubmissionContent(inspectingSubId!).then(r => {
      setOverrideMarks(r.data.grade?.draft_marks ?? r.data.grade?.final_marks ?? 0)
      setOverrideFeedback(r.data.grade?.draft_feedback ?? r.data.grade?.final_feedback ?? '')
      return r.data
    }),
    enabled: !!inspectingSubId,
  })

  const createMutation = useMutation({
    mutationFn: () => createAssignment(selectedCourse!, {
      ...form,
      max_marks: Number(form.max_marks),
      rubric: JSON.parse(form.rubric || '{}'),
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['assignments'] }); setShowCreate(false) },
  })

  const publishMutation = useMutation({
    mutationFn: (aId: number) => publishAssignment(selectedCourse!, aId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['assignments'] }),
  })

  const submitMutation = useMutation({
    mutationFn: ({ id, file }: { id: number; file: File }) => {
      const fd = new FormData(); fd.append('file', file)
      return submitAssignment(id, fd)
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['assignments'] }); setSubmitFile({ id: 0, file: null }) },
  })

  const runGradingMutation = useMutation({
    mutationFn: (aId: number) => runGrading(selectedCourse!, aId),
    onMutate: (aId: number) => {
      setGradingInProgress(prev => ({ ...prev, [aId]: true }))
    },
    onSuccess: (_data, aId) => {
      setGradingInProgress(prev => ({ ...prev, [aId]: false }))
      qc.invalidateQueries({ queryKey: ['submissions'] })
      qc.invalidateQueries({ queryKey: ['pending-grades'] })
      alert('AI Rubric Grading pipeline executed successfully! Evaluated submissions have been queued for faculty approval.')
    },
    onError: (_err, aId) => {
      setGradingInProgress(prev => ({ ...prev, [aId]: false }))
    },
  })

  const approveMutation = useMutation({
    mutationFn: ({ gradeId, marks, feedback }: { gradeId: number; marks: number; feedback: string }) =>
      approveGrade(gradeId, { final_marks: marks, final_feedback: feedback }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['submissions'] })
      qc.invalidateQueries({ queryKey: ['submission-content'] })
      qc.invalidateQueries({ queryKey: ['pending-grades'] })
      setInspectingSubId(null)
    }
  })

  const gradeSingleMutation = useMutation({
    mutationFn: (submissionId: number) => gradeSingleSubmission(submissionId),
    onMutate: (subId) => setGradingSubId(subId),
    onSettled: () => setGradingSubId(null),
    onSuccess: (res, subId) => {
      qc.invalidateQueries({ queryKey: ['submissions'] })
      qc.invalidateQueries({ queryKey: ['submission-content', subId] })
      qc.invalidateQueries({ queryKey: ['pending-grades'] })
      if (inspectingSubId === subId) {
        setOverrideMarks(res.data.draft_marks)
        setOverrideFeedback(res.data.draft_feedback)
      }
      alert(`AI grading completed for ${res.data.student_name}: Draft ${res.data.draft_marks}/${res.data.max_marks} marks drafted.`)
    },
    onError: (err: any) => {
      alert(`AI grading failed: ${err.response?.data?.detail || err.message}`)
    }
  })

  async function handleDownloadSubmission(subId: number, fileName: string) {
    try {
      const res = await downloadSubmission(subId)
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = fileName
      a.click()
    } catch {
      alert('Could not download submission file.')
    }
  }

  function handleCopyCode(code: string) {
    navigator.clipboard.writeText(code)
    setCopiedCode(true)
    setTimeout(() => setCopiedCode(false), 2000)
  }

  const statusBadge = (s: string) => {
    if (s === 'published') return <span className="badge-green flex items-center gap-1"><CheckCircle className="w-3 h-3" />{s}</span>
    if (s === 'draft') return <span className="badge-amber">{s}</span>
    return <span className="badge-red flex items-center gap-1"><XCircle className="w-3 h-3" />{s}</span>
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <ClipboardCheck className="w-6 h-6 text-blue-600" />
            Assignments & Submissions
          </h1>
          <p className="text-sm text-gray-500 mt-1">Manage assignment specifications, inspect submitted student code, review plagiarism checks, and verify rubric grading.</p>
        </div>
        <div className="flex gap-3">
          <select value={selectedCourse ?? ''} onChange={(e) => setSelectedCourse(Number(e.target.value))} className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white font-medium shadow-sm">
            <option value="">Select course…</option>
            {courses?.map((c: any) => <option key={c.id} value={c.id}>{c.code} — {c.name}</option>)}
          </select>
          {role !== 'student' && selectedCourse && (
            <button className="btn-primary flex items-center gap-2 shadow-sm" onClick={() => setShowCreate(!showCreate)}>
              <Plus className="w-4 h-4" />New Assignment
            </button>
          )}
        </div>
      </div>

      {showCreate && (
        <div className="card mb-6 border-blue-200 bg-blue-50/40">
          <h3 className="font-semibold text-gray-900 mb-4">Create New Course Assignment</h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div><label className="text-xs font-semibold text-gray-700 block mb-1">Title</label><input className="w-full border rounded px-3 py-2 text-sm bg-white" placeholder="e.g. Assignment 2: LangGraph StateGraph" value={form.title} onChange={e => setForm({...form, title: e.target.value})} /></div>
            <div><label className="text-xs font-semibold text-gray-700 block mb-1">Max Marks</label><input type="number" className="w-full border rounded px-3 py-2 text-sm bg-white" value={form.max_marks} onChange={e => setForm({...form, max_marks: Number(e.target.value)})} /></div>
            <div><label className="text-xs font-semibold text-gray-700 block mb-1">Due Date</label><input type="datetime-local" className="w-full border rounded px-3 py-2 text-sm bg-white" value={form.due_date} onChange={e => setForm({...form, due_date: e.target.value})} /></div>
            <div><label className="text-xs font-semibold text-gray-700 block mb-1">Rubric Specification (JSON)</label><input className="w-full border rounded px-3 py-2 text-sm font-mono bg-white" placeholder='{"Code Correctness": {"max":40}, "Reasoning": {"max":30}}' value={form.rubric} onChange={e => setForm({...form, rubric: e.target.value})} /></div>
          </div>
          <div className="mb-4"><label className="text-xs font-semibold text-gray-700 block mb-1">Assignment Problem Description</label><textarea className="w-full border rounded px-3 py-2 text-sm bg-white" rows={3} placeholder="Detailed instructions for students..." value={form.description} onChange={e => setForm({...form, description: e.target.value})} /></div>
          <div className="flex gap-2">
            <button onClick={() => createMutation.mutate()} className="btn-primary" disabled={createMutation.isPending}>{createMutation.isPending ? 'Creating…' : 'Save & Create'}</button>
            <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      {!selectedCourse && (
        <div className="card text-center py-12 text-gray-500 bg-white border border-dashed border-gray-200 rounded-xl">
          <ClipboardCheck className="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <p className="font-semibold text-sm text-gray-700">No course selected</p>
          <p className="text-xs text-gray-400 mt-1">Select a course from the dropdown above to view or manage its assignments.</p>
        </div>
      )}
      {isLoading && <p className="text-gray-400">Loading assignments…</p>}

      {selectedCourse && !isLoading && (!assignments || assignments.length === 0) && (
        <div className="card text-center py-12 text-gray-500 bg-white border border-dashed border-gray-200 rounded-xl">
          <ClipboardCheck className="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <p className="font-semibold text-sm text-gray-700">No assignments created yet for this course.</p>
          {role !== 'student' && (
            <p className="text-xs text-gray-400 mt-1">
              Click &quot;New Assignment&quot; above to create and publish your first assignment specification.
            </p>
          )}
        </div>
      )}

      <div className="space-y-4">
        {assignments?.map((a: any) => (
          <div key={a.id} className="card shadow-sm hover:shadow transition-shadow">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="font-semibold text-lg text-gray-900">{a.title}</h3>
                  {statusBadge(a.status)}
                </div>
                <div className="text-sm text-gray-600 mb-3 whitespace-pre-line leading-relaxed max-w-3xl bg-slate-50/80 p-3.5 rounded-xl border border-slate-200/80">
                  {a.description}
                </div>
                <div className="flex items-center gap-4 text-xs text-gray-500 mb-2">
                  <span className="flex items-center gap-1 font-medium text-gray-700">
                    <Clock className="w-3.5 h-3.5 text-blue-600" />
                    Due: {format(new Date(a.due_date), 'PPp')}
                  </span>
                  <span>·</span>
                  <span className="font-semibold text-gray-700">Max: {a.max_marks} marks</span>
                </div>
                {a.rubric && (
                  <div className="mt-2 flex flex-wrap gap-1.5 items-center">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mr-1">Rubric Criteria:</span>
                    {Array.isArray(a.rubric?.criteria) ? (
                      a.rubric.criteria.map((c: any, i: number) => (
                        <span key={i} className="text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-md" title={c.description}>
                          {c.name} ({c.marks ?? c.max} pts)
                        </span>
                      ))
                    ) : (
                      Object.entries(a.rubric).map(([k, v]: [string, any], i: number) => (
                        <span key={i} className="text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-md" title={v?.description}>
                          {k} ({v?.max ?? v} pts)
                        </span>
                      ))
                    )}
                  </div>
                )}
              </div>
              <div className="flex gap-2 flex-col items-end">
                {role !== 'student' && a.status === 'draft' && (
                  <button onClick={() => publishMutation.mutate(a.id)} className="btn-primary flex items-center gap-1 text-xs py-1.5"><Send className="w-3.5 h-3.5" />Publish</button>
                )}
                {role !== 'student' && a.status === 'published' && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => runGradingMutation.mutate(a.id)}
                      disabled={!!gradingInProgress[a.id]}
                      className="btn-secondary flex items-center gap-1.5 text-xs py-1.5 px-3 bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100"
                      title="Run AI Rubric Grading Pipeline"
                    >
                      <Brain className="w-3.5 h-3.5 text-purple-600" />
                      {gradingInProgress[a.id] ? 'Grading...' : 'Run AI Grading'}
                    </button>
                    <button
                      onClick={() => setViewSubs(viewSubs === a.id ? null : a.id)}
                      className="btn-primary text-xs py-1.5 px-3"
                    >
                      {viewSubs === a.id ? 'Hide Submissions' : 'View Submissions'}
                    </button>
                  </div>
                )}
                {role === 'student' && a.status === 'published' && (
                  <div className="flex items-center gap-2">
                    <input type="file" className="text-xs file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-blue-50 file:text-blue-700" onChange={e => setSubmitFile({ id: a.id, file: e.target.files?.[0] ?? null })} />
                    <button
                      onClick={() => submitFile.file && submitMutation.mutate({ id: a.id, file: submitFile.file })}
                      className="btn-primary flex items-center gap-1 text-xs py-1.5"
                      disabled={!submitFile.file || submitFile.id !== a.id}
                    >
                      <Upload className="w-3.5 h-3.5" />Submit Work
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Submissions Table with Student Names, Timing, Similarity and Actions */}
            {viewSubs === a.id && (
              <div className="mt-5 pt-4 border-t border-gray-100">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-semibold text-gray-800">
                    Student Submissions ({submissions?.length ?? 0})
                  </h4>
                  <span className="text-xs text-gray-500">
                    Due date deadline: {format(new Date(a.due_date), 'PPp')}
                  </span>
                </div>

                {subsLoading && <p className="text-sm text-gray-400 py-4">Loading submissions...</p>}

                {submissions && submissions.length === 0 && (
                  <p className="text-sm text-gray-400 py-4">No submissions received yet for this assignment.</p>
                )}

                {submissions && submissions.length > 0 && (
                  <div className="overflow-x-auto rounded-lg border border-gray-200">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 text-xs text-gray-600 font-semibold uppercase tracking-wider border-b border-gray-200">
                        <tr>
                          <th className="py-2.5 px-3 text-left">Student</th>
                          <th className="py-2.5 px-3 text-left">Submitted File</th>
                          <th className="py-2.5 px-3 text-left">Submission Time</th>
                          <th className="py-2.5 px-3 text-left">Timing Status</th>
                          <th className="py-2.5 px-3 text-left">Plagiarism Check</th>
                          <th className="py-2.5 px-3 text-left">Grade Status</th>
                          <th className="py-2.5 px-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 bg-white">
                        {submissions.map((s: any) => {
                          const matchFlag = s.similarity_flags?.[0]
                          const isOriginalFirst = matchFlag?.role === 'original' || matchFlag?.status === 'original_submission'
                          const isPlagiarized = ((s.similarity_score ?? 0) > 0.75) && !isOriginalFirst
                          const matchedName = matchFlag?.with_student || (matchFlag?.with_student_id ? `Student #${matchFlag.with_student_id}` : null)

                          return (
                            <tr key={s.id} className={`hover:bg-gray-50 transition-colors ${isPlagiarized ? 'bg-red-50/30' : isOriginalFirst ? 'bg-emerald-50/20' : ''}`}>
                              {/* Student Info */}
                              <td className="py-3 px-3">
                                <div className="font-semibold text-gray-900">{s.student_name}</div>
                                <div className="text-xs text-gray-500">{s.student_email || `ID #${s.student_id}`}</div>
                              </td>

                              {/* Submitted File */}
                              <td className="py-3 px-3">
                                <div className="flex items-center gap-1.5 text-xs font-mono text-gray-700">
                                  <FileCode className="w-4 h-4 text-blue-600 flex-shrink-0" />
                                  <span className="truncate max-w-[160px]">{s.file_name}</span>
                                </div>
                              </td>

                              {/* Submitted At */}
                              <td className="py-3 px-3 text-xs text-gray-600 whitespace-nowrap">
                                {format(new Date(s.submitted_at), 'PP p')}
                              </td>

                              {/* Timing Status: Late vs On time strictly validated against deadline */}
                              <td className="py-3 px-3">
                                {s.is_late ? (
                                  <span className="badge-red font-medium text-xs px-2 py-0.5">
                                    Late
                                  </span>
                                ) : (
                                  <span className="badge-green font-medium text-xs px-2 py-0.5">
                                    On time
                                  </span>
                                )}
                              </td>

                              {/* Plagiarism Similarity with Matched Peer */}
                              <td className="py-3 px-3">
                                {isPlagiarized ? (
                                  <div className="flex flex-col items-start gap-0.5">
                                    <span className="badge-red font-semibold text-xs flex items-center gap-1">
                                      <AlertTriangle className="w-3 h-3 text-red-600" />
                                      {(s.similarity_score * 100).toFixed(0)}% Plagiarized (0 Marks)
                                    </span>
                                    {matchedName && (
                                      <span className="text-[11px] font-medium text-red-700">
                                        Copied from: {matchedName}
                                      </span>
                                    )}
                                  </div>
                                ) : isOriginalFirst ? (
                                  <div className="flex flex-col items-start gap-0.5">
                                    <span className="badge-green font-semibold text-xs flex items-center gap-1">
                                      <CheckCircle className="w-3 h-3 text-emerald-600" />
                                      {(s.similarity_score * 100).toFixed(0)}% Original (Submitted First)
                                    </span>
                                    <span className="text-[11px] font-medium text-emerald-700">
                                      Earliest submission in cluster
                                    </span>
                                  </div>
                                ) : s.similarity_score != null ? (
                                  <span className="badge-green text-xs font-medium">
                                    {(s.similarity_score * 100).toFixed(0)}% (Original)
                                  </span>
                                ) : (
                                  <span className="text-gray-400 text-xs">—</span>
                                )}
                              </td>

                              {/* Grade Status */}
                              <td className="py-3 px-3">
                                {s.grade ? (
                                  s.grade.status === 'published' ? (
                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                                      <CheckCircle className="w-3 h-3 text-emerald-600" />
                                      {s.grade.final_marks}/100 Approved
                                    </span>
                                  ) : (
                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                                      Draft: {s.grade.draft_marks}/100 (Pending Review)
                                    </span>
                                  )
                                ) : (
                                  <span className="text-xs text-gray-400">Ungraded</span>
                                )}
                              </td>

                              {/* Actions: AI Grade, Review Code & Download */}
                              <td className="py-3 px-3 text-right whitespace-nowrap">
                                <div className="flex items-center justify-end gap-1.5">
                                  {role !== 'student' && (
                                    <button
                                      onClick={() => gradeSingleMutation.mutate(s.id)}
                                      disabled={gradingSubId === s.id}
                                      className="btn-primary text-xs py-1 px-2.5 flex items-center gap-1 bg-purple-600 hover:bg-purple-700 text-white shadow-sm"
                                      title="Run AI Rubric Grading on this student's submission"
                                    >
                                      {gradingSubId === s.id ? (
                                        <>
                                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                          Grading...
                                        </>
                                      ) : (
                                        <>
                                          <Sparkles className="w-3.5 h-3.5" />
                                          {s.grade ? 'Re-Grade' : 'AI Grade'}
                                        </>
                                      )}
                                    </button>
                                  )}
                                  <button
                                    onClick={() => setInspectingSubId(s.id)}
                                    className="btn-secondary text-xs py-1 px-2.5 flex items-center gap-1 bg-white border border-gray-300 hover:bg-gray-50"
                                    title="Inspect submitted code and rubric breakdown"
                                  >
                                    <Eye className="w-3.5 h-3.5 text-blue-600" />
                                    Review Code
                                  </button>
                                  <button
                                    onClick={() => handleDownloadSubmission(s.id, s.file_name)}
                                    className="btn-secondary text-xs py-1 px-2.5 flex items-center gap-1 bg-white border border-gray-300 hover:bg-gray-50"
                                    title="Download submission file to disk"
                                  >
                                    <Download className="w-3.5 h-3.5 text-gray-600" />
                                    Download
                                  </button>
                                </div>
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Faculty Code Review & Grade Approval Modal */}
      {inspectingSubId && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden border border-gray-200">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
              <div>
                <div className="flex items-center gap-2">
                  <FileCode className="w-5 h-5 text-blue-600" />
                  <h3 className="font-bold text-gray-900 text-lg">
                    {activeSubContent?.student_name} — {activeSubContent?.file_name}
                  </h3>
                </div>
                <div className="text-xs text-gray-500 mt-1 flex items-center gap-3">
                  <span>{activeSubContent?.student_email}</span>
                  <span>·</span>
                  <span>Submitted: {activeSubContent?.submitted_at ? format(new Date(activeSubContent.submitted_at), 'PPpp') : ''}</span>
                  <span>·</span>
                  <span className={activeSubContent?.is_late ? "text-red-600 font-semibold" : "text-green-600 font-semibold"}>
                    {activeSubContent?.is_late ? "Late Submission" : "On-Time Submission"}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setInspectingSubId(null)}
                className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Plagiarism Warning Callout if Flagged */}
              {(activeSubContent?.similarity_score ?? 0) > 0.75 && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h5 className="font-semibold text-red-900 text-sm">Plagiarism Flag Detected ({(activeSubContent.similarity_score * 100).toFixed(0)}% Similarity)</h5>
                    <p className="text-xs text-red-700 mt-0.5">
                      This submission shares high structural and lexical overlap with peer submission(s).
                      {activeSubContent.similarity_flags?.[0]?.with_student && ` Detected verbatim match with ${activeSubContent.similarity_flags[0].with_student}.`}
                    </p>
                  </div>
                </div>
              )}

              {/* Rubric Breakdown by Criteria */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                    <Brain className="w-4 h-4 text-purple-600" />
                    Course Rubric Assessment & AI Draft Breakdown
                  </h4>
                  {role !== 'student' && activeSubContent && (
                    <button
                      onClick={() => gradeSingleMutation.mutate(activeSubContent.id)}
                      disabled={gradingSubId === activeSubContent.id}
                      className="btn-secondary text-xs py-1 px-3 flex items-center gap-1.5 bg-purple-50 text-purple-700 border border-purple-200 hover:bg-purple-100 font-medium"
                      title="Run AI rubric evaluation on this student's submission"
                    >
                      {gradingSubId === activeSubContent.id ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-600" />
                          Evaluating with AI...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                          {activeSubContent.grade ? 'Re-Run AI Grade' : 'Run AI Grade'}
                        </>
                      )}
                    </button>
                  )}
                </div>
                {activeSubContent?.grade?.rubric_breakdown && Object.keys(activeSubContent.grade.rubric_breakdown).length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {Object.entries(activeSubContent.grade.rubric_breakdown).map(([criterion, data]: [string, any]) => {
                      const maxMark = typeof data === 'object' ? data.max : 25
                      const awardedMark = typeof data === 'object' ? data.marks : data
                      const comment = typeof data === 'object' ? data.comment : ''

                      return (
                        <div key={criterion} className="border border-gray-200 rounded-lg p-3 bg-gray-50/60">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-semibold text-xs text-gray-800 capitalize">
                              {criterion.replace(/_/g, ' ')}
                            </span>
                            <span className="font-bold text-xs text-purple-700 bg-purple-100 px-2 py-0.5 rounded">
                              {awardedMark} / {maxMark} pts
                            </span>
                          </div>
                          {comment && <p className="text-xs text-gray-600 mt-1">{comment}</p>}
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <p className="text-xs text-gray-500 italic">No automated rubric breakdown generated yet. Click &quot;Run AI Grading&quot; on the assignment to evaluate against the course rubric.</p>
                )}
              </div>

              {/* Student Submitted Code/Text */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                    <FileCode className="w-4 h-4 text-blue-600" />
                    Submitted Source Code ({activeSubContent?.file_name})
                  </h4>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleCopyCode(activeSubContent?.content || '')}
                      className="btn-secondary text-xs py-1 px-2 flex items-center gap-1"
                    >
                      {copiedCode ? <Check className="w-3.5 h-3.5 text-green-600" /> : <Copy className="w-3.5 h-3.5" />}
                      {copiedCode ? 'Copied' : 'Copy Code'}
                    </button>
                    <button
                      onClick={() => handleDownloadSubmission(activeSubContent.id, activeSubContent.file_name)}
                      className="btn-secondary text-xs py-1 px-2 flex items-center gap-1"
                    >
                      <Download className="w-3.5 h-3.5" />
                      Download Raw File
                    </button>
                  </div>
                </div>
                <div className="border border-gray-300 rounded-lg bg-gray-950 p-4 overflow-x-auto max-h-72">
                  <pre className="text-xs font-mono text-emerald-300 whitespace-pre">
                    {subContentLoading ? 'Loading file contents...' : activeSubContent?.content}
                  </pre>
                </div>
              </div>

              {/* Faculty Review, Modification & Approval Gate */}
              {role !== 'student' && activeSubContent?.grade && (
                <div className="p-4 bg-blue-50/70 border border-blue-200 rounded-xl space-y-3">
                  <h4 className="text-sm font-bold text-blue-950 flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-blue-700" />
                    Faculty Grade Override & Final Approval Gate
                  </h4>
                  <p className="text-xs text-blue-800">
                    AI rubric scores remain drafts until faculty reviews and signs off. You may adjust marks or feedback below before publishing.
                  </p>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="text-xs font-semibold text-gray-700 block mb-1">Final Marks (out of {activeSubContent.assignment_max_marks})</label>
                      <input
                        type="number"
                        className="w-full border rounded px-3 py-1.5 text-sm bg-white font-semibold"
                        value={overrideMarks ?? ''}
                        onChange={(e) => setOverrideMarks(Number(e.target.value))}
                      />
                    </div>
                    <div className="col-span-2">
                      <label className="text-xs font-semibold text-gray-700 block mb-1">Faculty Evaluation Feedback</label>
                      <input
                        type="text"
                        className="w-full border rounded px-3 py-1.5 text-sm bg-white"
                        value={overrideFeedback}
                        onChange={(e) => setOverrideFeedback(e.target.value)}
                        placeholder="Feedback visible to student upon release..."
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      onClick={() => approveMutation.mutate({
                        gradeId: activeSubContent.grade.id,
                        marks: overrideMarks ?? activeSubContent.grade.draft_marks,
                        feedback: overrideFeedback
                      })}
                      disabled={approveMutation.isPending}
                      className="btn-primary text-xs py-2 px-4 flex items-center gap-1.5 bg-blue-700 hover:bg-blue-800 text-white shadow-sm"
                    >
                      <CheckCircle className="w-3.5 h-3.5" />
                      {approveMutation.isPending ? 'Publishing...' : 'Approve & Finalize Grade'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

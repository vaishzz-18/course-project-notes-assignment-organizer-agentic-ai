import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Star, Brain, CheckCircle, RotateCcw, Send, Eye, FileCode, AlertTriangle, Download, X, Copy, Check } from 'lucide-react'
import { getCourses, getPendingGrades, approveGrade, rollbackGrade, bulkApprove, runGrading, nlQuery, getAssignments, getStudentGrades, getSubmissionContent, downloadSubmission } from '../services/api'

export default function GradesPage() {
  const role = localStorage.getItem('role') || 'student'
  const userId = Number(localStorage.getItem('user_id') || '0')
  const qc = useQueryClient()
  const [selectedCourse, setSelectedCourse] = useState<number | null>(() => {
    return Number(localStorage.getItem('active_course_id')) || null
  })
  const [selectedAssignment, setSelectedAssignment] = useState<number | null>(null)
  const [editGrade, setEditGrade] = useState<any>(null)
  const [query, setQuery] = useState('')
  const [queryAnswer, setQueryAnswer] = useState('')
  const [queryLoading, setQueryLoading] = useState(false)
  const [selectedGrades, setSelectedGrades] = useState<number[]>([])

  // Code review modal state
  const [inspectingSubId, setInspectingSubId] = useState<number | null>(null)
  const [copiedCode, setCopiedCode] = useState(false)
  const [overrideMarks, setOverrideMarks] = useState<number | null>(null)
  const [overrideFeedback, setOverrideFeedback] = useState<string>('')

  // Per-grade approval in-progress state (keyed by grade_id)
  const [approvingGrades, setApprovingGrades] = useState<Record<number, boolean>>({})

  const { data: courses } = useQuery({
    queryKey: ['courses'],
    queryFn: () => getCourses().then(r => {
      if (!selectedCourse && r.data?.length > 0) {
        setSelectedCourse(r.data[0].id)
      }
      return r.data
    })
  })

  const { data: assignments } = useQuery({
    queryKey: ['assignments', selectedCourse],
    queryFn: () => getAssignments(selectedCourse!).then(r => r.data),
    enabled: !!selectedCourse,
  })

  const { data: pending, isLoading } = useQuery({
    queryKey: ['pending-grades', selectedCourse],
    queryFn: () => getPendingGrades(selectedCourse!).then(r => r.data),
    enabled: !!selectedCourse && role !== 'student',
  })

  const { data: myGrades } = useQuery({
    queryKey: ['my-grades', userId],
    queryFn: () => getStudentGrades(userId).then(r => r.data),
    enabled: role === 'student',
  })

  const { data: activeSubContent, isLoading: subContentLoading } = useQuery({
    queryKey: ['grade-submission-content', inspectingSubId],
    queryFn: () => getSubmissionContent(inspectingSubId!).then(r => {
      setOverrideMarks(r.data.grade?.draft_marks ?? r.data.grade?.final_marks ?? 0)
      setOverrideFeedback(r.data.grade?.draft_feedback ?? r.data.grade?.final_feedback ?? '')
      return r.data
    }),
    enabled: !!inspectingSubId,
  })

  const runMutation = useMutation({
    mutationFn: () => runGrading(selectedCourse!, selectedAssignment!),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pending-grades'] }),
  })

  const approveMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => approveGrade(id, data),
    onMutate: ({ id }) => {
      setApprovingGrades(prev => ({ ...prev, [id]: true }))
    },
    onSuccess: (_data, { id }) => {
      setApprovingGrades(prev => ({ ...prev, [id]: false }))
      qc.invalidateQueries({ queryKey: ['pending-grades'] })
      setEditGrade(null)
      setInspectingSubId(null)
    },
    onError: (_err, { id }) => {
      setApprovingGrades(prev => ({ ...prev, [id]: false }))
    },
  })

  const rollbackMutation = useMutation({
    mutationFn: (id: number) => rollbackGrade(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pending-grades'] }),
  })

  const bulkMutation = useMutation({
    mutationFn: () => bulkApprove(selectedGrades),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['pending-grades'] }); setSelectedGrades([]) },
  })

  async function handleQuery() {
    if (!selectedCourse || !query.trim()) return
    setQueryLoading(true)
    try {
      const res = await nlQuery(selectedCourse, query)
      setQueryAnswer(res.data.answer)
    } catch { setQueryAnswer('Error contacting AI.') }
    finally { setQueryLoading(false) }
  }

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

  if (role === 'student') {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2 mb-6"><Star className="w-6 h-6 text-yellow-500" />My Grades & Feedback</h1>
        {myGrades?.length === 0 && <p className="text-gray-400">No published grades released yet by faculty.</p>}
        <div className="space-y-3">
          {myGrades?.map((g: any, i: number) => (
            <div key={i} className="card shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold text-gray-900 text-base">{g.assignment_title}</div>
                  <div className="text-sm text-gray-600 mt-1">{g.final_feedback}</div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-blue-700">{g.final_marks}<span className="text-sm text-gray-400">/{g.max_marks}</span></div>
                  <div className="text-xs text-gray-400 mt-1">{g.published_at ? new Date(g.published_at).toLocaleDateString() : 'Published'}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Star className="w-6 h-6 text-yellow-500" />
            Faculty Grade Approvals Queue
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Review automated AI rubric drafts, inspect student code, modify marks or feedback, and publish official grades.
          </p>
        </div>
        <div className="flex gap-3">
          <select value={selectedCourse ?? ''} onChange={e => setSelectedCourse(Number(e.target.value))} className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white font-medium shadow-sm">
            <option value="">Select course…</option>
            {courses?.map((c: any) => <option key={c.id} value={c.id}>{c.code} — {c.name}</option>)}
          </select>
          <select value={selectedAssignment ?? ''} onChange={e => setSelectedAssignment(Number(e.target.value))} className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white font-medium shadow-sm" disabled={!selectedCourse}>
            <option value="">Select assignment…</option>
            {assignments?.map((a: any) => <option key={a.id} value={a.id}>{a.title}</option>)}
          </select>
          {selectedAssignment && (
            <button onClick={() => runMutation.mutate()} className="btn-primary flex items-center gap-2 shadow-sm" disabled={runMutation.isPending}>
              <Brain className="w-4 h-4" />{runMutation.isPending ? 'Running AI…' : 'Run AI Grading'}
            </button>
          )}
        </div>
      </div>

      {/* NL Query Box */}
      {selectedCourse && (
        <div className="card mb-6 border-purple-100 bg-purple-50">
          <div className="flex items-center gap-2 mb-3">
            <Brain className="w-4 h-4 text-purple-600" />
            <span className="font-medium text-purple-900 text-sm">Ask Classroom AI anything about this course</span>
          </div>
          <div className="flex gap-2">
            <input value={query} onChange={e => setQuery(e.target.value)} placeholder="e.g. Which students scored below 80% or had plagiarism flags?" className="flex-1 border border-purple-200 rounded-lg px-3 py-2 text-sm bg-white" onKeyDown={e => e.key === 'Enter' && handleQuery()} />
            <button onClick={handleQuery} disabled={queryLoading} className="btn-primary"><Send className="w-4 h-4" /></button>
          </div>
          {queryAnswer && <div className="mt-3 text-sm text-purple-800 bg-white rounded p-3 border border-purple-100">{queryAnswer}</div>}
        </div>
      )}

      {selectedGrades.length > 0 && (
        <div className="flex items-center gap-3 mb-4 p-3 bg-green-50 rounded-lg border border-green-200 shadow-sm">
          <span className="text-sm text-green-800 font-semibold">{selectedGrades.length} grades selected</span>
          <button onClick={() => bulkMutation.mutate()} className="btn-primary text-xs py-1.5 flex items-center gap-1 bg-green-700 hover:bg-green-800" disabled={bulkMutation.isPending}>
            <CheckCircle className="w-3.5 h-3.5" />Bulk Approve & Publish
          </button>
          <button onClick={() => setSelectedGrades([])} className="btn-secondary text-xs py-1.5">Clear Selection</button>
        </div>
      )}

      {!selectedCourse && (
        <div className="card text-center py-12 text-gray-500 bg-white border border-dashed border-gray-200 rounded-xl">
          <Star className="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <p className="font-semibold text-sm text-gray-700">No course selected</p>
          <p className="text-xs text-gray-400 mt-1">Select a course above to view submissions pending faculty review.</p>
        </div>
      )}
      {isLoading && <p className="text-gray-400">Loading pending evaluations…</p>}
      {selectedCourse && !isLoading && (!pending || pending.length === 0) && (
        <div className="card text-center py-12 text-gray-500 bg-white border border-dashed border-gray-200 rounded-xl">
          <CheckCircle className="w-8 h-8 text-emerald-300 mx-auto mb-2" />
          <p className="font-semibold text-sm text-gray-700">No pending grades awaiting review</p>
          <p className="text-xs text-gray-400 mt-1">All evaluated submissions have been signed off, or no student submissions have been graded yet.</p>
        </div>
      )}

      <div className="space-y-4">
        {pending?.map((g: any) => {
          const matchFlag = g.similarity_flags?.[0]
          const isOriginalFirst = matchFlag?.role === 'original' || matchFlag?.status === 'original_submission'
          const isPlag = ((g.similarity_score ?? 0) > 0.75) && !isOriginalFirst
          const matchedPeer = matchFlag?.with_student || (matchFlag?.with_student_id ? `Student #${matchFlag.with_student_id}` : null)

          return (
            <div key={g.grade_id} className={`card shadow-sm border transition-shadow ${isPlag ? 'border-red-300 bg-red-50/40' : isOriginalFirst ? 'border-emerald-300 bg-emerald-50/20' : 'border-gray-200 bg-white hover:border-gray-300'}`}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <input type="checkbox" checked={selectedGrades.includes(g.grade_id)} onChange={e => setSelectedGrades(e.target.checked ? [...selectedGrades, g.grade_id] : selectedGrades.filter(x => x !== g.grade_id))} className="mt-1 w-4 h-4 text-blue-600 rounded" />
                  <div>
                    <div className="font-bold text-gray-900 text-base">{g.student_name || `Student #${g.student_id}`}</div>
                    <div className="text-xs text-gray-500">{g.student_email} · {g.assignment_title} {g.submission_file_name ? `· ${g.submission_file_name}` : ''}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900">{g.draft_marks}<span className="text-sm text-gray-400">/{g.max_marks}</span></div>
                  {isPlag ? (
                    <div className="badge-red mt-1 font-semibold text-xs flex flex-col items-end">
                      <span>{(g.similarity_score * 100).toFixed(0)}% Plagiarized (0 Marks)</span>
                      {matchedPeer && <span className="text-[11px] text-red-700 font-normal">Copied from: {matchedPeer}</span>}
                    </div>
                  ) : isOriginalFirst ? (
                    <div className="badge-green mt-1 text-xs font-semibold">
                      {(g.similarity_score * 100).toFixed(0)}% Original (Submitted First)
                    </div>
                  ) : g.similarity_score != null ? (
                    <div className="badge-green mt-1 text-xs">{(g.similarity_score * 100).toFixed(0)}% Original</div>
                  ) : null}
                </div>
              </div>

              {/* Rubric Breakdown Grid */}
              {g.draft_rubric_breakdown && Object.keys(g.draft_rubric_breakdown).length > 0 && (
                <div className="mb-3 pt-2 border-t border-gray-100">
                  <div className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">AI Rubric Evaluation Breakdown</div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {Object.entries(g.draft_rubric_breakdown).map(([crit, val]: [string, any]) => {
                      const maxMark = typeof val === 'object' ? val.max : 25
                      const awarded = typeof val === 'object' ? val.marks : val
                      return (
                        <div key={crit} className="bg-gray-50 border border-gray-200 rounded p-2 text-xs">
                          <div className="font-medium text-gray-800 capitalize truncate">{crit.replace(/_/g, ' ')}</div>
                          <div className="font-bold text-purple-700 mt-0.5">{awarded} / {maxMark} pts</div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              <p className="text-sm text-gray-700 mb-3 bg-gray-50/80 p-3 rounded-lg border border-gray-100">{g.draft_feedback}</p>

              {editGrade?.id === g.grade_id ? (
                <div className="border-t pt-3 space-y-2 bg-blue-50/40 p-3 rounded-lg border border-blue-100">
                  <div className="flex items-center gap-3">
                    <label className="text-xs font-semibold text-gray-700">Override Marks:</label>
                    <input type="number" className="border rounded px-2 py-1 text-sm w-28 bg-white font-bold" defaultValue={g.draft_marks}
                      onChange={e => setEditGrade({ ...editGrade, marks: Number(e.target.value) })} />
                  </div>
                  <textarea className="w-full border rounded px-3 py-2 text-sm bg-white" rows={2} placeholder="Edit feedback for student…" defaultValue={g.draft_feedback}
                    onChange={e => setEditGrade({ ...editGrade, feedback: e.target.value })} />
                  <div className="flex gap-2 pt-1">
                    <button onClick={() => approveMutation.mutate({ id: g.grade_id, data: { final_marks: editGrade.marks, final_feedback: editGrade.feedback } })} className="btn-primary text-xs py-1.5 flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5" />Approve with edits
                    </button>
                    <button onClick={() => setEditGrade(null)} className="btn-secondary text-xs py-1.5">Cancel</button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between border-t border-gray-100 pt-3">
                  <div className="flex items-center gap-2">
                    <button onClick={() => approveMutation.mutate({ id: g.grade_id, data: {} })} className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1 bg-blue-600 hover:bg-blue-700" disabled={!!approvingGrades[g.grade_id]}>
                      <CheckCircle className="w-3.5 h-3.5" />{approvingGrades[g.grade_id] ? 'Approving...' : 'Approve Draft'}
                    </button>
                    <button onClick={() => setEditGrade({ id: g.grade_id, marks: g.draft_marks, feedback: g.draft_feedback })} className="btn-secondary text-xs py-1.5 px-3">
                      Edit & Approve
                    </button>
                    <button onClick={() => rollbackMutation.mutate(g.grade_id)} className="flex items-center gap-1 text-xs py-1.5 px-3 text-red-600 hover:bg-red-50 rounded-lg">
                      <RotateCcw className="w-3.5 h-3.5" />Rollback
                    </button>
                  </div>
                  <button
                    onClick={() => setInspectingSubId(g.submission_id)}
                    className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5 text-blue-700 border-blue-200 hover:bg-blue-50"
                  >
                    <Eye className="w-3.5 h-3.5 text-blue-600" />
                    Review Code
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Code Review Modal */}
      {inspectingSubId && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden border border-gray-200">
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
                  <span>Submitted: {activeSubContent?.submitted_at ? new Date(activeSubContent.submitted_at).toLocaleString() : ''}</span>
                  <span>·</span>
                  <span className={activeSubContent?.is_late ? "text-red-600 font-semibold" : "text-green-600 font-semibold"}>
                    {activeSubContent?.is_late ? "Late Submission" : "On-Time Submission"}
                  </span>
                </div>
              </div>
              <button onClick={() => setInspectingSubId(null)} className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {(activeSubContent?.similarity_score ?? 0) > 0.75 && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h5 className="font-semibold text-red-900 text-sm">Plagiarism Flag Detected ({(activeSubContent.similarity_score * 100).toFixed(0)}% Similarity)</h5>
                    <p className="text-xs text-red-700 mt-0.5">
                      High similarity detected with peer submission.
                      {activeSubContent.similarity_flags?.[0]?.with_student && ` Verbatim match with ${activeSubContent.similarity_flags[0].with_student}.`}
                    </p>
                  </div>
                </div>
              )}

              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                    <FileCode className="w-4 h-4 text-blue-600" />
                    Submitted Source Code ({activeSubContent?.file_name})
                  </h4>
                  <div className="flex items-center gap-2">
                    <button onClick={() => handleCopyCode(activeSubContent?.content || '')} className="btn-secondary text-xs py-1 px-2 flex items-center gap-1">
                      {copiedCode ? <Check className="w-3.5 h-3.5 text-green-600" /> : <Copy className="w-3.5 h-3.5" />}
                      {copiedCode ? 'Copied' : 'Copy Code'}
                    </button>
                    <button onClick={() => handleDownloadSubmission(activeSubContent.id, activeSubContent.file_name)} className="btn-secondary text-xs py-1 px-2 flex items-center gap-1">
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

              {activeSubContent?.grade && (
                <div className="p-4 bg-blue-50/70 border border-blue-200 rounded-xl space-y-3">
                  <h4 className="text-sm font-bold text-blue-950 flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-blue-700" />
                    Faculty Grade Adjustment & Approval
                  </h4>
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
                      <label className="text-xs font-semibold text-gray-700 block mb-1">Feedback</label>
                      <input
                        type="text"
                        className="w-full border rounded px-3 py-1.5 text-sm bg-white"
                        value={overrideFeedback}
                        onChange={(e) => setOverrideFeedback(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="flex justify-end pt-2">
                    <button
                      onClick={() => approveMutation.mutate({
                        id: activeSubContent.grade.id,
                        data: { final_marks: overrideMarks, final_feedback: overrideFeedback }
                      })}
                      className="btn-primary text-xs py-2 px-4 flex items-center gap-1.5 bg-blue-700 hover:bg-blue-800 text-white"
                    >
                      <CheckCircle className="w-3.5 h-3.5" />
                      Approve & Publish Grade
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

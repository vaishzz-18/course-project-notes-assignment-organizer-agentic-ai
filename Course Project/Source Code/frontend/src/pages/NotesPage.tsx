import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileText,
  Upload,
  Download,
  BookOpen,
  Folder,
  Plus,
  File,
  X,
  CheckCircle2,
  AlertCircle,
  Trash2
} from 'lucide-react'
import {
  getCourses,
  getCourseCurriculum,
  uploadLessonPlan,
  downloadLessonPlan,
  uploadChapterNote,
  deleteNote,
  downloadNote
} from '../services/api'

export default function NotesPage() {
  const role = (localStorage.getItem('role') || 'student').toLowerCase()
  const currentUserId = Number(localStorage.getItem('user_id')) || 0
  const qc = useQueryClient()

  const [selectedCourse, setSelectedCourse] = useState<number | null>(() => {
    return Number(localStorage.getItem('active_course_id')) || null
  })

  // Course-level Lesson Plan state
  const [showLpModal, setShowLpModal] = useState(false)
  const [lpFile, setLpFile] = useState<File | null>(null)
  const [lpError, setLpError] = useState<string | null>(null)

  // Chapter-level document upload state
  const [activeUploadChapter, setActiveUploadChapter] = useState<{ id: number; title: string; unitTitle: string } | null>(null)
  const [docTitle, setDocTitle] = useState('')
  const [docFile, setDocFile] = useState<File | null>(null)
  const [docError, setDocError] = useState<string | null>(null)

  // Fetch courses
  const { data: courses } = useQuery({
    queryKey: ['courses'],
    queryFn: () =>
      getCourses().then((r) => {
        if (!selectedCourse && r.data?.length > 0) {
          setSelectedCourse(r.data[0].id)
        }
        return r.data
      }),
  })

  // Fetch curriculum hierarchy (Units -> Chapters -> Topics & Notes)
  const {
    data: curriculum,
    isLoading: curriculumLoading,
  } = useQuery({
    queryKey: ['curriculum', selectedCourse],
    queryFn: () => getCourseCurriculum(selectedCourse!).then((r) => r.data),
    enabled: !!selectedCourse,
  })

  const currentCourse = courses?.find((c: any) => c.id === selectedCourse)
  const isFacultyForCourse = role === 'faculty' && (!currentCourse?.faculty_id || currentCourse.faculty_id === currentUserId || true)

  // Lesson Plan upload mutation
  const lpMutation = useMutation({
    mutationFn: async () => {
      if (!lpFile || !selectedCourse) return
      const fd = new FormData()
      fd.append('file', lpFile)
      return uploadLessonPlan(selectedCourse, fd)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['curriculum', selectedCourse] })
      setShowLpModal(false)
      setLpFile(null)
      setLpError(null)
    },
    onError: (err: any) => {
      setLpError(err.response?.data?.detail || 'Failed to upload Lesson Plan.')
    },
  })

  // Chapter document upload mutation
  const chapterDocMutation = useMutation({
    mutationFn: async () => {
      if (!docFile || !selectedCourse || !activeUploadChapter) return
      const fd = new FormData()
      fd.append('file', docFile)
      if (docTitle.trim()) {
        fd.append('title', docTitle.trim())
      }
      return uploadChapterNote(selectedCourse, activeUploadChapter.id, fd)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['curriculum', selectedCourse] })
      setActiveUploadChapter(null)
      setDocFile(null)
      setDocTitle('')
      setDocError(null)
    },
    onError: (err: any) => {
      setDocError(err.response?.data?.detail || 'Failed to upload document for this chapter.')
    },
  })

  // Delete note mutation
  const deleteMutation = useMutation({
    mutationFn: async (noteId: number) => {
      return deleteNote(noteId)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['curriculum', selectedCourse] })
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || 'Failed to delete document.')
    },
  })

  async function handleDownloadLp() {
    if (!selectedCourse) return
    try {
      const res = await downloadLessonPlan(selectedCourse)
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = curriculum?.lesson_plan?.file_name || 'Lesson_Plan.pdf'
      a.click()
    } catch (err) {
      alert('Could not download Lesson Plan file.')
    }
  }

  async function handleDownloadNote(noteId: number, fileName: string) {
    try {
      const res = await downloadNote(noteId)
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = fileName
      a.click()
    } catch (err) {
      alert('Could not download document file.')
    }
  }

  function handleDeleteNote(noteId: number, fileName: string) {
    if (window.confirm(`Are you sure you want to delete "${fileName}" from this chapter?`)) {
      deleteMutation.mutate(noteId)
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
            <BookOpen className="w-6 h-6 text-blue-600" />
            <span>Course Materials & Curriculum</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Course-level Lesson Plan, unit-wise chapters, topics covered, and chapter document repository.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Select Course:
          </label>
          <select
            value={selectedCourse ?? ''}
            onChange={(e) => {
              const val = Number(e.target.value)
              setSelectedCourse(val)
              localStorage.setItem('active_course_id', String(val))
            }}
            className="text-xs font-bold text-slate-900 bg-white border border-slate-300 rounded-xl px-3.5 py-2 focus:ring-2 focus:ring-blue-500 shadow-sm"
          >
            {courses?.map((c: any) => (
              <option key={c.id} value={c.id}>
                {c.code} — {c.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {!selectedCourse && (
        <div className="p-12 text-center bg-white border border-dashed border-slate-300 rounded-2xl">
          <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-sm font-bold text-slate-700">No course selected</p>
          <p className="text-xs text-slate-400 mt-1">Please select an academic course from the dropdown above.</p>
        </div>
      )}

      {selectedCourse && (
        <div className="space-y-6">
          {/* COURSE-LEVEL LESSON PLAN SECTION */}
          <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-2xl p-6 text-white shadow-xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-5">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-blue-500/30 text-blue-200 border border-blue-400/40">
                    {curriculum?.course_code || currentCourse?.code || 'Course'}
                  </span>
                  <span className="text-xs text-slate-300 font-semibold">Course-Level Document</span>
                </div>
                <h2 className="text-xl font-bold tracking-tight text-white">
                  Lesson Plan: {curriculum?.course_name || currentCourse?.name}
                </h2>
                <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                  Official course curriculum syllabus and chapter-wise lesson delivery plan.
                </p>
              </div>

              {/* LP Status & Actions */}
              <div className="flex flex-wrap items-center gap-3">
                {curriculum?.lesson_plan ? (
                  <div className="flex items-center gap-3 bg-white/10 backdrop-blur-md border border-white/15 px-4 py-2.5 rounded-xl">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    <div className="text-left">
                      <div className="text-xs font-bold text-white truncate max-w-[200px]" title={curriculum.lesson_plan.file_name}>
                        {curriculum.lesson_plan.file_name}
                      </div>
                      <div className="text-[10px] text-slate-300">
                        Uploaded {new Date(curriculum.lesson_plan.uploaded_at).toLocaleDateString()}
                      </div>
                    </div>
                    <button
                      onClick={handleDownloadLp}
                      className="ml-2 flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition-all shadow-sm cursor-pointer"
                      title="Download Lesson Plan"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download LP</span>
                    </button>
                    {isFacultyForCourse && (
                      <button
                        onClick={() => {
                          setLpFile(null)
                          setLpError(null)
                          setShowLpModal(true)
                        }}
                        className="px-2.5 py-1.5 bg-white/10 hover:bg-white/20 text-slate-200 rounded-lg text-xs font-medium transition-colors cursor-pointer"
                        title="Upload a new version to replace current Lesson Plan"
                      >
                        Replace
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-3">
                    <div className="text-xs text-slate-300 flex items-center gap-1.5 bg-white/5 border border-white/10 px-3 py-2 rounded-xl">
                      <AlertCircle className="w-3.5 h-3.5 text-amber-300" />
                      <span>No Lesson Plan uploaded yet</span>
                    </div>
                    {isFacultyForCourse && (
                      <button
                        onClick={() => {
                          setLpFile(null)
                          setLpError(null)
                          setShowLpModal(true)
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-400 text-white rounded-xl text-xs font-extrabold shadow-lg shadow-blue-500/30 transition-all cursor-pointer"
                      >
                        <Upload className="w-4 h-4" />
                        <span>Upload Lesson Plan</span>
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* CURRICULUM HIERARCHY (Units -> Chapters -> Topics & Chapter Materials) */}
          {curriculumLoading && (
            <div className="p-8 text-center text-slate-400 text-xs font-medium">
              Loading course curriculum hierarchy…
            </div>
          )}

          {curriculum?.units && curriculum.units.length > 0 ? (
            <div className="space-y-8">
              {curriculum.units.map((unit: any) => (
                <div key={unit.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                  {/* Unit Header */}
                  <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-xs font-extrabold text-white">
                        U{unit.unit_number}
                      </span>
                      <h3 className="text-sm font-extrabold tracking-wide uppercase text-slate-100">
                        {unit.title}
                      </h3>
                    </div>
                    <span className="text-xs font-medium text-slate-400">
                      {unit.chapters?.length || 0} Chapters
                    </span>
                  </div>

                  {/* Chapters List */}
                  <div className="divide-y divide-slate-100 p-6 space-y-8">
                    {unit.chapters?.map((chapter: any) => (
                      <div key={chapter.id} className="space-y-5 pt-6 first:pt-0">
                        {/* Chapter Title Bar */}
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50 border border-slate-200 rounded-xl px-5 py-3">
                          <div className="flex items-center gap-3">
                            <Folder className="w-5 h-5 text-indigo-600 flex-shrink-0" />
                            <h4 className="text-sm font-extrabold text-slate-900 tracking-tight">
                              {chapter.title}
                            </h4>
                          </div>
                          <span className="text-[11px] font-bold text-slate-500 bg-white border border-slate-200 px-2.5 py-1 rounded-md self-start sm:self-auto">
                            {chapter.topics?.length || 0} Topics Covered
                          </span>
                        </div>

                        {/* Section 1: Topics Covered (Informational list only) */}
                        <div className="bg-slate-50/50 rounded-xl border border-slate-100 p-4 space-y-2">
                          <h5 className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                            Topics Covered:
                          </h5>
                          <ol className="list-decimal list-inside space-y-1 pl-1">
                            {chapter.topics?.map((topic: any, idx: number) => (
                              <li
                                key={topic.id || idx}
                                className="text-xs text-slate-700 font-medium leading-relaxed"
                              >
                                {topic.title}
                              </li>
                            ))}
                          </ol>
                        </div>

                        {/* Section 2: Chapter Notes & Materials (Single upload section per chapter) */}
                        <div className="bg-white rounded-xl border border-blue-100 p-4 space-y-3">
                          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                            <div className="flex items-center gap-2">
                              <FileText className="w-4 h-4 text-blue-600" />
                              <h5 className="text-xs font-extrabold text-slate-900 uppercase tracking-wider">
                                Chapter Notes & Materials
                              </h5>
                              <span className="text-[10px] font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
                                {chapter.notes?.length || 0} Documents
                              </span>
                            </div>

                            {/* Single Upload Documents button for this chapter */}
                            {isFacultyForCourse && (
                              <button
                                onClick={() => {
                                  setActiveUploadChapter({
                                    id: chapter.id,
                                    title: chapter.title,
                                    unitTitle: unit.title,
                                  })
                                  setDocTitle('')
                                  setDocFile(null)
                                  setDocError(null)
                                }}
                                className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition-all shadow-sm cursor-pointer"
                                title="Upload notes or documents for this chapter"
                              >
                                <Plus className="w-3.5 h-3.5" />
                                <span>Upload Documents</span>
                              </button>
                            )}
                          </div>

                          {/* Documents List */}
                          {chapter.notes && chapter.notes.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 pt-1">
                              {chapter.notes.map((doc: any) => (
                                <div
                                  key={doc.id}
                                  className="flex items-center justify-between bg-slate-50 hover:bg-blue-50/40 border border-slate-200 rounded-xl px-3.5 py-2.5 transition-colors"
                                >
                                  <div className="flex items-center gap-2.5 min-w-0">
                                    <File className="w-4 h-4 text-blue-600 flex-shrink-0" />
                                    <div className="min-w-0">
                                      <div className="text-xs font-bold text-slate-900 truncate" title={doc.title}>
                                        {doc.title}
                                      </div>
                                      <div className="text-[10px] text-slate-500 truncate">
                                        {doc.file_name} · v{doc.version} · {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'Recent'}
                                      </div>
                                    </div>
                                  </div>

                                  <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                                    <button
                                      onClick={() => handleDownloadNote(doc.id, doc.file_name)}
                                      className="p-1.5 text-slate-600 hover:text-blue-600 hover:bg-white rounded-lg border border-transparent hover:border-slate-200 transition-all cursor-pointer"
                                      title={`Download ${doc.file_name}`}
                                    >
                                      <Download className="w-3.5 h-3.5" />
                                    </button>
                                    {isFacultyForCourse && (
                                      <button
                                        onClick={() => handleDeleteNote(doc.id, doc.file_name)}
                                        className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg border border-transparent hover:border-red-200 transition-all cursor-pointer"
                                        title={`Delete ${doc.file_name}`}
                                      >
                                        <Trash2 className="w-3.5 h-3.5" />
                                      </button>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="text-xs text-slate-400 italic py-2">
                              No documents uploaded for this chapter yet.
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            !curriculumLoading && (
              <div className="p-12 text-center bg-white border border-dashed border-slate-300 rounded-2xl">
                <FileText className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                <p className="text-sm font-bold text-slate-700">No curriculum units configured yet</p>
                <p className="text-xs text-slate-400 mt-1">
                  Units and chapters will appear here once defined for this course.
                </p>
              </div>
            )
          )}
        </div>
      )}

      {/* UPLOAD LESSON PLAN MODAL */}
      {showLpModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6 relative animate-in fade-in zoom-in-95 duration-150">
            <button
              onClick={() => setShowLpModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="p-2.5 bg-blue-100 text-blue-700 rounded-xl">
                <BookOpen className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-slate-900">Upload Course Lesson Plan</h3>
                <p className="text-xs text-slate-500">
                  {curriculum?.course_code} — {curriculum?.course_name}
                </p>
              </div>
            </div>

            {lpError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl font-medium">
                {lpError}
              </div>
            )}

            <div className="space-y-4">
              <div className="border-2 border-dashed border-slate-300 rounded-xl p-5 text-center bg-slate-50 hover:bg-blue-50/30 transition-colors">
                <input
                  type="file"
                  id="lp-file-input"
                  onChange={(e) => setLpFile(e.target.files?.[0] || null)}
                  className="hidden"
                  accept=".pdf,.doc,.docx,.ppt,.pptx,.txt"
                />
                <label htmlFor="lp-file-input" className="cursor-pointer block">
                  <Upload className="w-7 h-7 text-blue-600 mx-auto mb-2" />
                  <span className="text-xs font-bold text-blue-700 block hover:underline">
                    {lpFile ? lpFile.name : 'Choose Lesson Plan Document'}
                  </span>
                  <span className="text-[11px] text-slate-400 mt-1 block">
                    Supported: PDF, DOCX, PPTX, TXT
                  </span>
                </label>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowLpModal(false)}
                  className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => lpMutation.mutate()}
                  disabled={!lpFile || lpMutation.isPending}
                  className="px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-xl transition-colors shadow-sm cursor-pointer"
                >
                  {lpMutation.isPending ? 'Uploading…' : 'Upload Lesson Plan'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* UPLOAD CHAPTER DOCUMENT MODAL */}
      {activeUploadChapter && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6 relative animate-in fade-in zoom-in-95 duration-150">
            <button
              onClick={() => setActiveUploadChapter(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="p-2.5 bg-blue-100 text-blue-700 rounded-xl">
                <FileText className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <h3 className="text-base font-extrabold text-slate-900 truncate">Upload Chapter Document</h3>
                <p className="text-xs text-slate-500 truncate" title={activeUploadChapter.title}>
                  {activeUploadChapter.unitTitle} · {activeUploadChapter.title}
                </p>
              </div>
            </div>

            {docError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl font-medium">
                {docError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Document Title (Optional)
                </label>
                <input
                  type="text"
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  placeholder="Defaults to document file name"
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                />
              </div>

              <div className="border-2 border-dashed border-slate-300 rounded-xl p-5 text-center bg-slate-50 hover:bg-blue-50/30 transition-colors">
                <input
                  type="file"
                  id="doc-file-input"
                  onChange={(e) => setDocFile(e.target.files?.[0] || null)}
                  className="hidden"
                  accept=".pdf,.doc,.docx,.ppt,.pptx,.txt"
                />
                <label htmlFor="doc-file-input" className="cursor-pointer block">
                  <Upload className="w-7 h-7 text-blue-600 mx-auto mb-2" />
                  <span className="text-xs font-bold text-blue-700 block hover:underline">
                    {docFile ? docFile.name : 'Choose Document File'}
                  </span>
                  <span className="text-[11px] text-slate-400 mt-1 block">
                    Supported: PDF, PPTX, DOCX, TXT
                  </span>
                </label>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setActiveUploadChapter(null)}
                  className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => chapterDocMutation.mutate()}
                  disabled={!docFile || chapterDocMutation.isPending}
                  className="px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-xl transition-colors shadow-sm cursor-pointer"
                >
                  {chapterDocMutation.isPending ? 'Uploading…' : 'Attach to Chapter'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

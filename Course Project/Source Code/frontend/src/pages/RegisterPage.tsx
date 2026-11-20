import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { GraduationCap, BookOpen, Check, AlertCircle, CheckCircle2 } from 'lucide-react'
import { register, getAvailableCourses } from '../services/api'

interface CourseItem {
  id: number
  code: string
  name: string
  description?: string
}

export default function RegisterPage() {
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'student' })
  const [availableCourses, setAvailableCourses] = useState<CourseItem[]>([])
  const [selectedCourseIds, setSelectedCourseIds] = useState<number[]>([])
  const [coursesLoading, setCoursesLoading] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    setCoursesLoading(true)
    getAvailableCourses()
      .then((res) => {
        if (res.data && Array.isArray(res.data)) {
          setAvailableCourses(res.data)
          // Default: pre-select the first 2 courses for quick convenience
          if (res.data.length > 0) {
            setSelectedCourseIds(res.data.slice(0, 2).map((c: CourseItem) => c.id))
          }
        }
      })
      .catch((err) => {
        console.warn('Could not load public courses:', err)
      })
      .finally(() => {
        setCoursesLoading(false)
      })
  }, [])

  function toggleCourse(courseId: number) {
    setSelectedCourseIds((prev) =>
      prev.includes(courseId) ? prev.filter((id) => id !== courseId) : [...prev, courseId]
    )
  }

  function selectAllCourses() {
    if (selectedCourseIds.length === availableCourses.length) {
      setSelectedCourseIds([])
    } else {
      setSelectedCourseIds(availableCourses.map((c) => c.id))
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (availableCourses.length > 0 && selectedCourseIds.length === 0) {
      setError(
        form.role === 'faculty'
          ? 'Please select at least one course to teach / take.'
          : 'Please select at least one course to enroll in.'
      )
      return
    }

    setLoading(true)
    setError('')
    try {
      await register({
        ...form,
        course_ids: selectedCourseIds
      })
      navigate('/login')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Please check your details.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4 sm:p-6 font-sans">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-xl p-6 sm:p-10 border border-slate-100">
        {/* Brand Header */}
        <div className="flex items-center gap-3.5 mb-8">
          <div className="p-3 bg-blue-600 rounded-2xl shadow-lg shadow-blue-500/20 text-white flex items-center justify-center">
            <GraduationCap className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Classroom</h1>
            <p className="text-xs font-semibold text-slate-500">Academic Portal — Create New Account</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Basic Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">
                Full Name
              </label>
              <input
                type="text"
                placeholder="Full name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50/50"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">
                Institutional Email
              </label>
              <input
                type="email"
                placeholder="name@university.edu"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50/50"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">
                Password
              </label>
              <input
                type="password"
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50/50"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">
                Account Role
              </label>
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="w-full border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-slate-50/50 cursor-pointer"
              >
                <option value="student">Student Account</option>
                <option value="faculty">Faculty Account</option>
              </select>
            </div>
          </div>

          {/* Course Selection Section (Multi-Course Enrollment/Assignment) */}
          <div className="pt-2">
            <div className="flex items-center justify-between mb-2">
              <div>
                <label className="block text-xs font-extrabold text-slate-900 uppercase tracking-wider">
                  {form.role === 'faculty'
                    ? 'Select Courses to Teach / Handle'
                    : 'Select Courses to Enroll In'}
                </label>
                <p className="text-[11px] text-slate-500">
                  {form.role === 'faculty'
                    ? 'Faculty can teach multiple courses concurrently across disciplines.'
                    : 'Students can enroll in multiple courses simultaneously.'}
                </p>
              </div>

              {availableCourses.length > 0 && (
                <button
                  type="button"
                  onClick={selectAllCourses}
                  className="text-[11px] font-bold text-blue-600 hover:text-blue-800 hover:underline"
                >
                  {selectedCourseIds.length === availableCourses.length ? 'Deselect All' : 'Select All'}
                </button>
              )}
            </div>

            {coursesLoading ? (
              <div className="p-4 text-center text-xs text-slate-400 bg-slate-50 rounded-xl">
                Loading available curriculum courses…
              </div>
            ) : availableCourses.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-500 bg-slate-50 rounded-xl">
                No active courses currently listed in catalog. You can complete registration now and courses can be created or assigned later.
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-h-56 overflow-y-auto p-1">
                {availableCourses.map((c) => {
                  const isSelected = selectedCourseIds.includes(c.id)
                  return (
                    <div
                      key={c.id}
                      onClick={() => toggleCourse(c.id)}
                      className={`cursor-pointer rounded-xl p-3 border text-left transition-all flex items-start gap-2.5 ${
                        isSelected
                          ? 'border-blue-600 bg-blue-50/80 shadow-sm'
                          : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      <div
                        className={`w-4 h-4 rounded-md mt-0.5 flex items-center justify-center flex-shrink-0 border transition-all ${
                          isSelected ? 'bg-blue-600 border-blue-600 text-white' : 'border-slate-300 bg-white'
                        }`}
                      >
                        {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] font-black px-1.5 py-0.5 rounded bg-slate-200 text-slate-800">
                            {c.code}
                          </span>
                        </div>
                        <div className="text-xs font-bold text-slate-900 truncate mt-1">{c.name}</div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
              <span>
                {selectedCourseIds.length} course{selectedCourseIds.length === 1 ? '' : 's'} selected
              </span>
              <span className="text-blue-600 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Multi-course registration enabled
              </span>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs font-semibold flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-lg shadow-blue-600/30 transition-all flex items-center justify-center gap-2"
          >
            {loading ? 'Creating Account…' : 'Register & Join Courses'}
          </button>
        </form>

        <p className="text-center text-xs font-medium text-slate-500 mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-blue-600 font-bold hover:underline">
            Sign in here
          </Link>
        </p>
      </div>
    </div>
  )
}

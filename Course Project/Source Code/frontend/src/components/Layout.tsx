import React, { useState, useEffect } from 'react'
import { Outlet, NavLink, useNavigate, Link } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  ClipboardCheck,
  Star,
  GitBranch,
  LogOut,
  GraduationCap,
  User,
  BookOpen,
  KeyRound,
  Lock,
  X
} from 'lucide-react'
import { getCourses, changePassword } from '../services/api'

const facultyNav = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/notes', label: 'Course Materials', icon: FileText },
  { to: '/assignments', label: 'Assignments & Rubrics', icon: ClipboardCheck },
  { to: '/grades', label: 'Grade Approvals', icon: Star },
  { to: '/milestones', label: 'Course Projects & GitHub', icon: GitBranch },
]

const studentNav = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/notes', label: 'Lecture Notes', icon: FileText },
  { to: '/assignments', label: 'My Assignments', icon: ClipboardCheck },
  { to: '/grades', label: 'Grades & Feedback', icon: Star },
  { to: '/milestones', label: 'Projects & GitHub', icon: GitBranch },
]

export default function Layout() {
  const navigate = useNavigate()
  const role = (localStorage.getItem('role') || 'student').toLowerCase()
  const name = localStorage.getItem('name') || 'User'
  const [courses, setCourses] = useState<any[]>([])
  const [activeCourseId, setActiveCourseId] = useState<number>(() => {
    return Number(localStorage.getItem('active_course_id')) || 0
  })

  // Change Password state
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [pwdError, setPwdError] = useState<string | null>(null)
  const [pwdSuccess, setPwdSuccess] = useState<string | null>(null)
  const [pwdLoading, setPwdLoading] = useState(false)

  async function handlePasswordChange(e: React.FormEvent) {
    e.preventDefault()
    setPwdError(null)
    setPwdSuccess(null)

    if (!currentPassword) {
      setPwdError('Please enter your current password.')
      return
    }
    if (newPassword.length < 6) {
      setPwdError('New password must be at least 6 characters.')
      return
    }
    if (newPassword !== confirmPassword) {
      setPwdError('New passwords do not match.')
      return
    }

    setPwdLoading(true)
    try {
      await changePassword(currentPassword, newPassword)
      setPwdSuccess('Password updated successfully!')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setTimeout(() => {
        setShowPasswordModal(false)
        setPwdSuccess(null)
      }, 1500)
    } catch (err: any) {
      setPwdError(err.response?.data?.detail || 'Failed to update password. Check your current password.')
    } finally {
      setPwdLoading(false)
    }
  }

  useEffect(() => {
    getCourses()
      .then((res) => {
        if (res.data && res.data.length > 0) {
          setCourses(res.data)
          const stored = Number(localStorage.getItem('active_course_id'))
          if (!stored || !res.data.some((c: any) => c.id === stored)) {
            setActiveCourseId(res.data[0].id)
            localStorage.setItem('active_course_id', String(res.data[0].id))
          }
        } else {
          setCourses([])
          setActiveCourseId(0)
          localStorage.removeItem('active_course_id')
        }
      })
      .catch((err) => console.warn('Could not load courses in layout:', err))
  }, [])

  function handleCourseChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const newId = Number(e.target.value)
    setActiveCourseId(newId)
    localStorage.setItem('active_course_id', String(newId))
    window.dispatchEvent(new Event('course-changed'))
  }

  function logout() {
    localStorage.clear()
    navigate('/login')
  }

  const currentNav = role === 'faculty' ? facultyNav : studentNav

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-slate-900 flex flex-col flex-shrink-0 border-r border-slate-800 shadow-xl">
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <Link
            to="/"
            title="Go to Dashboard"
            className="flex items-center gap-3 text-white hover:opacity-90 transition-opacity cursor-pointer group"
          >
            <div className="p-2.5 bg-blue-600 rounded-xl shadow-md flex items-center justify-center group-hover:bg-blue-500 transition-colors">
              <GraduationCap className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-extrabold text-lg tracking-tight text-white leading-tight">Classroom</div>
              <div className="text-[11px] text-slate-400 font-medium">Academic Portal</div>
            </div>
          </Link>
        </div>

        {/* Personalized Role Badge */}
        <div className="px-5 py-3 bg-slate-800/50 border-b border-slate-800/80 flex items-center justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            {role === 'faculty' ? 'Faculty Portal' : 'Student Portal'}
          </span>
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
            role === 'faculty' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
          }`}>
            {role.toUpperCase()}
          </span>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 p-3 space-y-1.5 overflow-y-auto">
          {currentNav.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-900/30'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User Card & Sign Out */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/70">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold shadow-sm flex-shrink-0">
              {name.charAt(0)}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-white text-xs font-bold truncate">{name}</div>
              <div className="text-[11px] text-slate-400 capitalize truncate">{role}</div>
            </div>
          </div>
          <button
            onClick={() => {
              setPwdError(null)
              setPwdSuccess(null)
              setCurrentPassword('')
              setNewPassword('')
              setConfirmPassword('')
              setShowPasswordModal(true)
            }}
            className="w-full flex items-center justify-center gap-2 px-3 py-1.5 mb-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg text-xs font-medium transition-colors"
          >
            <KeyRound className="w-3.5 h-3.5" />
            <span>Change password</span>
          </button>
          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg text-xs font-medium transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between gap-4 flex-shrink-0 z-10 shadow-sm">
          {/* Active Course Selector */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-slate-500">
              <BookOpen className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-bold uppercase tracking-wider hidden sm:inline text-slate-600">
                Course:
              </span>
            </div>
            {courses.length > 0 ? (
              <select
                value={activeCourseId}
                onChange={handleCourseChange}
                className="text-xs font-bold text-slate-900 bg-slate-50 border border-slate-300 rounded-xl px-3.5 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer shadow-sm hover:border-slate-400 transition-colors"
              >
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.code} — {c.name}
                  </option>
                ))}
              </select>
            ) : (
              <span className="text-xs font-medium text-slate-400 italic bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl">
                No courses available
              </span>
            )}

            {role === 'student' && (
              <button
                onClick={() => window.dispatchEvent(new Event('open-course-modal'))}
                className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-xl text-xs font-bold transition-all shadow-sm"
                title="Add, change, or update enrolled courses for next semester"
              >
                <BookOpen className="w-3.5 h-3.5 text-blue-600" />
                <span>Change / Add Courses</span>
              </button>
            )}
          </div>

          {/* User Profile Overview */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2.5">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-bold text-slate-900">{name}</div>
                <div className="text-[11px] text-slate-500 capitalize">{role} Account</div>
              </div>
              <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700">
                <User className="w-4 h-4" />
              </div>
            </div>
          </div>
        </header>

        {/* Page Body */}
        <main className="flex-1 overflow-auto bg-slate-50/70">
          <Outlet />
        </main>
      </div>

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6 relative animate-in fade-in zoom-in-95 duration-150">
            <button
              onClick={() => setShowPasswordModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-3 mb-5">
              <div className="p-2.5 bg-blue-100 text-blue-700 rounded-xl">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-slate-900">Change Password</h3>
                <p className="text-xs text-slate-500">Update your account login password</p>
              </div>
            </div>

            {pwdError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl font-medium">
                {pwdError}
              </div>
            )}

            {pwdSuccess && (
              <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs rounded-xl font-medium">
                {pwdSuccess}
              </div>
            )}

            <form onSubmit={handlePasswordChange} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Current Password
                </label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter current password"
                  required
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  New Password
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Minimum 6 characters"
                  required
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm new password"
                  required
                  className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowPasswordModal(false)}
                  className="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={pwdLoading}
                  className="px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-xl transition-colors shadow-sm shadow-blue-500/20"
                >
                  {pwdLoading ? 'Saving...' : 'Update Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

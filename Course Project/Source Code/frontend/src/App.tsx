import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import NotesPage from './pages/NotesPage'
import AssignmentsPage from './pages/AssignmentsPage'
import GradesPage from './pages/GradesPage'
import MilestonesPage from './pages/MilestonesPage'
import AuditPage from './pages/AuditPage'
import LabWorkbenchPage from './pages/LabWorkbenchPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token')
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="notes" element={<NotesPage />} />
          <Route path="assignments" element={<AssignmentsPage />} />
          <Route path="grades" element={<GradesPage />} />
          <Route path="milestones" element={<MilestonesPage />} />
          <Route path="audit" element={<AuditPage />} />
          <Route path="labs" element={<LabWorkbenchPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Configure from './pages/Configure'
import Persons from './pages/Persons'
import Alerts from './pages/Alerts'
import Events from './pages/Events'
import ThreatCenter from './pages/ThreatCenter'
import Search from './pages/Search'
import Summary from './pages/Summary'
import Cameras from './pages/Cameras'
import Assets from './pages/Assets'
import PublishCamera from './pages/PublishCamera'
import Manage from './pages/Manage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('sentinel_token')
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/publish/:mode/:token" element={<PublishCamera />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/cameras" element={<Cameras />} />
        <Route path="/configure" element={<Configure />} />
        <Route path="/persons" element={<Persons />} />
        <Route path="/assets" element={<Assets />} />
        <Route path="/events" element={<Events />} />
        <Route path="/threats" element={<ThreatCenter />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/search" element={<Search />} />
        <Route path="/summary" element={<Summary />} />
        <Route path="/manage" element={<Manage />} />
      </Route>
    </Routes>
  )
}

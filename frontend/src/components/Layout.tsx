import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  Shield, LayoutDashboard, Camera, Users, Bell, Settings,
  Activity, Search, FileText, Box, LogOut, Radio, Database,
} from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'
import clsx from 'clsx'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Command Center' },
  { to: '/cameras', icon: Camera, label: 'Cameras' },
  { to: '/configure', icon: Settings, label: 'Configure' },
  { to: '/persons', icon: Users, label: 'Persons' },
  { to: '/assets', icon: Box, label: 'Assets' },
  { to: '/events', icon: Activity, label: 'Events' },
  { to: '/threats', icon: Shield, label: 'Threat Center' },
  { to: '/alerts', icon: Bell, label: 'Alert Rules' },
  { to: '/search', icon: Search, label: 'Intel Search' },
  { to: '/summary', icon: FileText, label: 'AI Summary' },
  { to: '/manage', icon: Database, label: 'Manage' },
]

export default function Layout() {
  const navigate = useNavigate()
  const { connected, alerts } = useWebSocket('/ws/live')

  const logout = () => {
    localStorage.removeItem('sentinel_token')
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-64 flex-shrink-0 glass-card border-r border-surface-border flex flex-col">
        <div className="p-5 border-b border-surface-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sentinel-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sentinel-500/20">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg tracking-tight">Sentinel AI</h1>
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <Radio className={clsx('w-3 h-3', connected ? 'text-green-400' : 'text-red-400')} />
                {connected ? 'Live' : 'Reconnecting'}
              </div>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-sentinel-600/20 text-sentinel-300 border border-sentinel-500/20'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5',
                )
              }
            >
              <Icon className="w-4 h-4" />
              {label}
              {to === '/threats' && alerts.length > 0 && (
                <span className="ml-auto bg-threat-critical text-white text-xs px-1.5 py-0.5 rounded-full">
                  {alerts.length}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-surface-border">
          <button onClick={logout} className="btn-ghost w-full flex items-center gap-2 text-sm">
            <LogOut className="w-4 h-4" /> Sign Out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}

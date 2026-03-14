/**
 * App shell: sidebar, header, logout, nav links. Used for all authenticated pages.
 */

import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import styles from './AppLayout.module.css'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/departments', label: 'Departments' },
  { to: '/reporting-cycles', label: 'Reporting Cycles' },
  { to: '/contributions', label: 'Contributions' },
  { to: '/analytics', label: 'Analytics' },
  { to: '/report-sections', label: 'Report Sections' },
  { to: '/exports', label: 'Exports' },
] as const

export function AppLayout() {
  const { user, logout } = useAuth()

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <h2 className={styles.appName}>Sustainability & SDG Reporting Hub</h2>
        </div>
        <nav className={styles.nav}>
          {NAV_ITEMS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
              }
              end={to === '/dashboard'}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className={styles.main}>
        <header className={styles.header}>
          <div className={styles.headerUser}>
            {user && (
              <span className={styles.userInfo}>
                {user.name}
                <span className={styles.role}>({user.role.replace(/_/g, ' ')})</span>
              </span>
            )}
            <button type="button" onClick={logout} className={styles.logoutBtn}>
              Log out
            </button>
          </div>
        </header>
        <main className={styles.content}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}

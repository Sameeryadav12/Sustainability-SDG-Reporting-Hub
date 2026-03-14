import { Link } from 'react-router-dom'
import styles from './NotFoundPage.module.css'

export function NotFoundPage() {
  return (
    <div className={styles.page}>
      <h1 className={styles.title}>Page not found</h1>
      <p className={styles.message}>The page you are looking for does not exist.</p>
      <Link to="/" className={styles.link}>Go to Dashboard</Link>
      <span className={styles.sep}> · </span>
      <Link to="/login" className={styles.link}>Log in</Link>
    </div>
  )
}

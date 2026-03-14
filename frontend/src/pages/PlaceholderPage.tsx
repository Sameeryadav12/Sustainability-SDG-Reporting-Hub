import { Link } from 'react-router-dom'
import styles from './PlaceholderPage.module.css'

type PlaceholderPageProps = {
  title: string
}

export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <div className={styles.page}>
      <h1 className={styles.title}>{title}</h1>
      <p className={styles.message}>Coming next</p>
      <Link to="/dashboard" className={styles.back}>
        ← Back to Dashboard
      </Link>
    </div>
  )
}

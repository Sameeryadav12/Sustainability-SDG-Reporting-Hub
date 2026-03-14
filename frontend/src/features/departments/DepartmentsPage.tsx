/**
 * Departments page: list, create (admin), edit (admin). Read-only for non-admins.
 */

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { fetchDepartments, createDepartment, updateDepartment } from '@/features/departments/departmentApi'
import type { Department } from '@/features/departments/departmentTypes'
import { DepartmentForm, type DepartmentFormValues } from '@/features/departments/DepartmentForm'
import type { ApiError } from '@/api/client'
import styles from './DepartmentsPage.module.css'

const ROLE_ADMIN = 'ADMIN'

export function DepartmentsPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === ROLE_ADMIN

  const [list, setList] = useState<Department[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState<'create' | 'edit' | null>(null)
  const [editing, setEditing] = useState<Department | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchDepartments()
      setList(data)
    } catch (e) {
      const err = e as ApiError
      setError(err.message || 'Unable to load departments.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const handleCreate = async (values: DepartmentFormValues) => {
    await createDepartment(values)
    setModalOpen(null)
    setSuccess('Department created successfully.')
    setTimeout(() => setSuccess(null), 4000)
    await load()
  }

  const handleUpdate = async (values: DepartmentFormValues) => {
    if (!editing) return
    await updateDepartment(editing.id, values)
    setEditing(null)
    setModalOpen(null)
    setSuccess('Department updated successfully.')
    setTimeout(() => setSuccess(null), 4000)
    await load()
  }

  const openEdit = (dept: Department) => {
    setEditing(dept)
    setModalOpen('edit')
  }

  const closeModal = () => {
    setModalOpen(null)
    setEditing(null)
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Departments</h1>
        {isAdmin && (
          <button type="button" onClick={() => setModalOpen('create')} className={styles.primaryBtn}>
            New department
          </button>
        )}
      </div>

      {loading && <p className={styles.status}>Loading…</p>}
      {success && <p className={styles.success} role="status">{success}</p>}
      {error && <p className={styles.error} role="alert">{error}</p>}
      {!loading && !error && list.length === 0 && (
        <p className={styles.empty}>No departments yet.</p>
      )}
      {!loading && !error && list.length > 0 && (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Name</th>
                <th>Code</th>
                <th>Type</th>
                {isAdmin && <th className={styles.actionsCol} />}
              </tr>
            </thead>
            <tbody>
              {list.map((dept) => (
                <tr key={dept.id}>
                  <td>{dept.name}</td>
                  <td>{dept.code}</td>
                  <td>{dept.type.replace(/_/g, ' ')}</td>
                  {isAdmin && (
                    <td className={styles.actionsCol}>
                      <button
                        type="button"
                        onClick={() => openEdit(dept)}
                        className={styles.linkBtn}
                      >
                        Edit
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modalOpen === 'create' && (
        <DepartmentForm
          onClose={closeModal}
          onSubmit={handleCreate}
        />
      )}
      {modalOpen === 'edit' && editing && (
        <DepartmentForm
          edit={editing}
          onClose={closeModal}
          onSubmit={handleUpdate}
        />
      )}
    </div>
  )
}

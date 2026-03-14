/**
 * Departments API (uses existing api client + auth).
 */

import { apiRequest } from '@/api/client'
import type { Department, DepartmentCreate, DepartmentUpdate } from './departmentTypes'

export async function fetchDepartments(): Promise<Department[]> {
  return apiRequest<Department[]>('/departments')
}

export async function createDepartment(data: DepartmentCreate): Promise<Department> {
  return apiRequest<Department>('/departments', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function updateDepartment(id: string, data: DepartmentUpdate): Promise<Department> {
  return apiRequest<Department>(`/departments/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

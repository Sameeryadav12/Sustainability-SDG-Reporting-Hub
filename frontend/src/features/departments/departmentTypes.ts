/**
 * Department types (aligned with backend schemas).
 */

export type DepartmentType = 'ACADEMIC' | 'OPERATIONS' | 'RESEARCH_CENTRE' | 'OTHER'

export const DEPARTMENT_TYPES: DepartmentType[] = [
  'ACADEMIC',
  'OPERATIONS',
  'RESEARCH_CENTRE',
  'OTHER',
]

export type Department = {
  id: string
  name: string
  code: string
  type: DepartmentType
  created_at: string
  updated_at: string
}

export type DepartmentCreate = {
  name: string
  code: string
  type: DepartmentType
}

export type DepartmentUpdate = {
  name?: string
  code?: string
  type?: DepartmentType
}

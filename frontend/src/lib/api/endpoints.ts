/**
 * API endpoint definitions
 * TODO: Implement actual API calls using apiClient
 */

import { apiClient } from './client'

// Auth endpoints
export const authApi = {
  login: (credentials: { email: string; password: string }) =>
    apiClient.post('/auth/login', credentials),
  logout: (refreshToken: string) =>
    apiClient.post('/auth/logout', { refresh_token: refreshToken }),
  refresh: (refreshToken: string) =>
    apiClient.post('/auth/refresh', { refresh_token: refreshToken }),
  getMe: () => apiClient.get('/auth/me'),
}

// Tenant endpoints
export const tenantsApi = {
  list: () => apiClient.get('/tenants'),
  get: (id: string) => apiClient.get(`/tenants/${id}`),
  create: (data: unknown) => apiClient.post('/tenants', data),
  update: (id: string, data: unknown) => apiClient.put(`/tenants/${id}`, data),
}

// Entity endpoints
export const entitiesApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    apiClient.get('/entities', { params }),
  get: (id: string) => apiClient.get(`/entities/${id}`),
  create: (data: unknown) => apiClient.post('/entities', data),
  update: (id: string, data: unknown) => apiClient.put(`/entities/${id}`, data),
  delete: (id: string) => apiClient.delete(`/entities/${id}`),
}

// Compliance Master endpoints
export const complianceMastersApi = {
  list: (params?: { category?: string; skip?: number; limit?: number }) =>
    apiClient.get('/compliance-masters', { params }),
  get: (id: string) => apiClient.get(`/compliance-masters/${id}`),
  create: (data: unknown) => apiClient.post('/compliance-masters', data),
  update: (id: string, data: unknown) =>
    apiClient.put(`/compliance-masters/${id}`, data),
}

// Compliance Instance endpoints
export const complianceInstancesApi = {
  list: (params?: {
    entity_id?: string
    status?: string
    category?: string
    rag_status?: string
    owner_id?: string
    skip?: number
    limit?: number
  }) => apiClient.get('/compliance-instances', { params }),
  get: (id: string) => apiClient.get(`/compliance-instances/${id}`),
  create: (data: unknown) => apiClient.post('/compliance-instances', data),
  update: (id: string, data: unknown) =>
    apiClient.put(`/compliance-instances/${id}`, data),
  recalculateStatus: (id: string) =>
    apiClient.post(`/compliance-instances/${id}/recalculate-status`),
}

// Workflow Task endpoints
export const workflowTasksApi = {
  list: (params?: {
    compliance_instance_id?: string
    assigned_to?: string
    status?: string
    skip?: number
    limit?: number
  }) => apiClient.get('/workflow-tasks', { params }),
  get: (id: string) => apiClient.get(`/workflow-tasks/${id}`),
  create: (data: unknown) => apiClient.post('/workflow-tasks', data),
  update: (id: string, data: unknown) =>
    apiClient.put(`/workflow-tasks/${id}`, data),
  complete: (id: string) => apiClient.post(`/workflow-tasks/${id}/complete`),
  getComments: (id: string) => apiClient.get(`/workflow-tasks/${id}/comments`),
  addComment: (id: string, data: { comment_text: string; is_internal?: boolean }) =>
    apiClient.post(`/workflow-tasks/${id}/comments`, data),
}

// Evidence endpoints
export const evidenceApi = {
  list: (params?: {
    compliance_instance_id?: string
    entity_id?: string
    approval_status?: string
    skip?: number
    limit?: number
  }) => apiClient.get('/evidence', { params }),
  get: (id: string) => apiClient.get(`/evidence/${id}`),
  upload: (
    file: File,
    compliance_instance_id: string,
    evidence_type: string
  ) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/evidence/upload', formData, {
      params: { compliance_instance_id, evidence_type },
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  download: (id: string) => apiClient.get(`/evidence/${id}/download`),
  approve: (id: string) => apiClient.post(`/evidence/${id}/approve`),
  reject: (id: string, reason: string) =>
    apiClient.post(`/evidence/${id}/reject`, { rejection_reason: reason }),
}

// Audit Log endpoints
export const auditLogsApi = {
  list: (params?: {
    resource_type?: string
    resource_id?: string
    user_id?: string
    action_type?: string
    skip?: number
    limit?: number
  }) => apiClient.get('/audit-logs', { params }),
  get: (id: string) => apiClient.get(`/audit-logs/${id}`),
  getResourceTrail: (resource_type: string, resource_id: string) =>
    apiClient.get(`/audit-logs/resource/${resource_type}/${resource_id}`),
}

// Dashboard endpoints
export const dashboardApi = {
  getOverview: () => apiClient.get('/dashboard/overview'),
  getOverdue: (params?: { skip?: number; limit?: number }) =>
    apiClient.get('/dashboard/overdue', { params }),
  getUpcoming: (params?: { days?: number; skip?: number; limit?: number }) =>
    apiClient.get('/dashboard/upcoming', { params }),
  getOwnerHeatmap: () => apiClient.get('/dashboard/owner-heatmap'),
  getCategoryBreakdown: () => apiClient.get('/dashboard/category-breakdown'),
}

// Notification endpoints
export const notificationsApi = {
  list: (params?: { is_read?: boolean; skip?: number; limit?: number }) =>
    apiClient.get('/notifications', { params }),
  getCount: () => apiClient.get('/notifications/count'),
  get: (id: string) => apiClient.get(`/notifications/${id}`),
  markRead: (id: string) => apiClient.put(`/notifications/${id}/read`),
  markMultipleRead: (notificationIds: string[]) =>
    apiClient.post('/notifications/mark-read', { notification_ids: notificationIds }),
  markAllRead: () => apiClient.post('/notifications/mark-all-read'),
  delete: (id: string) => apiClient.delete(`/notifications/${id}`),
  deleteMultiple: (notificationIds: string[]) =>
    apiClient.delete('/notifications', { data: { notification_ids: notificationIds } }),
}

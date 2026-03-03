import axios from 'axios'
import type {
  JobInfo,
  UploadResponse,
  ParameterCheckRequest,
  TrendChartRequest,
  StressCurveRequest,
  NormalDistributionRequest,
  ReportGenerationRequest,
} from './types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// ==================== Jobs API ====================
export const jobsApi = {
  getJob: (jobId: string) => api.get<JobInfo>(`/jobs/${jobId}`),
  listJobs: (params?: { status?: string; job_type?: string; limit?: number; offset?: number }) =>
    api.get<{ jobs: JobInfo[]; total: number }>('/jobs/', { params }),
  downloadResult: (jobId: string) =>
    `${api.defaults.baseURL}/jobs/${jobId}/download`,
}

// ==================== Parameter Check API ====================
export const parameterCheckApi = {
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('files', file)
    return api.post<UploadResponse>('/parameter-check/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  process: (data: ParameterCheckRequest) =>
    api.post<{ job_id: string; status: string; message: string }>('/parameter-check/process', data),
  preview: (fileId: string) =>
    api.get(`/parameter-check/preview/${fileId}`),
}

// ==================== Trend Chart API ====================
export const trendChartApi = {
  generateVF: (data: TrendChartRequest) =>
    api.post<{ job_id: string; status: string; message: string }>('/trend-chart/vf', data),
  generateBV: (data: TrendChartRequest) =>
    api.post<{ job_id: string; status: string; message: string }>('/trend-chart/bv', data),
  generateIR: (data: TrendChartRequest) =>
    api.post<{ job_id: string; status: string; message: string }>('/trend-chart/ir', data),
  getDataTemplate: () =>
    api.get('/trend-chart/data-template'),
}

// ==================== Stress Curve API ====================
export const stressCurveApi = {
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<UploadResponse>('/stress-curve/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  analyze: (data: StressCurveRequest) =>
    api.post<{ job_id: string; status: string; message: string }>('/stress-curve/analyze', data),
  preview: (fileId: string) =>
    api.get(`/stress-curve/preview/${fileId}`),
}

// ==================== Normal Distribution API ====================
export const normalDistributionApi = {
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<UploadResponse>('/normal-distribution/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  analyze: (data: NormalDistributionRequest) =>
    api.post<{ job_id: string; status: string; message: string }>('/normal-distribution/analyze', data),
  preview: (fileId: string) =>
    api.get(`/normal-distribution/preview/${fileId}`),
}

// ==================== Report Generation API ====================
export const reportGenerationApi = {
  uploadTemplate: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<UploadResponse>('/report/upload-template', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  uploadData: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<UploadResponse>('/report/upload-data', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  generate: (data: ReportGenerationRequest) =>
    api.post<{ job_id: string; status: string; message: string }>('/report/generate', data),
  getReportTypes: () =>
    api.get('/report/report-types'),
}

export default api
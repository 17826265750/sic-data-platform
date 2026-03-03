import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'
import type {
  JobInfo,
  UploadResponse,
  ParameterCheckRequest,
  TrendChartRequest,
  StressCurveRequest,
  NormalDistributionRequest,
  ReportGenerationRequest,
} from './types'

// API Error class for better error handling
export class ApiError extends Error {
  public status: number
  public detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add timestamp to prevent caching for GET requests
    if (config.method === 'get') {
      config.params = { ...config.params, _t: Date.now() }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - improved error handling
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<{ detail?: string; error?: string; message?: string }>) => {
    // Extract error message
    let errorMessage = '请求失败，请稍后重试'
    let status = 500

    if (error.response) {
      // Server responded with error status
      status = error.response.status
      const data = error.response.data

      if (data?.detail) {
        errorMessage = data.detail
      } else if (data?.error) {
        errorMessage = data.error
      } else if (data?.message) {
        errorMessage = data.message
      } else if (status === 400) {
        errorMessage = '请求参数错误'
      } else if (status === 401) {
        errorMessage = '未授权，请重新登录'
      } else if (status === 403) {
        errorMessage = '没有权限访问'
      } else if (status === 404) {
        errorMessage = '请求的资源不存在'
      } else if (status === 422) {
        errorMessage = '数据验证失败'
      } else if (status === 500) {
        errorMessage = '服务器内部错误'
      }
    } else if (error.request) {
      // Request was made but no response received
      if (error.code === 'ECONNABORTED') {
        errorMessage = '请求超时，请检查网络连接'
      } else {
        errorMessage = '网络连接失败，请检查网络'
      }
    } else {
      // Error in request setup
      errorMessage = error.message || '请求配置错误'
    }

    // Log error for debugging
    console.error('API Error:', {
      status,
      message: errorMessage,
      url: error.config?.url,
      method: error.config?.method,
    })

    // Show user-friendly message for non-4xx errors
    if (status >= 500 || !error.response) {
      message.error(errorMessage)
    }

    return Promise.reject(new ApiError(status, errorMessage))
  }
)

// ==================== Jobs API ====================
export const jobsApi = {
  getJob: (jobId: string) => api.get<JobInfo>(`/jobs/${jobId}`),
  listJobs: (params?: { status?: string; job_type?: string; limit?: number; offset?: number }) =>
    api.get<{ jobs: JobInfo[]; total: number }>('/jobs/', { params }),
  downloadResult: (jobId: string) =>
    `${api.defaults.baseURL}/jobs/${jobId}/download`,
  deleteJob: (jobId: string) =>
    api.delete(`/jobs/${jobId}`),
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
  uploadMultiple: (files: File[]) => {
    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))
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
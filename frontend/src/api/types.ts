// API Types
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface JobInfo {
  job_id: string
  job_type: string
  status: JobStatus
  progress: number
  message?: string
  result?: Record<string, unknown>
  error?: string
  created_at: string
  updated_at: string
}

export interface UploadResponse {
  file_id: string
  filename: string
  size: number
  message: string
}

// Parameter Check
export interface ParameterCheckRequest {
  file_ids: string[]
  column_mapping?: Record<string, number>
}

// Trend Chart
export interface TrendChartRequest {
  chart_type: 'VF' | 'BV' | 'IR'
  product_list: string[]
  time_labels: string[]
  means: Record<string, number[]>
  stds: Record<string, number[]>
}

// Stress Curve
export interface StressCurveRequest {
  file_id: string
  time_start: number
  time_end: number
  leakage_columns: string
  show_legend: boolean
  smooth_data: boolean
  smooth_window: number
}

// Normal Distribution
export interface NormalDistributionRequest {
  file_id: string
  params: string[]
  times: string[]
  sheets?: string[]
  enable_outlier_removal: boolean
  outlier_sigma: number
}

// Report Generation
export interface ReportGenerationRequest {
  template_id: string
  data_file_id: string
  report_type: string
  output_name?: string
}
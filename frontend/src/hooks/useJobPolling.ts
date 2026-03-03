import { useState, useEffect, useCallback, useRef } from 'react'
import { jobsApi } from '../api'
import type { JobInfo } from '../api/types'

interface UseJobPollingOptions {
  /** Polling interval in milliseconds */
  interval?: number
  /** Maximum number of polling attempts */
  maxAttempts?: number
  /** Callback when job completes successfully */
  onComplete?: (job: JobInfo) => void
  /** Callback when job fails */
  onError?: (error: string) => void
}

/**
 * Custom hook for polling job status
 * Handles cleanup on unmount to prevent memory leaks
 */
export function useJobPolling(options: UseJobPollingOptions = {}) {
  const { interval = 2000, maxAttempts = 1800, onComplete, onError } = options // 1 hour max

  const [job, setJob] = useState<JobInfo | null>(null)
  const [isPolling, setIsPolling] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isMountedRef = useRef(true)
  const timeoutIdRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const attemptsRef = useRef(0)

  const clearPolling = useCallback(() => {
    if (timeoutIdRef.current) {
      clearTimeout(timeoutIdRef.current)
      timeoutIdRef.current = null
    }
    setIsPolling(false)
  }, [])

  const pollJob = useCallback(async (jobId: string) => {
    if (!isMountedRef.current) return

    attemptsRef.current += 1

    if (attemptsRef.current > maxAttempts) {
      setError('轮询超时，请手动刷新查看结果')
      clearPolling()
      return
    }

    try {
      const response = await jobsApi.getJob(jobId)

      if (!isMountedRef.current) return

      const jobData = response.data
      setJob(jobData)

      // Check if job is still running
      if (jobData.status === 'pending' || jobData.status === 'running') {
        timeoutIdRef.current = setTimeout(() => pollJob(jobId), interval)
      } else {
        clearPolling()

        if (jobData.status === 'completed' && onComplete) {
          onComplete(jobData)
        } else if (jobData.status === 'failed' && onError) {
          onError(jobData.error || '任务处理失败')
        }
      }
    } catch (err) {
      if (!isMountedRef.current) return

      const errorMessage = err instanceof Error ? err.message : '获取任务状态失败'
      setError(errorMessage)
      clearPolling()

      if (onError) {
        onError(errorMessage)
      }
    }
  }, [interval, maxAttempts, clearPolling, onComplete, onError])

  const startPolling = useCallback((jobId: string) => {
    // Reset state
    setJob(null)
    setError(null)
    attemptsRef.current = 0

    // Start polling
    setIsPolling(true)
    pollJob(jobId)
  }, [pollJob])

  const stopPolling = useCallback(() => {
    clearPolling()
  }, [clearPolling])

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true

    return () => {
      isMountedRef.current = false
      clearPolling()
    }
  }, [clearPolling])

  return {
    job,
    isPolling,
    error,
    startPolling,
    stopPolling,
  }
}

export default useJobPolling
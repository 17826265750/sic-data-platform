import { useState, useEffect } from 'react'
import { Card, Table, Tag, Button, Space, Select, Typography, Badge } from 'antd'
import { DownloadOutlined, ReloadOutlined, EyeOutlined } from '@ant-design/icons'
import { jobsApi } from '../api'
import type { JobInfo, JobStatus } from '../api/types'

const { Title } = Typography

const statusColors: Record<JobStatus, string> = {
  pending: 'default',
  running: 'processing',
  completed: 'success',
  failed: 'error',
  cancelled: 'warning',
}

const statusTexts: Record<JobStatus, string> = {
  pending: '等待中',
  running: '处理中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
}

export default function JobHistory() {
  const [jobs, setJobs] = useState<JobInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [total, setTotal] = useState(0)

  const loadJobs = async () => {
    setLoading(true)
    try {
      const response = await jobsApi.listJobs({
        status: statusFilter,
        limit: 50,
      })
      setJobs(response.data.jobs)
      setTotal(response.data.total)
    } catch (error) {
      console.error('Load jobs error:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadJobs()
    // 定时刷新
    const interval = setInterval(loadJobs, 10000)
    return () => clearInterval(interval)
  }, [statusFilter])

  const handleDownload = (jobId: string) => {
    window.open(jobsApi.downloadResult(jobId), '_blank')
  }

  const columns = [
    {
      title: '任务ID',
      dataIndex: 'job_id',
      key: 'job_id',
      width: 280,
      render: (id: string) => (
        <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{id.slice(0, 8)}...</span>
      ),
    },
    {
      title: '任务类型',
      dataIndex: 'job_type',
      key: 'job_type',
      width: 150,
      render: (type: string) => {
        const typeMap: Record<string, string> = {
          parameter_check: '参数检查',
          trend_chart_vf: 'VF趋势图',
          trend_chart_bv: 'BV趋势图',
          trend_chart_ir: 'IR趋势图',
          stress_curve: '应力曲线',
          normal_distribution: '正态分布',
          report_generation: '报告生成',
        }
        return typeMap[type] || type
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: JobStatus) => (
        <Tag color={statusColors[status]}>{statusTexts[status]}</Tag>
      ),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 80,
      render: (progress: number, record: JobInfo) => (
        record.status === 'running' || record.status === 'pending'
          ? `${progress}%`
          : '-'
      ),
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
      render: (msg: string) => msg || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: JobInfo) => (
        <Space>
          {record.status === 'completed' && (
            <Button
              type="link"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record.job_id)}
            >
              下载
            </Button>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Card
        title={
          <Space>
            <Title level={4} style={{ margin: 0 }}>任务历史</Title>
            <Badge count={total} style={{ backgroundColor: '#1677ff' }} />
          </Space>
        }
        extra={
          <Space>
            <Select
              style={{ width: 150 }}
              placeholder="筛选状态"
              allowClear
              onChange={setStatusFilter}
              options={[
                { label: '全部', value: undefined },
                { label: '等待中', value: 'pending' },
                { label: '处理中', value: 'running' },
                { label: '已完成', value: 'completed' },
                { label: '失败', value: 'failed' },
              ]}
            />
            <Button icon={<ReloadOutlined />} onClick={loadJobs}>
              刷新
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={jobs}
          columns={columns}
          rowKey="job_id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: false,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>
    </div>
  )
}
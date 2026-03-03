import { Progress, Card, Button, Typography, Space, Tag } from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import { JobStatus } from '../../api/types'

const { Text, Paragraph } = Typography

interface JobProgressProps {
  jobId: string
  status: JobStatus
  progress: number
  message?: string
  error?: string
  result?: Record<string, unknown>
  onDownload?: () => void
}

const statusConfig = {
  pending: { color: 'default', icon: <ClockCircleOutlined />, text: '等待中' },
  running: { color: 'processing', icon: <LoadingOutlined />, text: '处理中' },
  completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
  failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
  cancelled: { color: 'warning', icon: <CloseCircleOutlined />, text: '已取消' },
}

export default function JobProgress({
  jobId,
  status,
  progress,
  message,
  error,
  result,
  onDownload,
}: JobProgressProps) {
  const config = statusConfig[status] || statusConfig.pending

  return (
    <Card
      title={
        <Space>
          <span>任务进度</span>
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        </Space>
      }
      extra={
        status === 'completed' && onDownload && (
          <Button type="primary" icon={<DownloadOutlined />} onClick={onDownload}>
            下载结果
          </Button>
        )
      }
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <div>
          <Text type="secondary">任务ID: </Text>
          <Text code>{jobId}</Text>
        </div>

        {(status === 'running' || status === 'pending') && (
          <Progress
            percent={progress}
            status={status === 'running' ? 'active' : 'normal'}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
        )}

        {message && (
          <Paragraph
            ellipsis={{ rows: 2 }}
            style={{ marginBottom: 0, color: '#666' }}
          >
            {message}
          </Paragraph>
        )}

        {error && (
          <Paragraph type="danger" style={{ marginBottom: 0 }}>
            错误: {error}
          </Paragraph>
        )}

        {status === 'completed' && result && (
          <div>
            <Text type="secondary">处理结果: </Text>
            <Text>
              {typeof result === 'object' && 'output_files' in result
                ? `${(result.output_files as string[]).length} 个文件已生成`
                : '处理完成'}
            </Text>
          </div>
        )}
      </Space>
    </Card>
  )
}
import { useState } from 'react'
import { Card, Button, Space, Upload, message, List, Typography, Steps } from 'antd'
import { UploadOutlined, PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons'
import FileUploader from '../components/common/FileUploader'
import JobProgress from '../components/common/JobProgress'
import { parameterCheckApi, jobsApi } from '../api'
import type { JobInfo } from '../api/types'

const { Text, Paragraph } = Typography

export default function ParameterCheck() {
  const [uploadedFiles, setUploadedFiles] = useState<{ id: string; name: string }[]>([])
  const [currentJob, setCurrentJob] = useState<JobInfo | null>(null)
  const [loading, setLoading] = useState(false)

  const handleUploadSuccess = (fileId: string, filename: string) => {
    setUploadedFiles((prev) => [...prev, { id: fileId, name: filename }])
  }

  const handleProcess = async () => {
    if (uploadedFiles.length === 0) {
      message.warning('请先上传文件')
      return
    }

    setLoading(true)
    try {
      const response = await parameterCheckApi.process({
        file_ids: uploadedFiles.map((f) => f.id),
      })

      // 开始轮询任务状态
      pollJobStatus(response.data.job_id)
    } catch (error) {
      message.error('启动处理任务失败')
    } finally {
      setLoading(false)
    }
  }

  const pollJobStatus = async (jobId: string) => {
    const poll = async () => {
      try {
        const response = await jobsApi.getJob(jobId)
        setCurrentJob(response.data)

        if (response.data.status === 'pending' || response.data.status === 'running') {
          setTimeout(poll, 2000)
        }
      } catch (error) {
        console.error('Poll error:', error)
      }
    }

    poll()
  }

  const handleDownload = () => {
    if (currentJob) {
      window.open(jobsApi.downloadResult(currentJob.job_id), '_blank')
    }
  }

  const handleReset = () => {
    setUploadedFiles([])
    setCurrentJob(null)
  }

  return (
    <div>
      <Steps
        current={currentJob ? (currentJob.status === 'completed' ? 2 : 1) : 0}
        items={[
          { title: '上传文件', description: '上传Excel模板和数据文件' },
          { title: '处理数据', description: '自动匹配和填充数据' },
          { title: '下载结果', description: '获取处理后的文件' },
        ]}
        style={{ marginBottom: 24 }}
      />

      <Card title="文件上传" style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Paragraph type="secondary">
            请上传需要处理的Excel文件，包括模板文件（包含"数据处理"的文件）、源数据文件（H3TRB/HTRB时间点数据）和应力数据文件。
          </Paragraph>

          <FileUploader
            multiple
            maxCount={20}
            uploadUrl="/api/v1/parameter-check/upload"
            onUploadSuccess={handleUploadSuccess}
            hint="支持多个Excel文件，单个文件不超过50MB"
          />

          {uploadedFiles.length > 0 && (
            <List
              size="small"
              header={`已上传 ${uploadedFiles.length} 个文件`}
              dataSource={uploadedFiles}
              renderItem={(item) => (
                <List.Item>
                  <Text>{item.name}</Text>
                </List.Item>
              )}
            />
          )}
        </Space>
      </Card>

      <Space style={{ marginBottom: 24 }}>
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={handleProcess}
          loading={loading}
          disabled={uploadedFiles.length === 0}
        >
          开始处理
        </Button>
        <Button icon={<ReloadOutlined />} onClick={handleReset}>
          重置
        </Button>
      </Space>

      {currentJob && (
        <JobProgress
          jobId={currentJob.job_id}
          status={currentJob.status}
          progress={currentJob.progress}
          message={currentJob.message}
          error={currentJob.error}
          result={currentJob.result}
          onDownload={handleDownload}
        />
      )}
    </div>
  )
}
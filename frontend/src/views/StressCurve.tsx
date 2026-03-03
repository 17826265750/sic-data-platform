import { useState, useEffect } from 'react'
import { Card, Form, Button, Space, InputNumber, Switch, Select, Typography, Divider, message, Alert } from 'antd'
import { PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons'
import FileUploader from '../components/common/FileUploader'
import JobProgress from '../components/common/JobProgress'
import { stressCurveApi, jobsApi } from '../api'
import type { JobInfo } from '../api/types'

const { Paragraph, Text } = Typography

export default function StressCurve() {
  const [fileId, setFileId] = useState<string | null>(null)
  const [fileInfo, setFileInfo] = useState<{
    filename: string
    channels_count: number
    time_range: { min: number; max: number }
    leakage_columns: string[]
  } | null>(null)
  const [currentJob, setCurrentJob] = useState<JobInfo | null>(null)
  const [loading, setLoading] = useState(false)

  const [form] = Form.useForm()

  const handleUploadSuccess = async (uploadedFileId: string, filename: string) => {
    setFileId(uploadedFileId)
    // 获取文件预览信息
    try {
      const response = await stressCurveApi.preview(uploadedFileId)
      setFileInfo(response.data)
      form.setFieldsValue({
        time_start: response.data.time_range?.min || 0,
        time_end: response.data.time_range?.max || 1000,
      })
    } catch (error) {
      console.error('Preview error:', error)
    }
  }

  const handleAnalyze = async () => {
    if (!fileId) {
      message.warning('请先上传数据文件')
      return
    }

    const values = form.getFieldsValue()
    setLoading(true)

    try {
      const response = await stressCurveApi.analyze({
        file_id: fileId,
        time_start: values.time_start || 0,
        time_end: values.time_end || 1000,
        leakage_columns: values.leakage_columns || 'all',
        show_legend: values.show_legend || false,
        smooth_data: values.smooth_data || false,
        smooth_window: values.smooth_window || 5,
      })

      pollJobStatus(response.data.job_id)
    } catch (error) {
      message.error('启动分析任务失败')
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
    setFileId(null)
    setFileInfo(null)
    setCurrentJob(null)
    form.resetFields()
  }

  return (
    <div>
      <Card title="文件上传" style={{ marginBottom: 24 }}>
        <Paragraph type="secondary">
          上传应力数据Excel文件，文件应包含时间列、温度列和漏电流列（I1-I80）。
        </Paragraph>

        <FileUploader
          accept=".xlsx,.xls"
          uploadUrl="/api/v1/stress-curve/upload"
          onUploadSuccess={handleUploadSuccess}
          hint="支持Excel文件，需包含时间和漏电流数据"
        />

        {fileInfo && (
          <Alert
            type="info"
            style={{ marginTop: 16 }}
            message={`文件: ${fileInfo.filename}`}
            description={
              <Space direction="vertical">
                <Text>漏电流通道数: {fileInfo.channels_count}</Text>
                <Text>
                  时间范围: {fileInfo.time_range?.min || 0} - {fileInfo.time_range?.max || 1000} 小时
                </Text>
              </Space>
            }
          />
        )}
      </Card>

      <Card title="分析参数" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" initialValues={{
          time_start: 0,
          time_end: 1000,
          leakage_columns: 'all',
          show_legend: false,
          smooth_data: false,
          smooth_window: 5,
        }}>
          <Space size="large" wrap>
            <Form.Item label="时间范围开始" name="time_start">
              <InputNumber min={0} max={1000} />
            </Form.Item>
            <Form.Item label="时间范围结束" name="time_end">
              <InputNumber min={0} max={1000} />
            </Form.Item>
            <Form.Item label="漏电流列" name="leakage_columns">
              <Select style={{ width: 200 }}>
                <Select.Option value="all">全部通道</Select.Option>
                {fileInfo?.leakage_columns?.slice(0, 10).map((col) => (
                  <Select.Option key={col} value={col}>{col}</Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Space>

          <Divider />

          <Space size="large">
            <Form.Item label="显示图例" name="show_legend" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item label="数据平滑" name="smooth_data" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item label="平滑窗口" name="smooth_window">
              <InputNumber min={3} max={21} step={2} />
            </Form.Item>
          </Space>
        </Form>
      </Card>

      <Space style={{ marginBottom: 24 }}>
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={handleAnalyze}
          loading={loading}
          disabled={!fileId}
        >
          开始分析
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
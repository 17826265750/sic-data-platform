import { useState, useCallback, useEffect } from 'react'
import { Card, Form, Button, Space, Select, Switch, InputNumber, Checkbox, Typography, Divider, message, Alert } from 'antd'
import { PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons'
import FileUploader from '../components/common/FileUploader'
import JobProgress from '../components/common/JobProgress'
import { normalDistributionApi, jobsApi } from '../api'
import { useJobPolling } from '../hooks/useJobPolling'

const { Paragraph, Text } = Typography

export default function NormalDistribution() {
  const [fileId, setFileId] = useState<string | null>(null)
  const [fileInfo, setFileInfo] = useState<{
    filename: string
    sheets: string[]
    sheet_count: number
    available_params: string[]
    available_times: string[]
  } | null>(null)

  const [form] = Form.useForm()

  // Use custom hook for job polling
  const { job, isPolling, startPolling, stopPolling } = useJobPolling({
    onComplete: () => message.success('正态分布分析完成！'),
    onError: (error) => message.error(`分析失败: ${error}`),
  })

  const handleUploadSuccess = useCallback(async (uploadedFileId: string, filename: string) => {
    setFileId(uploadedFileId)
    try {
      const response = await normalDistributionApi.preview(uploadedFileId)
      setFileInfo(response.data)
      form.setFieldsValue({
        params: response.data.available_params,
        times: response.data.available_times?.slice(0, 2) || ['T0', '168h'],
      })
    } catch (error) {
      console.error('Preview error:', error)
    }
  }, [form])

  const handleAnalyze = useCallback(async () => {
    if (!fileId) {
      message.warning('请先上传数据文件')
      return
    }

    const values = form.getFieldsValue()

    try {
      const response = await normalDistributionApi.analyze({
        file_id: fileId,
        params: values.params || ['VF', 'IR', 'BV'],
        times: values.times || ['T0', '168h'],
        sheets: values.sheets,
        enable_outlier_removal: values.enable_outlier_removal ?? true,
        outlier_sigma: values.outlier_sigma || 3.0,
      })

      startPolling(response.data.job_id)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '启动分析任务失败'
      message.error(errorMessage)
    }
  }, [fileId, form, startPolling])

  const handleDownload = useCallback(() => {
    if (job) {
      window.open(jobsApi.downloadResult(job.job_id), '_blank')
    }
  }, [job])

  const handleReset = useCallback(() => {
    stopPolling()
    setFileId(null)
    setFileInfo(null)
    form.resetFields()
  }, [stopPolling, form])

  return (
    <div>
      <Card title="数据文件上传" style={{ marginBottom: 24 }}>
        <Paragraph type="secondary">
          上传包含多产品参数数据的Excel文件，每个Sheet代表一个产品，包含各时间点的VF/IR/BV参数。
        </Paragraph>

        <FileUploader
          accept=".xlsx,.xls"
          uploadUrl="/api/v1/normal-distribution/upload"
          onUploadSuccess={handleUploadSuccess}
          hint="支持多Sheet的Excel文件"
        />

        {fileInfo && (
          <Alert
            type="info"
            style={{ marginTop: 16 }}
            message={`文件: ${fileInfo.filename}`}
            description={
              <Space direction="vertical">
                <Text>产品数量: {fileInfo.sheet_count} 个Sheet</Text>
                <Text>可用参数: {fileInfo.available_params?.join(', ')}</Text>
                <Text>可用时间点: {fileInfo.available_times?.join(', ')}</Text>
              </Space>
            }
          />
        )}
      </Card>

      <Card title="分析参数" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" initialValues={{
          params: ['VF', 'IR', 'BV'],
          times: ['T0', '168h'],
          enable_outlier_removal: true,
          outlier_sigma: 3.0,
        }}>
          <Form.Item label="分析参数" name="params">
            <Checkbox.Group>
              <Space>
                <Checkbox value="VF">VF (正向电压)</Checkbox>
                <Checkbox value="IR">IR (反向漏电流)</Checkbox>
                <Checkbox value="BV">BV (击穿电压)</Checkbox>
              </Space>
            </Checkbox.Group>
          </Form.Item>

          <Form.Item label="对比时间点" name="times">
            <Checkbox.Group>
              <Space>
                {fileInfo?.available_times?.map((time) => (
                  <Checkbox key={time} value={time}>{time}</Checkbox>
                )) || (
                  <>
                    <Checkbox value="T0">T0</Checkbox>
                    <Checkbox value="168h">168h</Checkbox>
                    <Checkbox value="500h">500h</Checkbox>
                    <Checkbox value="1000h">1000h</Checkbox>
                  </>
                )}
              </Space>
            </Checkbox.Group>
          </Form.Item>

          <Form.Item label="选择产品Sheet" name="sheets">
            <Select
              mode="multiple"
              style={{ width: '100%' }}
              placeholder="不选择则分析全部产品"
              options={fileInfo?.sheets?.map((s) => ({ label: s, value: s })) || []}
            />
          </Form.Item>

          <Divider />

          <Space size="large">
            <Form.Item label="3-sigma异常值移除" name="enable_outlier_removal" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item label="Sigma阈值" name="outlier_sigma">
              <InputNumber min={1} max={5} step={0.5} />
            </Form.Item>
          </Space>
        </Form>
      </Card>

      <Space style={{ marginBottom: 24 }}>
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={handleAnalyze}
          loading={isPolling}
          disabled={!fileId || isPolling}
        >
          {isPolling ? '分析中...' : '开始分析'}
        </Button>
        <Button icon={<ReloadOutlined />} onClick={handleReset}>
          重置
        </Button>
      </Space>

      {job && (
        <JobProgress
          jobId={job.job_id}
          status={job.status}
          progress={job.progress}
          message={job.message}
          error={job.error}
          result={job.result}
          onDownload={handleDownload}
        />
      )}
    </div>
  )
}
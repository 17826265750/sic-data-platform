import { useState, useCallback, useEffect } from 'react'
import { Card, Form, Button, Space, Select, Typography, message, Alert, Steps, Upload, Input } from 'antd'
import { PlayCircleOutlined, ReloadOutlined, UploadOutlined } from '@ant-design/icons'
import JobProgress from '../components/common/JobProgress'
import { reportGenerationApi, jobsApi } from '../api'
import { useJobPolling } from '../hooks/useJobPolling'

const { Paragraph } = Typography

export default function ReportGeneration() {
  const [templateId, setTemplateId] = useState<string | null>(null)
  const [dataFileId, setDataFileId] = useState<string | null>(null)
  const [reportTypes, setReportTypes] = useState<{ code: string; name: string; description: string }[]>([])
  const [currentStep, setCurrentStep] = useState(0)

  const [form] = Form.useForm()

  // Use custom hook for job polling
  const { job, isPolling, startPolling, stopPolling } = useJobPolling({
    onComplete: () => message.success('报告生成完成！'),
    onError: (error) => message.error(`生成失败: ${error}`),
  })

  useEffect(() => {
    loadReportTypes()
  }, [])

  const loadReportTypes = useCallback(async () => {
    try {
      const response = await reportGenerationApi.getReportTypes()
      setReportTypes(response.data.report_types)
    } catch (error) {
      console.error('Load report types error:', error)
    }
  }, [])

  const handleTemplateUpload = useCallback(async (file: File) => {
    try {
      const response = await reportGenerationApi.uploadTemplate(file)
      setTemplateId(response.data.file_id)
      setCurrentStep(1)
      message.success('模板上传成功')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '模板上传失败'
      message.error(errorMessage)
    }
    return false
  }, [])

  const handleDataUpload = useCallback(async (file: File) => {
    try {
      const response = await reportGenerationApi.uploadData(file)
      setDataFileId(response.data.file_id)
      setCurrentStep(2)
      message.success('数据文件上传成功')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '数据文件上传失败'
      message.error(errorMessage)
    }
    return false
  }, [])

  const handleGenerate = useCallback(async () => {
    if (!templateId || !dataFileId) {
      message.warning('请先上传模板和数据文件')
      return
    }

    const values = form.getFieldsValue()

    try {
      const response = await reportGenerationApi.generate({
        template_id: templateId,
        data_file_id: dataFileId,
        report_type: values.report_type || 'HTRB',
        output_name: values.output_name,
      })

      startPolling(response.data.job_id)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '启动报告生成失败'
      message.error(errorMessage)
    }
  }, [templateId, dataFileId, form, startPolling])

  const handleDownload = useCallback(() => {
    if (job) {
      window.open(jobsApi.downloadResult(job.job_id), '_blank')
    }
  }, [job])

  const handleReset = useCallback(() => {
    stopPolling()
    setTemplateId(null)
    setDataFileId(null)
    setCurrentStep(0)
    form.resetFields()
  }, [stopPolling, form])

  return (
    <div>
      <Steps
        current={currentStep}
        items={[
          { title: '上传Word模板', description: '上传.docx报告模板' },
          { title: '上传数据文件', description: '上传Excel测试数据' },
          { title: '生成报告', description: '选择报告类型并生成' },
        ]}
        style={{ marginBottom: 24 }}
      />

      <Card title="1. Word模板上传" style={{ marginBottom: 24 }}>
        <Paragraph type="secondary">
          上传Word报告模板文件，模板中应包含需要填充数据的表格。
        </Paragraph>

        <Upload
          accept=".docx"
          beforeUpload={handleTemplateUpload}
          showUploadList={false}
        >
          <Button icon={<UploadOutlined />} disabled={!!templateId}>
            {templateId ? '已上传模板' : '选择Word模板'}
          </Button>
        </Upload>

        {templateId && (
          <Alert
            type="success"
            message="模板已上传"
            style={{ marginTop: 16 }}
          />
        )}
      </Card>

      <Card title="2. 数据文件上传" style={{ marginBottom: 24 }}>
        <Paragraph type="secondary">
          上传包含测试数据的Excel文件。
        </Paragraph>

        <Upload
          accept=".xlsx,.xls"
          beforeUpload={handleDataUpload}
          showUploadList={false}
        >
          <Button icon={<UploadOutlined />} disabled={!!dataFileId || !templateId}>
            {dataFileId ? '已上传数据文件' : '选择Excel数据文件'}
          </Button>
        </Upload>

        {dataFileId && (
          <Alert
            type="success"
            message="数据文件已上传"
            style={{ marginTop: 16 }}
          />
        )}
      </Card>

      <Card title="3. 报告配置" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" initialValues={{
          report_type: 'HTRB',
        }}>
          <Form.Item label="报告类型" name="report_type">
            <Select style={{ width: 300 }}>
              {reportTypes.map((type) => (
                <Select.Option key={type.code} value={type.code}>
                  {type.name} - {type.description}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="输出文件名 (可选)" name="output_name">
            <Input
              style={{ width: 300 }}
              placeholder="不填写则自动生成"
            />
          </Form.Item>
        </Form>
      </Card>

      <Space style={{ marginBottom: 24 }}>
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={handleGenerate}
          loading={isPolling}
          disabled={!templateId || !dataFileId || isPolling}
        >
          {isPolling ? '生成中...' : '生成报告'}
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
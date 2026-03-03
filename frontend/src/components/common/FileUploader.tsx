import { Upload, message, Card, Typography, Row, Col } from 'antd'
import { InboxOutlined, FileExcelOutlined, FileWordOutlined } from '@ant-design/icons'
import { UploadProps } from 'antd/es/upload'
import { useState } from 'react'

const { Dragger } = Upload
const { Text } = Typography

interface FileUploaderProps {
  accept?: string
  multiple?: boolean
  maxCount?: number
  uploadUrl: string
  onUploadSuccess?: (fileId: string, filename: string) => void
  onUploadError?: (error: string) => void
  hint?: string
}

export default function FileUploader({
  accept = '.xlsx,.xls',
  multiple = false,
  maxCount = 1,
  uploadUrl,
  onUploadSuccess,
  onUploadError,
  hint = '支持 Excel 文件 (.xlsx, .xls)',
}: FileUploaderProps) {
  const [uploading, setUploading] = useState(false)

  const props: UploadProps = {
    name: 'file',
    multiple,
    accept,
    maxCount,
    action: uploadUrl,
    showUploadList: false,
    onChange(info) {
      const { status } = info.file
      if (status === 'uploading') {
        setUploading(true)
      }
      if (status === 'done') {
        setUploading(false)
        const response = info.file.response
        if (response) {
          message.success(`${info.file.name} 上传成功`)
          onUploadSuccess?.(response.file_id, info.file.name)
        }
      } else if (status === 'error') {
        setUploading(false)
        message.error(`${info.file.name} 上传失败`)
        onUploadError?.('上传失败')
      }
    },
    beforeUpload(file) {
      const isValidType = accept.split(',').some((ext) =>
        file.name.toLowerCase().endsWith(ext.trim())
      )
      if (!isValidType) {
        message.error(`只支持 ${accept} 格式的文件`)
        return Upload.LIST_IGNORE
      }
      const isLt50M = file.size / 1024 / 1024 < 50
      if (!isLt50M) {
        message.error('文件大小不能超过 50MB')
        return Upload.LIST_IGNORE
      }
      return true
    },
  }

  return (
    <Dragger {...props} disabled={uploading}>
      <p className="ant-upload-drag-icon">
        <InboxOutlined style={{ color: '#1677ff' }} />
      </p>
      <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
      <p className="ant-upload-hint">{hint}</p>
    </Dragger>
  )
}

// 文件图标组件
export function FileIcon({ filename }: { filename: string }) {
  const ext = filename.split('.').pop()?.toLowerCase()
  if (ext === 'xlsx' || ext === 'xls') {
    return <FileExcelOutlined style={{ color: '#52c41a', fontSize: 24 }} />
  }
  if (ext === 'docx' || ext === 'doc') {
    return <FileWordOutlined style={{ color: '#1677ff', fontSize: 24 }} />
  }
  return null
}
import { useState } from 'react'
import { Card, Form, Button, Space, Input, Select, Typography, Divider, message, Table, Tabs } from 'antd'
import { PlayCircleOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import JobProgress from '../components/common/JobProgress'
import { trendChartApi, jobsApi } from '../api'
import type { JobInfo } from '../api/types'

const { Title, Paragraph, Text } = Typography
const { TabPane } = Tabs

interface ProductData {
  name: string
  means: number[]
  stds: number[]
}

export default function TrendChart() {
  const [form] = Form.useForm()
  const [products, setProducts] = useState<ProductData[]>([
    { name: '', means: [0, 0, 0, 0], stds: [0, 0, 0, 0] },
  ])
  const [currentJob, setCurrentJob] = useState<JobInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [chartType, setChartType] = useState<'VF' | 'BV' | 'IR'>('VF')

  const timeLabels = ['初始值(T0)', '168小时', '500小时', '1000小时']

  const addProduct = () => {
    setProducts([
      ...products,
      { name: '', means: [0, 0, 0, 0], stds: [0, 0, 0, 0] },
    ])
  }

  const removeProduct = (index: number) => {
    if (products.length > 1) {
      setProducts(products.filter((_, i) => i !== index))
    }
  }

  const updateProduct = (
    index: number,
    field: 'name' | 'means' | 'stds',
    value: string | number[]
  ) => {
    const newProducts = [...products]
    if (field === 'name') {
      newProducts[index].name = value as string
    } else {
      newProducts[index][field] = value as number[]
    }
    setProducts(newProducts)
  }

  const handleGenerate = async (type: 'VF' | 'BV' | 'IR') => {
    // 验证数据
    const validProducts = products.filter((p) => p.name.trim() !== '')
    if (validProducts.length === 0) {
      message.warning('请至少添加一个产品')
      return
    }

    setChartType(type)
    setLoading(true)

    try {
      const means: Record<string, number[]> = {}
      const stds: Record<string, number[]> = {}

      validProducts.forEach((p) => {
        means[p.name] = p.means
        stds[p.name] = p.stds
      })

      const response = await trendChartApi.generateVF({
        chart_type: type,
        product_list: validProducts.map((p) => p.name),
        time_labels: timeLabels,
        means,
        stds,
      })

      pollJobStatus(response.data.job_id)
    } catch (error) {
      message.error('启动任务失败')
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

  const columns = [
    {
      title: '产品型号',
      dataIndex: 'name',
      key: 'name',
      render: (value: string, _: ProductData, index: number) => (
        <Input
          value={value}
          onChange={(e) => updateProduct(index, 'name', e.target.value)}
          placeholder="输入产品型号"
        />
      ),
    },
    ...timeLabels.map((label, timeIndex) => ({
      title: label,
      key: `time-${timeIndex}`,
      children: [
        {
          title: '均值',
          dataIndex: 'means',
          key: `mean-${timeIndex}`,
          render: (_: number[], record: ProductData, index: number) => (
            <InputNumber
              value={record.means[timeIndex]}
              onChange={(val) => {
                const newMeans = [...record.means]
                newMeans[timeIndex] = val || 0
                updateProduct(index, 'means', newMeans)
              }}
              style={{ width: '100%' }}
            />
          ),
        },
        {
          title: '标准差',
          dataIndex: 'stds',
          key: `std-${timeIndex}`,
          render: (_: number[], record: ProductData, index: number) => (
            <InputNumber
              value={record.stds[timeIndex]}
              onChange={(val) => {
                const newStds = [...record.stds]
                newStds[timeIndex] = val || 0
                updateProduct(index, 'stds', newStds)
              }}
              style={{ width: '100%' }}
            />
          ),
        },
      ],
    })),
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, __: ProductData, index: number) => (
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          onClick={() => removeProduct(index)}
          disabled={products.length <= 1}
        />
      ),
    },
  ]

  // Flatten columns for nested structure
  const flattenedColumns = columns.flatMap((col) =>
    col.children ? [col, ...col.children] : [col]
  )

  return (
    <div>
      <Card title="变化率作图" style={{ marginBottom: 24 }}>
        <Paragraph type="secondary">
          输入各产品在不同时间点的参数均值和标准差，自动生成趋势图并计算变化率。
          支持 VF (正向电压)、BV (反向击穿电压)、IR (反向漏电流) 三种参数类型。
        </Paragraph>

        <Divider />

        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Button type="dashed" onClick={addProduct} icon={<PlusOutlined />}>
            添加产品
          </Button>

          <Table
            dataSource={products}
            columns={flattenedColumns as any}
            pagination={false}
            size="small"
            rowKey={(_, index) => `product-${index}`}
          />
        </Space>
      </Card>

      <Card title="生成图表" style={{ marginBottom: 24 }}>
        <Space size="large">
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => handleGenerate('VF')}
            loading={loading && chartType === 'VF'}
          >
            生成VF趋势图
          </Button>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => handleGenerate('BV')}
            loading={loading && chartType === 'BV'}
            style={{ background: '#52c41a', borderColor: '#52c41a' }}
          >
            生成BV趋势图
          </Button>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => handleGenerate('IR')}
            loading={loading && chartType === 'IR'}
            style={{ background: '#722ed1', borderColor: '#722ed1' }}
          >
            生成IR趋势图
          </Button>
        </Space>
      </Card>

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

// InputNumber component
function InputNumber({ value, onChange, style }: { value: number; onChange: (val: number | null) => void; style?: React.CSSProperties }) {
  return (
    <Input
      type="number"
      value={value}
      onChange={(e) => onChange(parseFloat(e.target.value) || null)}
      style={style}
    />
  )
}
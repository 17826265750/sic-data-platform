import { useState, useCallback } from 'react'
import { Card, Form, Button, Space, Input, Select, Typography, Divider, message, Table, InputNumber } from 'antd'
import { PlayCircleOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import JobProgress from '../components/common/JobProgress'
import { trendChartApi, jobsApi } from '../api'
import { useJobPolling } from '../hooks/useJobPolling'
import type { JobInfo } from '../api/types'

const { Title, Paragraph, Text } = Typography

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
  const [chartType, setChartType] = useState<'VF' | 'BV' | 'IR'>('VF')

  const timeLabels = ['初始值(T0)', '168小时', '500小时', '1000小时']

  // Use custom hook for job polling - prevents memory leaks
  const { job, isPolling, startPolling } = useJobPolling({
    onComplete: () => message.success('趋势图生成完成！'),
    onError: (error) => message.error(`生成失败: ${error}`),
  })

  const addProduct = useCallback(() => {
    setProducts((prev) => [
      ...prev,
      { name: '', means: [0, 0, 0, 0], stds: [0, 0, 0, 0] },
    ])
  }, [])

  const removeProduct = useCallback((index: number) => {
    setProducts((prev) => {
      if (prev.length <= 1) return prev
      return prev.filter((_, i) => i !== index)
    })
  }, [])

  const updateProduct = useCallback((
    index: number,
    field: 'name' | 'means' | 'stds',
    value: string | number[]
  ) => {
    setProducts((prev) => {
      const newProducts = [...prev]
      if (field === 'name') {
        newProducts[index].name = value as string
      } else {
        newProducts[index][field] = value as number[]
      }
      return newProducts
    })
  }, [])

  const handleGenerate = useCallback(async (type: 'VF' | 'BV' | 'IR') => {
    // 验证数据
    const validProducts = products.filter((p) => p.name.trim() !== '')
    if (validProducts.length === 0) {
      message.warning('请至少添加一个产品')
      return
    }

    setChartType(type)

    try {
      const means: Record<string, number[]> = {}
      const stds: Record<string, number[]> = {}

      validProducts.forEach((p) => {
        means[p.name] = p.means
        stds[p.name] = p.stds
      })

      const apiMethod = type === 'VF' ? trendChartApi.generateVF
        : type === 'BV' ? trendChartApi.generateBV
        : trendChartApi.generateIR

      const response = await apiMethod({
        chart_type: type,
        product_list: validProducts.map((p) => p.name),
        time_labels: timeLabels,
        means,
        stds,
      })

      startPolling(response.data.job_id)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '启动任务失败'
      message.error(errorMessage)
    }
  }, [products, timeLabels, startPolling])

  const handleDownload = useCallback(() => {
    if (job) {
      window.open(jobsApi.downloadResult(job.job_id), '_blank')
    }
  }, [job])

  const columns = [
    {
      title: '产品型号',
      dataIndex: 'name',
      key: 'name',
      width: 150,
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
          width: 100,
          render: (_: number[], record: ProductData, index: number) => (
            <InputNumber
              value={record.means[timeIndex]}
              onChange={(val) => {
                const newMeans = [...record.means]
                newMeans[timeIndex] = val || 0
                updateProduct(index, 'means', newMeans)
              }}
              style={{ width: '100%' }}
              step={chartType === 'VF' ? 0.001 : 0.1}
              precision={chartType === 'VF' ? 3 : 1}
            />
          ),
        },
        {
          title: '标准差',
          dataIndex: 'stds',
          key: `std-${timeIndex}`,
          width: 100,
          render: (_: number[], record: ProductData, index: number) => (
            <InputNumber
              value={record.stds[timeIndex]}
              onChange={(val) => {
                const newStds = [...record.stds]
                newStds[timeIndex] = val || 0
                updateProduct(index, 'stds', newStds)
              }}
              style={{ width: '100%' }}
              step={0.001}
              precision={3}
              min={0}
            />
          ),
        },
      ],
    })),
    {
      title: '操作',
      key: 'action',
      width: 60,
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
            scroll={{ x: 'max-content' }}
          />
        </Space>
      </Card>

      <Card title="生成图表" style={{ marginBottom: 24 }}>
        <Space size="large">
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => handleGenerate('VF')}
            loading={isPolling && chartType === 'VF'}
            disabled={isPolling}
          >
            生成VF趋势图
          </Button>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => handleGenerate('BV')}
            loading={isPolling && chartType === 'BV'}
            disabled={isPolling}
            style={{ background: '#52c41a', borderColor: '#52c41a' }}
          >
            生成BV趋势图
          </Button>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => handleGenerate('IR')}
            loading={isPolling && chartType === 'IR'}
            disabled={isPolling}
            style={{ background: '#722ed1', borderColor: '#722ed1' }}
          >
            生成IR趋势图
          </Button>
        </Space>
      </Card>

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
import { Row, Col, Card, Typography, Statistic } from 'antd'
import {
  FileSearchOutlined,
  LineChartOutlined,
  AreaChartOutlined,
  BarChartOutlined,
  FileTextOutlined,
  RocketOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title, Paragraph } = Typography

const features = [
  {
    key: 'parameter-check',
    title: '参数检查数据处理',
    description: 'Excel模板数据合并与智能匹配，自动填充VF/IR/BVR参数数据',
    icon: <FileSearchOutlined style={{ fontSize: 40, color: '#1677ff' }} />,
    path: '/parameter-check',
  },
  {
    key: 'trend-chart',
    title: '变化率作图',
    description: 'VF/BV/IR参数趋势图生成，自动计算变化率并标注',
    icon: <LineChartOutlined style={{ fontSize: 40, color: '#52c41a' }} />,
    path: '/trend-chart',
  },
  {
    key: 'stress-curve',
    title: '应力数据曲线',
    description: '漏电流趋势可视化，支持80通道数据，可选平滑处理',
    icon: <AreaChartOutlined style={{ fontSize: 40, color: '#faad14' }} />,
    path: '/stress-curve',
  },
  {
    key: 'normal-dist',
    title: '正态分布分析',
    description: '统计分析与正态分布图，支持3-sigma异常值处理',
    icon: <BarChartOutlined style={{ fontSize: 40, color: '#722ed1' }} />,
    path: '/normal-dist',
  },
  {
    key: 'report-gen',
    title: '测试报告生成',
    description: 'Word报告自动生成，支持HTRB/H3TRB/HTGB/TC等多种测试类型',
    icon: <FileTextOutlined style={{ fontSize: 40, color: '#eb2f96' }} />,
    path: '/report-gen',
  },
]

export default function Home() {
  const navigate = useNavigate()

  return (
    <div>
      <div style={{ marginBottom: 32, textAlign: 'center' }}>
        <Title level={2}>
          <RocketOutlined style={{ marginRight: 8 }} />
          SiC数据处理平台
        </Title>
        <Paragraph type="secondary" style={{ fontSize: 16 }}>
          碳化硅JBS二极管试验数据一体化处理平台
        </Paragraph>
      </div>

      <Row gutter={[24, 24]}>
        {features.map((feature) => (
          <Col xs={24} sm={12} lg={8} key={feature.key}>
            <Card
              hoverable
              style={{ height: '100%' }}
              onClick={() => navigate(feature.path)}
            >
              <div style={{ textAlign: 'center', marginBottom: 16 }}>
                {feature.icon}
              </div>
              <Title level={4} style={{ textAlign: 'center', marginBottom: 8 }}>
                {feature.title}
              </Title>
              <Paragraph
                type="secondary"
                style={{ textAlign: 'center', marginBottom: 0 }}
              >
                {feature.description}
              </Paragraph>
            </Card>
          </Col>
        ))}
      </Row>

      <Card style={{ marginTop: 32 }}>
        <Row gutter={24}>
          <Col span={6}>
            <Statistic
              title="处理模块"
              value={5}
              suffix="个"
              valueStyle={{ color: '#1677ff' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="支持格式"
              value="Excel, Word"
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="异步处理"
              value="支持"
              valueStyle={{ color: '#faad14' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="中文支持"
              value="完整"
              valueStyle={{ color: '#722ed1' }}
            />
          </Col>
        </Row>
      </Card>
    </div>
  )
}
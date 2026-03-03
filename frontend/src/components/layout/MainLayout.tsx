import { ReactNode } from 'react'
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  FileSearchOutlined,
  LineChartOutlined,
  AreaChartOutlined,
  BarChartOutlined,
  FileTextOutlined,
  HistoryOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'

const { Sider, Content, Header } = Layout

interface MainLayoutProps {
  children: ReactNode
}

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: '首页',
  },
  {
    key: '/parameter-check',
    icon: <FileSearchOutlined />,
    label: '参数检查',
  },
  {
    key: '/trend-chart',
    icon: <LineChartOutlined />,
    label: '变化率作图',
  },
  {
    key: '/stress-curve',
    icon: <AreaChartOutlined />,
    label: '应力曲线',
  },
  {
    key: '/normal-dist',
    icon: <BarChartOutlined />,
    label: '正态分布',
  },
  {
    key: '/report-gen',
    icon: <FileTextOutlined />,
    label: '报告生成',
  },
  {
    key: '/job-history',
    icon: <HistoryOutlined />,
    label: '任务历史',
  },
]

export default function MainLayout({ children }: MainLayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        width={220}
        style={{
          background: '#001529',
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: 18,
            fontWeight: 'bold',
            borderBottom: '1px solid #002140',
          }}
        >
          SiC数据处理平台
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <h2 style={{ margin: 0, fontSize: 18 }}>
            {menuItems.find((item) => item.key === location.pathname)?.label || 'SiC数据处理平台'}
          </h2>
        </Header>
        <Content
          style={{
            margin: 24,
            padding: 24,
            background: '#fff',
            borderRadius: 8,
            minHeight: 280,
            overflow: 'auto',
          }}
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import MainLayout from './components/layout/MainLayout'
import Home from './views/Home'
import ParameterCheck from './views/ParameterCheck'
import TrendChart from './views/TrendChart'
import StressCurve from './views/StressCurve'
import NormalDistribution from './views/NormalDistribution'
import ReportGeneration from './views/ReportGeneration'
import JobHistory from './views/JobHistory'

function App() {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/parameter-check" element={<ParameterCheck />} />
          <Route path="/trend-chart" element={<TrendChart />} />
          <Route path="/stress-curve" element={<StressCurve />} />
          <Route path="/normal-dist" element={<NormalDistribution />} />
          <Route path="/report-gen" element={<ReportGeneration />} />
          <Route path="/job-history" element={<JobHistory />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  )
}

export default App
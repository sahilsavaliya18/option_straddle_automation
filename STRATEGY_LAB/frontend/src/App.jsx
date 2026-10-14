import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ErrorBoundary from './components/ErrorBoundary';
import Dashboard from './pages/Dashboard';
import Strategies from './pages/Strategies';
import RunBacktest from './pages/RunBacktest';
import Results from './pages/Results';
import Compare from './pages/Compare';
import DataStatus from './pages/DataStatus';

export default function App() {
  return (
    <div className="app-layout">
      <Sidebar />
      <header className="topbar">
        <div style={{ flex: 1 }} />
        <div style={{
          display: 'flex', alignItems: 'center', gap: 'var(--sp-3)',
          fontSize: 'var(--text-sm)', color: 'var(--text-tertiary)'
        }}>
          <span className="status-dot green" />
          NIFTY Options Lab
        </div>
      </header>
      <main className="main-content">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/strategies" element={<Strategies />} />
            <Route path="/run" element={<RunBacktest />} />
            <Route path="/results" element={<Results />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="/data-status" element={<DataStatus />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  );
}

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import ParticleBackground from './components/ParticleBackground';
import './App.css';

export default function App() {
  return (
    <Router>
      {/* 3D Particle Mesh Background */}
      <ParticleBackground />

      <main style={{ position: 'relative', zIndex: 1, minHeight: '100dvh' }}>
        <Routes>
          {/* Public Application Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard/:filename" element={<DashboardPage />} />

          {/* Fallback redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </Router>
  );
}

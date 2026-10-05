import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/layout/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Jobs from './pages/Jobs';
import JobDetails from './pages/JobDetails';
import Candidates from './pages/Candidates';
import CandidateProfile from './pages/CandidateProfile';
import JobMatches from './pages/JobMatches';
import Pipeline from './pages/Pipeline';
import Interviews from './pages/Interviews';
import Followups from './pages/Followups';
import Analytics from './pages/Analytics';
import AIAssistant from './pages/AIAssistant';
import CandidateComparison from './pages/CandidateComparison';
import UsersPage from './pages/Users';

// Placeholder view for features being implemented in upcoming phases
const UpcomingPhasePlaceholder: React.FC<{ title: string; phase: string }> = ({ title, phase }) => (
  <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-12 text-center space-y-4">
    <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400 flex items-center justify-center mx-auto">
      <span className="font-bold text-lg">{phase}</span>
    </div>
    <h2 className="text-xl font-bold text-white">{title}</h2>
    <p className="text-xs text-slate-400 max-w-md mx-auto">
      This module is scheduled for implementation in {phase}. Backend API models and database structures are primed and active.
    </p>
  </div>
);

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Auth Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Application Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="jobs" element={<Jobs />} />
            <Route path="jobs/:id" element={<JobDetails />} />
            <Route path="jobs/:id/matches" element={<JobMatches />} />
            <Route path="candidates" element={<Candidates />} />
            <Route path="candidates/:id" element={<CandidateProfile />} />
            <Route path="pipeline" element={<Pipeline />} />
            <Route path="compare" element={<CandidateComparison />} />
            <Route path="interviews" element={<Interviews />} />
            <Route path="followups" element={<Followups />} />
            <Route path="ai-assistant" element={<AIAssistant />} />
            <Route path="analytics" element={<Analytics />} />
            
            {/* Admin Exclusive Route */}
            <Route
              path="users"
              element={
                <ProtectedRoute requiredRole="ADMIN">
                  <UsersPage />
                </ProtectedRoute>
              }
            />
          </Route>

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;

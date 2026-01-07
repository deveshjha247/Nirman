import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute, AdminRoute } from './components/ProtectedRoute';
import CookieConsent from './components/CookieConsent';
import './App.css';

// Page imports
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Builder from './pages/Builder';
import Build from './pages/Build';
import Wallet from './pages/Wallet';
import Plans from './pages/Plans';
import Referrals from './pages/Referrals';
import AIKeys from './pages/AIKeys';
import Admin from './pages/Admin';
import ManageCookies from './pages/ManageCookies';
import Terms from './pages/Terms';
import Privacy from './pages/Privacy';
import About from './pages/About';
import Careers from './pages/Careers';
import Download from './pages/Download';
import Settings from './pages/Settings';
import Integrations from './pages/Integrations';
import Agent from './pages/Agent';
import AgentChat from './pages/AgentChat';
import LLMKeys from './pages/LLMKeys';
import Docs from './pages/Docs';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <CookieConsent />
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/cookies" element={<ManageCookies />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/about" element={<About />} />
          <Route path="/careers" element={<Careers />} />
          <Route path="/download" element={<Download />} />
          
          {/* Protected Routes - Require Authentication */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/builder/:projectId" element={
            <ProtectedRoute>
              <Builder />
            </ProtectedRoute>
          } />
          <Route path="/build/:projectId" element={
            <ProtectedRoute>
              <Build />
            </ProtectedRoute>
          } />
          <Route path="/wallet" element={
            <ProtectedRoute>
              <Wallet />
            </ProtectedRoute>
          } />
          <Route path="/plans" element={
            <ProtectedRoute>
              <Plans />
            </ProtectedRoute>
          } />
          <Route path="/referrals" element={
            <ProtectedRoute>
              <Referrals />
            </ProtectedRoute>
          } />
          <Route path="/ai-keys" element={
            <ProtectedRoute>
              <AIKeys />
            </ProtectedRoute>
          } />
          <Route path="/settings" element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          } />
          <Route path="/integrations" element={
            <ProtectedRoute>
              <Integrations />
            </ProtectedRoute>
          } />
          <Route path="/agent" element={
            <ProtectedRoute>
              <Agent />
            </ProtectedRoute>
          } />
          <Route path="/chat" element={
            <ProtectedRoute>
              <AgentChat />
            </ProtectedRoute>
          } />
          
          {/* Admin Route - Require Admin Role */}
          <Route path="/admin" element={
            <AdminRoute>
              <Admin />
            </AdminRoute>
          } />
          
          {/* Catch all - redirect to landing */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProcessProvider } from './contexts/ProcessContext';
import Header from './components/common/Header';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import GuidelinesList from './components/guidelines/GuidelinesList';
import GuidelineDetail from './components/guidelines/GuidelineDetail';
import GuidelineForm from './components/guidelines/GuidelineForm';
import AdminDashboard from './components/admin/AdminDashboard';
import AdminUsers from './components/admin/AdminUsers';
import AdminDocuments from './components/admin/AdminDocuments';
import NotFound from './components/common/NotFound';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AdminRoute from './components/auth/AdminRoute';
import ProgressModal from './components/common/ProgressModal';
import DocumentSearch from './components/documents/DocumentSearch';

function App() {
  return (
    <AuthProvider>
      <ProcessProvider>
        <div className="min-h-screen bg-gray-100">
          <Header />
          <main className="container mx-auto px-4 py-8">
            <Routes>
            <Route path="/" element={<Navigate to="/guidelines" replace />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            <Route 
              path="/guidelines" 
              element={
                <ProtectedRoute>
                  <GuidelinesList />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/guidelines/:id" 
              element={
                <ProtectedRoute>
                  <GuidelineDetail />
                </ProtectedRoute>
              } 
            />
            
            <Route 
              path="/guidelines/new" 
              element={
                <AdminRoute>
                  <GuidelineForm />
                </AdminRoute>
              } 
            />
            
            <Route 
              path="/guidelines/edit/:id" 
              element={
                <AdminRoute>
                  <GuidelineForm />
                </AdminRoute>
              } 
            />
            
            <Route 
              path="/admin" 
              element={
                <AdminRoute>
                  <AdminDashboard />
                </AdminRoute>
              } 
            />
            
            <Route 
              path="/admin/users" 
              element={
                <AdminRoute>
                  <AdminUsers />
                </AdminRoute>
              } 
            />
            
            <Route 
              path="/admin/documents" 
              element={
                <AdminRoute>
                  <AdminDocuments />
                </AdminRoute>
              } 
            />
            
            <Route 
              path="/documents/search" 
              element={
                <ProtectedRoute>
                  <DocumentSearch />
                </ProtectedRoute>
              } 
            />
            
            <Route path="*" element={<NotFound />} />
          </Routes>
          <ProgressModal />
        </main>
      </div>
      </ProcessProvider>
    </AuthProvider>
  );
}

export default App;

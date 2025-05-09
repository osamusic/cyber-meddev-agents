import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axiosClient from '../../api/axiosClient';
import CrawlerForm from './CrawlerForm';
import ClassificationForm from './ClassificationForm';

const AdminDashboard = () => {
  const [stats, setStats] = useState({
    totalDocuments: 0,
    totalUsers: 0,
    totalGuidelines: 0,
    indexStats: {
      total_documents: 0,
      total_chunks: 0,
      last_updated: null
    }
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCrawlerForm, setShowCrawlerForm] = useState(false);
  const [showClassificationForm, setShowClassificationForm] = useState(false);
  const [updatingIndex, setUpdatingIndex] = useState(false);
  const [indexUpdateMessage, setIndexUpdateMessage] = useState(null);

  const handleUpdateIndex = async () => {
    try {
      setUpdatingIndex(true);
      setIndexUpdateMessage({
        type: 'info',
        text: 'インデックスを更新中...'
      });
      
      const response = await axiosClient.post('/index/documents');
      
      setIndexUpdateMessage({
        type: 'success',
        text: response.data.message || 'インデックスが正常に更新されました'
      });
      
      await fetchStats();
      
    } catch (err) {
      console.error('Error updating index:', err);
      setIndexUpdateMessage({
        type: 'error',
        text: err.response?.data?.detail || 'インデックスの更新中にエラーが発生しました'
      });
    } finally {
      setUpdatingIndex(false);
      
      setTimeout(() => {
        setIndexUpdateMessage(null);
      }, 5000);
    }
  };

  const fetchStats = async () => {
    try {
      setLoading(true);
      
      const [usersRes, guidelinesRes, indexStatsRes] = await Promise.all([
        axiosClient.get('/admin/users'),
        axiosClient.get('/guidelines'),
        axiosClient.get('/index/stats')
      ]);
      
      setStats({
        totalUsers: usersRes.data.length,
        totalGuidelines: guidelinesRes.data.length,
        totalDocuments: indexStatsRes.data.total_documents,
        indexStats: indexStatsRes.data
      });
    } catch (err) {
      console.error('Error fetching stats:', err);
      setError('統計情報の取得中にエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">管理者ダッシュボード</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-lg font-semibold mb-2">ユーザー</h2>
          <p className="text-3xl font-bold text-blue-600">{stats.totalUsers}</p>
          <Link 
            to="/admin/users" 
            className="text-blue-600 hover:underline mt-4 inline-block"
          >
            ユーザー管理 →
          </Link>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-lg font-semibold mb-2">ガイドライン</h2>
          <p className="text-3xl font-bold text-blue-600">{stats.totalGuidelines}</p>
          <Link 
            to="/guidelines" 
            className="text-blue-600 hover:underline mt-4 inline-block"
          >
            ガイドライン一覧 →
          </Link>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-lg font-semibold mb-2">ドキュメント</h2>
          <p className="text-3xl font-bold text-blue-600">{stats.totalDocuments}</p>
          <Link 
            to="/admin/documents" 
            className="text-blue-600 hover:underline mt-4 inline-block"
          >
            ドキュメント管理 →
          </Link>
        </div>
      </div>
      
      {/* Index stats */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-lg font-semibold mb-4">インデックス情報</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <h3 className="font-medium text-gray-500">総ドキュメント数</h3>
            <p className="text-xl font-semibold">{stats.indexStats.total_documents}</p>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-500">総チャンク数</h3>
            <p className="text-xl font-semibold">{stats.indexStats.total_chunks}</p>
          </div>
          
          <div>
            <h3 className="font-medium text-gray-500">最終更新日時</h3>
            <p className="text-xl font-semibold">
              {stats.indexStats.last_updated 
                ? new Date(stats.indexStats.last_updated).toLocaleString('ja-JP')
                : '更新なし'}
            </p>
          </div>
        </div>
      </div>
      
      {/* Quick actions */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-lg font-semibold mb-4">クイックアクション</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button 
            className={`bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded ${
              updatingIndex ? 'opacity-75 cursor-not-allowed' : ''
            }`}
            onClick={handleUpdateIndex}
            disabled={updatingIndex}
          >
            {updatingIndex ? 'インデックス更新中...' : 'インデックスを更新'}
          </button>
          
          <button 
            className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded"
            onClick={() => setShowCrawlerForm(!showCrawlerForm)}
          >
            {showCrawlerForm ? 'フォームを閉じる' : 'クローラーを実行'}
          </button>
          
          <button 
            className="bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded"
            onClick={() => setShowClassificationForm(!showClassificationForm)}
          >
            {showClassificationForm ? 'フォームを閉じる' : 'ドキュメント分類'}
          </button>
        </div>
      </div>

      {indexUpdateMessage && (
        <div className={`mt-4 px-4 py-3 rounded ${
          indexUpdateMessage.type === 'success' 
            ? 'bg-green-100 border border-green-400 text-green-700' 
            : indexUpdateMessage.type === 'error'
              ? 'bg-red-100 border border-red-400 text-red-700'
              : 'bg-blue-100 border border-blue-400 text-blue-700'
        }`}>
          {indexUpdateMessage.text}
        </div>
      )}

      {showCrawlerForm && (
        <CrawlerForm 
          onCrawlComplete={(data) => {
            fetchStats();
            setShowCrawlerForm(false);
          }} 
        />
      )}
      
      {showClassificationForm && (
        <ClassificationForm 
          onClassifyComplete={(data) => {
            fetchStats();
            setShowClassificationForm(false);
          }} 
        />
      )}
    </div>
  );
};

export default AdminDashboard;

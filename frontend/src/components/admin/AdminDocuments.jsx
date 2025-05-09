import React, { useState, useEffect } from 'react';
import axiosClient from '../../api/axiosClient';

const AdminDocuments = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteConfirmation, setDeleteConfirmation] = useState(null);
  const [actionInProgress, setActionInProgress] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await axiosClient.get('/admin/documents');
      setDocuments(response.data);
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError('ドキュメント情報の取得中にエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  const confirmDelete = (docId) => {
    setDeleteConfirmation(docId);
  };

  const cancelDelete = () => {
    setDeleteConfirmation(null);
  };

  const deleteDocument = async (docId) => {
    try {
      setActionInProgress(true);
      await axiosClient.delete(`/admin/documents/${docId}`, {
        data: { confirmed: true }
      });
      
      await fetchDocuments();
      
      setDeleteConfirmation(null);
      
    } catch (err) {
      console.error('Error deleting document:', err);
      setError('ドキュメントの削除中にエラーが発生しました');
    } finally {
      setActionInProgress(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('ja-JP');
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">ドキュメント管理</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                タイトル
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ソース
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ダウンロード日時
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                アクション
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {documents.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                  ドキュメントが見つかりません
                </td>
              </tr>
            ) : (
              documents.map((doc) => (
                <tr key={doc.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {doc.doc_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {doc.title}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <a 
                      href={doc.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      {doc.source_type}
                    </a>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(doc.downloaded_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {deleteConfirmation === doc.doc_id ? (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => deleteDocument(doc.doc_id)}
                          disabled={actionInProgress}
                          className={`text-red-600 hover:text-red-900 ${
                            actionInProgress ? 'opacity-50 cursor-not-allowed' : ''
                          }`}
                        >
                          確認
                        </button>
                        <button
                          onClick={cancelDelete}
                          disabled={actionInProgress}
                          className="text-gray-600 hover:text-gray-900"
                        >
                          キャンセル
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => confirmDelete(doc.doc_id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        削除
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminDocuments;

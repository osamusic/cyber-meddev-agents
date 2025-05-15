import React, { useState, useEffect } from 'react';
import axiosClient from '../../api/axiosClient';
import { FaChevronDown, FaChevronRight } from 'react-icons/fa';

const AdminDocuments = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteConfirmation, setDeleteConfirmation] = useState(null);
  const [groupDeleteConfirmation, setGroupDeleteConfirmation] = useState(null);
  const [actionInProgress, setActionInProgress] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState({});

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
      await axiosClient.delete(`/admin/documents/${docId}`, { data: { confirmed: true } });
      await fetchDocuments();
      setDeleteConfirmation(null);
    } catch (err) {
      console.error('Error deleting document:', err);
      setError('ドキュメントの削除中にエラーが発生しました');
    } finally {
      setActionInProgress(false);
    }
  };

  const confirmDeleteGroup = (groupTitle) => {
    setGroupDeleteConfirmation(groupTitle);
  };

  const cancelDeleteGroup = () => {
    setGroupDeleteConfirmation(null);
  };

  const deleteGroup = async (groupTitle) => {
    try {
      setActionInProgress(true);
      const groups = groupDocumentsByOriginalTitle();
      const docsToDelete = groups[groupTitle] || [];
      await Promise.all(
        docsToDelete.map(doc =>
          axiosClient.delete(`/admin/documents/${doc.doc_id}`, { data: { confirmed: true } })
        )
      );
      await fetchDocuments();
      setGroupDeleteConfirmation(null);
    } catch (err) {
      console.error('Error deleting group:', err);
      setError('ドキュメントのグループ削除中にエラーが発生しました');
    } finally {
      setActionInProgress(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('ja-JP');
  };

  const toggleGroup = (groupTitle) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupTitle]: !prev[groupTitle]
    }));
  };

  const groupDocumentsByOriginalTitle = () => {
    const groups = {};
    documents.forEach(doc => {
      const groupTitle = doc.original_title || doc.title;
      if (!groups[groupTitle]) {
        groups[groupTitle] = [];
      }
      groups[groupTitle].push(doc);
    });
    return groups;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const documentGroups = groupDocumentsByOriginalTitle();

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">ドキュメント管理</h1>
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        {Object.keys(documentGroups).length === 0 ? (
          <div className="px-6 py-4 text-center text-gray-500">
            ドキュメントが見つかりません
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {Object.entries(documentGroups).map(([groupTitle, docs]) => (
              <div key={groupTitle} className="border-b border-gray-200 last:border-b-0">
                <div
                  className="px-6 py-4 bg-gray-50 flex items-center justify-between cursor-pointer"
                  onClick={() => toggleGroup(groupTitle)}
                >
                  <div className="flex items-center">
                    <div className="mr-2">
                      {expandedGroups[groupTitle] ? <FaChevronDown /> : <FaChevronRight />}
                    </div>
                    <h3 className="text-lg font-medium text-gray-900">{groupTitle}</h3>
                    <span className="ml-2 text-sm text-gray-500">({docs.length}件)</span>
                  </div>
                  <div className="flex items-center">
                    {docs.length > 0 && (
                      <>
                        <span className="text-sm text-gray-500 mr-4">
                          ソース:
                          <a
                            href={docs[0].url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="ml-1 text-blue-600 hover:underline"
                            onClick={e => e.stopPropagation()}
                          >
                            {docs[0].source_type}
                          </a>
                        </span>
                        <span className="text-sm text-gray-500 mr-4">
                          ダウンロード日時: {formatDate(docs[0].downloaded_at)}
                        </span>
                      </>
                    )}
                    {groupDeleteConfirmation === groupTitle ? (
                      <div className="flex space-x-2" onClick={e => e.stopPropagation()}>
                        <button
                          onClick={() => deleteGroup(groupTitle)}
                          disabled={actionInProgress}
                          className={`text-red-600 hover:text-red-900 ${
                            actionInProgress ? 'opacity-50 cursor-not-allowed' : ''
                          }`}
                        >
                          確認
                        </button>
                        <button
                          onClick={cancelDeleteGroup}
                          disabled={actionInProgress}
                          className="text-gray-600 hover:text-gray-900"
                        >
                          キャンセル
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={e => { e.stopPropagation(); confirmDeleteGroup(groupTitle); }}
                        className="text-red-600 hover:text-red-900 mr-4"
                      >
                        削除
                      </button>
                    )}
                  </div>
                </div>
                {expandedGroups[groupTitle] && (
                  <div className="overflow-x-auto">
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
                            アクション
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {docs.map((doc) => (
                          <tr key={doc.id || doc.doc_id}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {doc.doc_id}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              {doc.title}
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
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDocuments;

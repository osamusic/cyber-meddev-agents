import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import axiosClient from '../../api/axiosClient';
import { FaSpinner } from 'react-icons/fa';

const ClassificationForm = ({ onClassifyComplete }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [classifyAll, setClassifyAll] = useState(false);
  const [success, setSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);
  const [progressStatus, setProgressStatus] = useState('');
  
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await axiosClient.get('/admin/documents');
        setDocuments(response.data);
      } catch (err) {
        console.error('Error fetching documents:', err);
        setError('ドキュメントの取得中にエラーが発生しました');
      }
    };
    
    fetchDocuments();
  }, []);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(false);
      setProgressStatus('ドキュメントの分類を開始しています...');
      
      const requestData = {
        all_documents: classifyAll,
        document_ids: classifyAll ? [] : selectedDocuments,
      };
      
      setProgressStatus('ドキュメントを処理中...');
      
      const response = await axiosClient.post('/classifier/classify', requestData);
      
      setProgressStatus('分類処理が完了しました');
      setSuccess(true);
      setSuccessMessage(response.data.message);
      if (onClassifyComplete) {
        onClassifyComplete(response.data);
      }
      
    } catch (err) {
      console.error('Error classifying documents:', err);
      setProgressStatus('エラーが発生しました');
      setError(err.response?.data?.detail || '分類処理中にエラーが発生しました');
    } finally {
      setTimeout(() => {
        setLoading(false);
        setProgressStatus('');
      }, 1000); // 1秒後にローディング状態をクリア（進捗表示を確認できるようにするため）
    }
  };
  
  const handleDocumentSelect = (e, docId) => {
    if (e.target.checked) {
      setSelectedDocuments(prev => [...prev, docId]);
    } else {
      setSelectedDocuments(prev => prev.filter(id => id !== docId));
    }
  };
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-md mt-4">
      <h2 className="text-lg font-semibold mb-4">ドキュメント分類</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          分類処理が開始されました。結果は数分後に反映されます。
          {successMessage && <p className="mt-2">{successMessage}</p>}
        </div>
      )}
      
      {loading && (
        <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4 flex items-center">
          <FaSpinner className="animate-spin mr-2 text-xl" />
          <div>
            <p className="font-medium">分類処理実行中...</p>
            <p className="text-sm">{progressStatus}</p>
          </div>
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="flex items-center mb-2">
            <input
              type="checkbox"
              checked={classifyAll}
              onChange={(e) => setClassifyAll(e.target.checked)}
              className="mr-2"
            />
            <span className="font-medium">すべてのドキュメントを分類</span>
          </label>
        </div>
        
        {!classifyAll && (
          <div className="mb-4">
            <h3 className="font-medium mb-2">分類するドキュメントを選択:</h3>
            <div className="max-h-60 overflow-y-auto border rounded p-2">
              {documents.length === 0 ? (
                <p className="text-gray-500">ドキュメントがありません</p>
              ) : (
                documents.map(doc => (
                  <label key={doc.id} className={`flex items-center mb-2 ${doc.is_classified ? 'text-gray-400' : ''}`}>
                    <input
                      type="checkbox"
                      onChange={(e) => handleDocumentSelect(e, doc.id)}
                      checked={selectedDocuments.includes(doc.id)}
                      disabled={doc.is_classified}
                      className="mr-2"
                    />
                    <span>{doc.title || doc.url}</span>
                    {doc.is_classified && <span className="ml-2 text-sm text-gray-500">（分類済み）</span>}
                  </label>
                ))
              )}
            </div>
          </div>
        )}
        
        <button
          type="submit"
          disabled={loading || (!classifyAll && selectedDocuments.length === 0)}
          className={`w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded flex items-center justify-center ${
            loading || (!classifyAll && selectedDocuments.length === 0)
              ? 'opacity-50 cursor-not-allowed'
              : ''
          }`}
        >
          {loading ? (
            <>
              <FaSpinner className="animate-spin mr-2" />
              処理中...
            </>
          ) : (
            '分類を開始'
          )}
        </button>
      </form>
    </div>
  );
};

ClassificationForm.propTypes = {
  onClassifyComplete: PropTypes.func
};

export default ClassificationForm;

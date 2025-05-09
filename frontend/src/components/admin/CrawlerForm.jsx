import React, { useState } from 'react';
import axiosClient from '../../api/axiosClient';

const CrawlerForm = ({ onCrawlComplete }) => {
  const [url, setUrl] = useState('');
  const [depth, setDepth] = useState(2);
  const [mimeTypes, setMimeTypes] = useState(['application/pdf', 'text/html']);
  const [updateExisting, setUpdateExisting] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');

  const handleMimeTypeChange = (type) => {
    if (mimeTypes.includes(type)) {
      setMimeTypes(mimeTypes.filter(t => t !== type));
    } else {
      setMimeTypes([...mimeTypes, type]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setStatusMessage('');
    
    if (!url) {
      setError('URLを入力してください');
      return;
    }
    
    try {
      setIsSubmitting(true);
      setStatusMessage('クローラーを実行中...');
      
      const response = await axiosClient.post('/crawler/run', {
        url,
        depth: parseInt(depth),
        mime_filters: mimeTypes,
        name: `Crawl of ${url}`,
        update_existing: updateExisting
      });
      
      setStatusMessage('クローラーが開始されました。処理が完了するまでしばらくお待ちください。');
      
      setTimeout(async () => {
        try {
          const statusRes = await axiosClient.get('/crawler/status');
          if (onCrawlComplete) {
            onCrawlComplete(statusRes.data);
          }
        } catch (err) {
          console.error('Error checking crawler status:', err);
        } finally {
          setIsSubmitting(false);
        }
      }, 5000);
      
    } catch (err) {
      console.error('Error running crawler:', err);
      setError(err.response?.data?.detail || 'クローラーの実行中にエラーが発生しました');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-lg font-semibold mb-4">クローラーの実行</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {statusMessage && (
        <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4">
          {statusMessage}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="url" className="block text-gray-700 font-medium mb-2">
            クロール対象URL
          </label>
          <input
            type="url"
            id="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="https://example.com"
            required
          />
        </div>
        
        <div className="mb-4">
          <label htmlFor="depth" className="block text-gray-700 font-medium mb-2">
            クロール深度
          </label>
          <select
            id="depth"
            value={depth}
            onChange={(e) => setDepth(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="1">1 - 最初のページのみ</option>
            <option value="2">2 - リンク1階層まで</option>
            <option value="3">3 - リンク2階層まで</option>
            <option value="4">4 - リンク3階層まで</option>
            <option value="5">5 - リンク4階層まで</option>
          </select>
        </div>
        
        <div className="mb-4">
          <span className="block text-gray-700 font-medium mb-2">
            ファイルタイプ
          </span>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={mimeTypes.includes('application/pdf')}
                onChange={() => handleMimeTypeChange('application/pdf')}
                className="mr-2"
              />
              PDF
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={mimeTypes.includes('text/html')}
                onChange={() => handleMimeTypeChange('text/html')}
                className="mr-2"
              />
              HTML
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={mimeTypes.includes('application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
                onChange={() => handleMimeTypeChange('application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
                className="mr-2"
              />
              Word (DOCX)
            </label>
          </div>
        </div>
        
        <div className="mb-4">
          <span className="block text-gray-700 font-medium mb-2">
            オプション
          </span>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={updateExisting}
                onChange={() => setUpdateExisting(!updateExisting)}
                className="mr-2"
              />
              既存のドキュメントを更新する（オフにすると重複をスキップ）
            </label>
          </div>
        </div>
        
        <button
          type="submit"
          disabled={isSubmitting}
          className={`w-full py-2 px-4 rounded-lg text-white font-medium ${
            isSubmitting 
              ? 'bg-blue-400 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {isSubmitting ? '実行中...' : 'クローラーを実行'}
        </button>
      </form>
    </div>
  );
};

export default CrawlerForm;

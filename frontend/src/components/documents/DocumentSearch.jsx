import React, { useState } from 'react';
import axiosClient from '../../api/axiosClient';
import { FaSearch } from 'react-icons/fa';

const SOURCE_TYPES = ['FDA', 'NIST', 'PMDA', 'Other'];
const TOP_K_OPTIONS = [3, 5, 10, 20];

const highlightText = (text, query) => {
  if (!query) return text;
  const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escapedQuery})`, 'gi');
  const parts = text.split(regex);
  return parts.map((part, index) =>
    regex.test(part) ? <mark key={index} className="bg-yellow-200">{part}</mark> : part
  );
};

const DocumentSearch = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [topK, setTopK] = useState(5);
  const [filters, setFilters] = useState({});
  const [showFilters, setShowFilters] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    setLoading(true);
    setError(null);

    try {
      const filterParams = filters.sourceType ? { source_type: filters.sourceType } : undefined;
      const response = await axiosClient.post('/index/search', {
        query: searchQuery,
        top_k: topK,
        filters: filterParams
      });
      setSearchResults(response.data);
    } catch (err) {
      console.error(err);
      setError('検索中にエラーが発生しました。');
      setSearchResults([]);
    } finally {
      setLoading(false);
      setIsSearching(false);
    }
  };

  const resetFilters = () => {
    setFilters({});
    setSearchQuery('');
    setSearchResults([]);
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const renderSearchResult = (result, index) => (
    <div key={index} className="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start">
        <h3 className="text-lg font-semibold mb-2">{result.metadata?.title || 'タイトルなし'}</h3>
        <div>
          {result.metadata?.source_type && (
            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded mr-2">
              {result.metadata.source_type}
            </span>
          )}
          <span className="text-sm text-gray-500">スコア: {Math.round(result.score * 100) / 100}</span>
        </div>
      </div>
      <div className="mt-2 text-gray-700 whitespace-pre-wrap">
        {highlightText(result.text, searchQuery)}
      </div>
      {result.metadata?.url && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <a href={result.metadata.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline text-sm">
            原文を表示
          </a>
        </div>
      )}
    </div>
  );

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">ドキュメント検索</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">{error}</div>
      )}

      <div className="bg-white p-4 rounded-lg shadow-md mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">検索設定</h2>
          <button onClick={() => setShowFilters(!showFilters)} className="text-blue-600 hover:text-blue-800">
            {showFilters ? '設定を隠す' : '設定を表示'}
          </button>
        </div>

        <form onSubmit={handleSearch} className="flex gap-2 mb-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="ドキュメントを検索..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={isSearching || !searchQuery.trim()}
            className={`px-4 py-2 rounded-lg text-white font-medium flex items-center ${
              isSearching || !searchQuery.trim() ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            <FaSearch className="mr-2" />
            {isSearching ? '検索中...' : '検索'}
          </button>
          <button
            type="button"
            onClick={resetFilters}
            className="px-4 py-2 rounded-lg text-blue-600 border border-blue-600 hover:bg-blue-50"
          >
            リセット
          </button>
        </form>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div>
              <label className="block text-gray-700 font-medium mb-2">件数制限</label>
              <select
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {TOP_K_OPTIONS.map((k) => (
                  <option key={k} value={k}>{k}件</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-gray-700 font-medium mb-2">ソースタイプ</label>
              <select
                value={filters.sourceType || ''}
                onChange={(e) => handleFilterChange('sourceType', e.target.value)}
                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">すべて</option>
                {SOURCE_TYPES.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : searchResults.length === 0 && searchQuery.trim() && !isSearching ? (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6 text-center">
          <h3 className="text-lg font-semibold mb-4">検索結果が見つかりませんでした</h3>
          <p className="text-gray-600">検索条件を変更して再度お試しください。</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {searchResults.map(renderSearchResult)}
        </div>
      )}
    </div>
  );
};

export default DocumentSearch;

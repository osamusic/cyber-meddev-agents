import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axiosClient from '../../api/axiosClient';

const GuidelinesList = () => {
  const [guidelines, setGuidelines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [categories, setCategories] = useState([]);
  const [standards, setStandards] = useState([]);
  const [regions, setRegions] = useState([]);
  
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedStandard, setSelectedStandard] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        const [categoriesRes, standardsRes, regionsRes] = await Promise.all([
          axiosClient.get('/guidelines/categories'),
          axiosClient.get('/guidelines/standards'),
          axiosClient.get('/guidelines/regions')
        ]);
        
        setCategories(categoriesRes.data);
        setStandards(standardsRes.data);
        setRegions(regionsRes.data);
        
        let url = '/guidelines?';
        if (selectedCategory) url += `category=${selectedCategory}&`;
        if (selectedStandard) url += `standard=${selectedStandard}&`;
        if (selectedRegion) url += `region=${selectedRegion}&`;
        
        const guidelinesRes = await axiosClient.get(url);
        setGuidelines(guidelinesRes.data);
        
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('データの取得中にエラーが発生しました。');
      } finally {
        setLoading(false);
        setIsSearching(false);
      }
    };
    
    fetchData();
  }, [selectedCategory, selectedStandard, selectedRegion]);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!searchQuery.trim()) {
      return;
    }
    
    try {
      setIsSearching(true);
      
      const response = await axiosClient.post('/guidelines/search', {
        query: searchQuery,
        category: selectedCategory || undefined,
        standard: selectedStandard || undefined,
        region: selectedRegion || undefined
      });
      
      setGuidelines(response.data);
    } catch (err) {
      console.error('Search error:', err);
      setError('検索中にエラーが発生しました。');
    } finally {
      setIsSearching(false);
    }
  };

  const resetFilters = () => {
    setSelectedCategory('');
    setSelectedStandard('');
    setSelectedRegion('');
    setSearchQuery('');
  };

  if (!loading && !error && guidelines.length === 0) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold mb-4">ガイドラインが見つかりません</h2>
        <p className="text-gray-600 mb-6">
          選択したフィルタに一致するガイドラインがありません。
        </p>
        <button
          onClick={resetFilters}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
        >
          フィルタをリセット
        </button>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">医療機器サイバーセキュリティガイドライン</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-md mb-6">
        <h2 className="text-lg font-semibold mb-4">フィルタ</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {/* Category filter */}
          <div>
            <label className="block text-gray-700 font-medium mb-2">
              カテゴリ
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">すべて</option>
              {categories.map((category, index) => (
                <option key={index} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>
          
          {/* Standard filter */}
          <div>
            <label className="block text-gray-700 font-medium mb-2">
              標準
            </label>
            <select
              value={selectedStandard}
              onChange={(e) => setSelectedStandard(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">すべて</option>
              {standards.map((standard, index) => (
                <option key={index} value={standard}>
                  {standard}
                </option>
              ))}
            </select>
          </div>
          
          {/* Region filter */}
          <div>
            <label className="block text-gray-700 font-medium mb-2">
              地域
            </label>
            <select
              value={selectedRegion}
              onChange={(e) => setSelectedRegion(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">すべて</option>
              {regions.map((region, index) => (
                <option key={index} value={region}>
                  {region}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        {/* Search */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="ガイドラインを検索..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={isSearching || !searchQuery.trim()}
            className={`px-4 py-2 rounded-lg text-white font-medium ${
              isSearching || !searchQuery.trim()
                ? 'bg-blue-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
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
      </div>
      
      {/* Guidelines list */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {guidelines.map((guideline) => (
            <div
              key={guideline.id}
              className="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow"
            >
              <div className="flex justify-between items-start">
                <h3 className="text-lg font-semibold mb-2">
                  <Link
                    to={`/guidelines/${guideline.id}`}
                    className="text-blue-600 hover:underline"
                  >
                    {guideline.standard}: {guideline.guideline_id}
                  </Link>
                </h3>
                <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
                  {guideline.category}
                </span>
              </div>
              
              <p className="text-gray-700 mb-3 line-clamp-3">
                {guideline.control_text}
              </p>
              
              <div className="flex justify-between items-center">
                <div className="flex flex-wrap gap-1">
                  {guideline.keywords.map((keyword, index) => (
                    <span
                      key={index}
                      className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
                
                <span className="text-sm text-gray-500">
                  {guideline.region}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default GuidelinesList;

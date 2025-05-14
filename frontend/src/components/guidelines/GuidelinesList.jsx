/* eslint-disable react/prop-types */
import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import axiosClient from '../../api/axiosClient';
import { FaChevronDown, FaChevronRight, FaPlus, FaEdit, FaTrash } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';


const GuidelinesList = () => {
  const location = useLocation();
  const [guidelines, setGuidelines] = useState([]);
  const [classifications, setClassifications] = useState([]);
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
  
  const [selectedClassification, setSelectedClassification] = useState(null);
  const [showClassificationList, setShowClassificationList] = useState(true);
  const [loadingClassifications, setLoadingClassifications] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [guidelineToDelete, setGuidelineToDelete] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        console.log('ガイドラインデータを取得中...');
        
        const [categoriesRes, standardsRes, regionsRes] = await Promise.all([
          axiosClient.get('/guidelines/categories'),
          axiosClient.get('/guidelines/standards'),
          axiosClient.get('/guidelines/regions')
        ]);
        
        console.log('取得したカテゴリー:', categoriesRes.data);
        console.log('取得した標準規格:', standardsRes.data);
        console.log('取得した地域:', regionsRes.data);
        
        setCategories(categoriesRes.data && categoriesRes.data.length > 0 ? categoriesRes.data : ['NIST CSF', 'IEC 62443', 'Custom']);
        setStandards(standardsRes.data && standardsRes.data.length > 0 ? standardsRes.data : ['NIST-CSF-ID', 'IEC-62443-SR-1']);
        setRegions(regionsRes.data && regionsRes.data.length > 0 ? regionsRes.data : ['International', 'Japan', 'US']);
        
        let url = '/guidelines?';
        if (selectedCategory) url += `category=${encodeURIComponent(selectedCategory)}&`;
        if (selectedStandard) url += `standard=${encodeURIComponent(selectedStandard)}&`;
        if (selectedRegion) url += `region=${encodeURIComponent(selectedRegion)}&`;
        
        console.log('ガイドライン取得URL:', url);
        const guidelinesRes = await axiosClient.get(url);
        console.log('取得したガイドライン:', guidelinesRes.data);
        
        setGuidelines(guidelinesRes.data || []);
        
      } catch (err) {
        console.error('データ取得エラー:', err);
        if (err.response) {
          console.error('エラーレスポンス:', err.response.status, err.response.data);
          if (err.response.status === 401) {
            setError('認証エラー: ログインが必要です。再度ログインしてください。');
          } else {
            setError(`データの取得中にエラーが発生しました (${err.response.status}): ${err.response.data.detail || ''}`);
          }
        } else if (err.request) {
          console.error('リクエストエラー:', err.request);
          setError('サーバーに接続できませんでした。ネットワーク接続を確認してください。');
        } else {
          setError('データの取得中に予期しないエラーが発生しました。');
        }
      } finally {
        setLoading(false);
        setIsSearching(false);
      }
    };
    
    fetchData();
  }, [selectedCategory, selectedStandard, selectedRegion]);
  
  useEffect(() => {
    const fetchClassifications = async () => {
      try {
        setLoadingClassifications(true);
        console.log('分類データを取得中...');
        
        const response = await axiosClient.get('/classifier/all');
        console.log('取得した分類データ:', response.data);
        
        setClassifications(response.data || []);
      } catch (err) {
        console.error('分類データ取得エラー:', err);
        if (err.response) {
          console.error('エラーレスポンス:', err.response.status, err.response.data);
        }
      } finally {
        setLoadingClassifications(false);
      }
    };
    
    fetchClassifications();
  }, []);
  
  useEffect(() => {
    const checkIsAdmin = async () => {
      try {
        const response = await axiosClient.get('/me');
        setIsAdmin(response.data.is_admin);
      } catch (err) {
        console.error('Error checking admin status:', err);
        setIsAdmin(false);
      }
    };
    
    checkIsAdmin();
  }, []);
  
  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      window.history.replaceState({}, document.title);
    }
  }, [location]);

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

  const resetFilters = async () => {
    setSelectedCategory('');
    setSelectedStandard('');
    setSelectedRegion('');
    setSearchQuery('');
    setIsSearching(true);
    
    try {
      const response = await axiosClient.get('/guidelines');
      setGuidelines(response.data || []);
      setError(null);
    } catch (err) {
      console.error('フィルターリセットエラー:', err);
      setError('ガイドラインデータの再取得中にエラーが発生しました。');
    } finally {
      setIsSearching(false);
    }
  };
  
  const handleDeleteGuideline = async (guideline) => {
    if (!guideline) return;
    
    try {
      setLoading(true);
      await axiosClient.delete(`/guidelines/${guideline.guideline_id}`);
      
      setGuidelines(prev => prev.filter(g => g.id !== guideline.id));
      
      setSuccessMessage(`ガイドライン "${guideline.guideline_id}" は正常に削除されました`);
      
      setGuidelineToDelete(null);
    } catch (err) {
      console.error('Error deleting guideline:', err);
      let errorMessage = 'ガイドラインの削除中にエラーが発生しました';
      if (err.response) {
        errorMessage = `エラー (${err.response.status}): ${err.response.data.detail || errorMessage}`;
      }
      setError(errorMessage);
      setGuidelineToDelete(null);
    } finally {
      setLoading(false);
    }
  };

  if (!loading && !error && guidelines.length === 0 && classifications.length === 0) {
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

  const createGuidelineFromClassification = async (classification, selectedReqs = []) => {
    if (!classification) return;

    try {
      const nistCategory = classification.nist?.primary_category
        ? `NIST : ${classification.nist.primary_category}` : '';
      const iecRequirement = classification.iec?.primary_requirement
        ? `IEC62443 : ${classification.iec?.primary_requirement}` : '';
      const keywords = classification.keywords || [];
      const processedKeywords = keywords.map(keyword => 
        typeof keyword === 'object' ? keyword.keyword : keyword
      );

      const categories = [nistCategory, iecRequirement].filter(Boolean).join(' / ');
      const guidelineId = String(classification.document_id);
      
      let controlText = '';
      if (Array.isArray(classification.requirements)) {
        const filteredRequirements = classification.requirements.filter(req => 
          selectedReqs.includes(req.id)
        );
        
        if (filteredRequirements.length > 0) {
          controlText = filteredRequirements.map(req => 
            `${req.id}. 【${req.type}】${req.text}`
          ).join('\n');
        } else {
          controlText = '選択された要件はありません';
        }
      } else {
        controlText = classification.requirements || '分類結果から生成されたガイドライン';
      }
      
      // source_urlとoriginal_titleをDBから取得
      let documentUrl = '';
      let originalTitle = '';
      try {
        const documentResponse = await axiosClient.get(`/admin/documents/${classification.document_id}`);
        documentUrl = documentResponse.data.url || '';
        originalTitle = documentResponse.data.original_title || '';
        
        if (!originalTitle) {
          originalTitle = documentResponse.data.title;
        }
      } catch (docErr) {
        console.warn('ドキュメント情報取得エラー:', docErr);
        documentUrl = 'Error';
        originalTitle = 'Error';
      }
      
      const guidelineData = {
        guideline_id: guidelineId,
        category: categories,
        standard: originalTitle,
        control_text: controlText,
        source_url: documentUrl,
        region: 'International',
        keywords: processedKeywords
      };
      
      const response = await axiosClient.post('/guidelines/', guidelineData);
      console.log('ガイドライン作成成功:', response.data);
      
      let url = '/guidelines?';
      if (selectedCategory) url += `category=${encodeURIComponent(selectedCategory)}&`;
      if (selectedStandard) url += `standard=${encodeURIComponent(selectedStandard)}&`;
      if (selectedRegion) url += `region=${encodeURIComponent(selectedRegion)}&`;
      
      const guidelinesRes = await axiosClient.get(url);
      setGuidelines(guidelinesRes.data || []);
      
      setSelectedClassification(null);
      
      return response.data;
    } catch (err) {
      console.error('ガイドライン作成エラー:', err);
      
      if (err.response) {
        console.error('エラーレスポンス:', err.response.status, err.response.data);
        
        if (err.response.status === 422) {
          const validationErrors = err.response.data.detail || [];
          if (Array.isArray(validationErrors) && validationErrors.length > 0) {
            const errorMessages = validationErrors.map(error => 
              `${error.loc.join('.')}：${error.msg}`
            ).join('\n');
            setError(`ガイドライン作成のバリデーションエラー:\n${errorMessages}`);
          } else {
            setError(`ガイドライン作成のバリデーションエラー: ${JSON.stringify(err.response.data)}`);
          }
        } else if (err.response.status === 401 || err.response.status === 403) {
          setError(`権限エラー: ガイドラインを作成する権限がありません (${err.response.status})`);
        } else {
          const errorDetail = err.response.data.detail || '';
          const errorMessage = typeof errorDetail === 'string' 
            ? errorDetail 
            : JSON.stringify(errorDetail);
          setError(`ガイドライン作成中にエラーが発生しました (${err.response.status}): ${errorMessage}`);
        }
      } else if (err.request) {
        console.error('リクエストエラー:', err.request);
        setError('サーバーに接続できませんでした。ネットワーク接続を確認してください。');
      } else {
        console.error('リクエスト設定エラー:', err.message);
        setError(`ガイドライン作成中に予期しないエラーが発生しました: ${err.message}`);
      }
      
      return null;
    }
  };
  
const ClassificationDetail = ({ classification, onClose, onCreateGuideline }) => {
    const [selectedRequirements, setSelectedRequirements] = useState([]);
    const [isAdmin, setIsAdmin] = useState(false);
    
    useEffect(() => {
      const checkIsAdmin = async () => {
        try {
          const response = await axiosClient.get('/me');
          setIsAdmin(response.data.is_admin);
        } catch (err) {
          console.error('Error checking admin status:', err);
          setIsAdmin(false);
        }
      };
      
      checkIsAdmin();
    }, []);
    
    const toggleRequirement = (reqId) => {
      if (!isAdmin) return; // 管理者以外は変更不可
      
      if (selectedRequirements.includes(reqId)) {
        setSelectedRequirements(selectedRequirements.filter(id => id !== reqId));
      } else {
        setSelectedRequirements([...selectedRequirements, reqId]);
      }
    };
    
    useEffect(() => {
      if (classification && Array.isArray(classification.requirements)) {
        setSelectedRequirements(classification.requirements.map(req => req.id));
      }
    }, [classification]);
    
    if (!classification) return null;
    
    return (
      <div>
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-xl font-semibold">分類詳細</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
        
        <div className="mb-4">
          <h4 className="text-lg font-medium mb-2">ドキュメント情報</h4>
          <p><span className="font-medium">タイトル:</span> {classification.document_title}</p>
          <p><span className="font-medium">作成日時:</span> {new Date(classification.created_at).toLocaleString('ja-JP')}</p>
        </div>
        
        <div className="mb-4">
          <h4 className="text-lg font-medium mb-2">要件リスト</h4>
          {Array.isArray(classification.requirements) ? (
            <div className="space-y-2">
              {classification.requirements.map((req) => (
                <div key={req.id} className="flex items-start">
                  <input
                    type="checkbox"
                    id={`req-${req.id}`}
                    className="mt-1 mr-2"
                    checked={selectedRequirements.includes(req.id)}
                    onChange={() => toggleRequirement(req.id)}
                    disabled={!isAdmin}
                  />
                  <label 
                    htmlFor={`req-${req.id}`} 
                    className={`${isAdmin ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                  >
                    <span className="font-medium">{`【${req.type}】`}</span> {req.text}
                  </label>
                </div>
              ))}
            </div>
          ) : (
            <ReactMarkdown>{`${classification.requirements}`}</ReactMarkdown>
          )}
        </div>

        {classification.nist && (
          <div className="mb-4">
            <h4 className="text-lg font-medium mb-2">NIST CSF分類</h4>
            <p><span className="font-medium">主要カテゴリ:</span> {classification.nist.primary_category}</p>
            <p><span className="font-medium">説明:</span> {classification.nist.explanation}</p>
            
            <div className="mt-2">
              <h5 className="font-medium">カテゴリスコア:</h5>
              <div className="grid grid-cols-2 gap-2 mt-1">
                {Object.entries(classification.nist.categories || {}).map(([category, data]) => (
                  <div key={category} className="bg-blue-50 p-2 rounded">
                    <div className="flex justify-between">
                      <span className="font-medium">{category}:</span>
                      <span>{data.score}/10</span>
                    </div>
                    <p className="text-sm text-gray-600">{data.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {classification.iec && (
          <div className="mb-4">
            <h4 className="text-lg font-medium mb-2">IEC 62443分類</h4>
            <p><span className="font-medium">主要要件:</span> {classification.iec.primary_requirement}</p>
            <p><span className="font-medium">説明:</span> {classification.iec.explanation}</p>
            
            <div className="mt-2">
              <h5 className="font-medium">要件スコア:</h5>
              <div className="grid grid-cols-2 gap-2 mt-1">
                {Object.entries(classification.iec.requirements || {}).map(([req, data]) => (
                  <div key={req} className="bg-green-50 p-2 rounded">
                    <div className="flex justify-between">
                      <span className="font-medium">{req}:</span>
                      <span>{data.score}/10</span>
                    </div>
                    <p className="text-sm text-gray-600">{data.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        
        {classification.keywords && classification.keywords.length > 0 && (
          <div className="mb-4">
            <h4 className="text-lg font-medium mb-2">キーワード</h4>
            <div className="flex flex-wrap gap-2">
              {classification.keywords.map((keywordObj, index) => (
                <span
                  key={index}
                  className="bg-purple-100 text-purple-800 text-sm px-3 py-1 rounded-full"
                >
                  {typeof keywordObj === 'object' ? keywordObj.keyword : keywordObj}
                </span>
              ))}
            </div>
          </div>
        )}
        
        <div className="mt-6 flex justify-end">
          <button
            onClick={() => onCreateGuideline(classification, selectedRequirements)}
            className={`${isAdmin 
              ? 'bg-green-600 hover:bg-green-700' 
              : 'bg-gray-400 cursor-not-allowed'} text-white font-medium py-2 px-4 rounded flex items-center`}
            disabled={!isAdmin}
            title={!isAdmin ? "管理者権限が必要です" : ""}
          >
            <FaPlus className="mr-2" /> ガイドラインを作成
          </button>
        </div>
      </div>
    );
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">医療機器サイバーセキュリティガイドライン</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {successMessage && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          {successMessage}
          <button onClick={() => setSuccessMessage('')} className="float-right">✕</button>
        </div>
      )}
      
      {/* 選択された分類の詳細表示はリスト内に移動 */}
      
      {/* Create New Guideline Button (admin only) */}
      {isAdmin && (
        <div className="mb-4">
          <Link 
            to="/guidelines/new"
            className="bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded-lg inline-flex items-center"
          >
            <FaPlus className="mr-2" /> 新しいガイドラインを作成
          </Link>
        </div>
      )}
      
      {/* 分類データ一覧 */}
      <div className="bg-white p-4 rounded-lg shadow-md mb-6">
        <div 
          className="flex justify-between items-center cursor-pointer"
          onClick={() => setShowClassificationList(!showClassificationList)}
        >
          <h2 className="text-lg font-semibold">分類データ一覧</h2>
          {showClassificationList ? <FaChevronDown /> : <FaChevronRight />}
        </div>
        
        {showClassificationList && (
          <div className="mt-4">
            {loadingClassifications ? (
              <div className="flex justify-center items-center h-24">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
              </div>
            ) : classifications.length === 0 ? (
              <p className="text-gray-500 text-center py-4">分類データがありません</p>
            ) : (
              <div className="grid grid-cols-1 gap-3 mt-3">
                {classifications.map((classification) => (
                  <div
                    key={classification.id}
                    className="border rounded-lg transition-colors overflow-hidden"
                  >
                    <div 
                      className={`p-3 cursor-pointer ${
                        selectedClassification && selectedClassification.id === classification.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                      onClick={() => {
                        if (selectedClassification && selectedClassification.id === classification.id) {
                          setSelectedClassification(null);
                        } else {
                          setSelectedClassification(classification);
                        }
                      }}
                    >
                      <div className="flex justify-between items-start">
                        <h3 className="font-medium">{classification.document_title}</h3>
                        <span className="text-xs text-gray-500">
                          {new Date(classification.created_at).toLocaleDateString('ja-JP')}
                        </span>
                      </div>
                      
                      <div className="mt-2 flex flex-wrap gap-2">
                        {classification.nist && (
                          <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                            NIST: {classification.nist.primary_category}
                          </span>
                        )}
                        {classification.iec && (
                          <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                            IEC: {classification.iec.primary_requirement}
                          </span>
                        )}
                      </div>
                      
                      {classification.requirements && (
                        <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                          {Array.isArray(classification.requirements) 
                            ? classification.requirements.map(req => `【${req.type}】${req.text}`).slice(0, 2).join(', ') + (classification.requirements.length > 2 ? '...' : '')
                            : classification.requirements}
                        </p>
                      )}
                    </div>
                    
                    {/* インライン詳細表示 */}
                    {selectedClassification && selectedClassification.id === classification.id && (
                      <div className="border-t border-gray-200 bg-white p-4">
                        <ClassificationDetail
                          classification={classification}
                          onClose={() => setSelectedClassification(null)}
                          onCreateGuideline={createGuidelineFromClassification}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      
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
      ) : guidelines.length === 0 ? (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h3 className="text-lg font-semibold mb-4">ガイドラインがまだありません</h3>
          <p className="text-gray-600 mb-4">
            分類データから新しいガイドラインを作成できます。上部の「分類データ一覧」から選択してください。
          </p>
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
                <div>
                  <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded mr-2">
                    {guideline.category}
                  </span>
                  {isAdmin && (
                    <>
                      <Link to={`/guidelines/edit/${guideline.id}`} className="text-yellow-500 hover:text-yellow-600 mx-2">
                        <FaEdit />
                      </Link>
                      <button 
                        onClick={() => setGuidelineToDelete(guideline)}
                        className="text-red-500 hover:text-red-600"
                      >
                        <FaTrash />
                      </button>
                    </>
                  )}
                </div>
              </div>
              
              <p className="text-gray-700 mb-3 line-clamp-3">
                {guideline.control_text}
              </p>
              
              {/* Classification results */}
              {guideline.classification && (
                <div className="mt-3 mb-3 pt-3 border-t border-gray-200">
                  <h4 className="text-sm font-medium mb-2">分類結果:</h4>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {guideline.classification.nist && (
                      <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                        NIST: {guideline.classification.nist}
                      </span>
                    )}
                    {guideline.classification.iec && (
                      <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                        IEC: {guideline.classification.iec}
                      </span>
                    )}
                  </div>
                  {guideline.classification.requirements && (
                    <div className="mt-2">
                      <p className="text-sm text-gray-600 italic line-clamp-2">
                        &quot;{Array.isArray(guideline.classification.requirements) 
                          ? guideline.classification.requirements.map(req => `【${req.type}】${req.text}`).slice(0, 2).join(', ') + (guideline.classification.requirements.length > 2 ? '...' : '')
                          : guideline.classification.requirements}&quot;
                      </p>
                    </div>
                  )}
                </div>
              )}
              
              <div className="flex justify-between items-center">
                <div className="flex flex-wrap gap-1">
                  {guideline.keywords && guideline.keywords.map((keyword, index) => (
                    <span
                      key={index}
                      className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded"
                    >
                      {keyword}
                    </span>
                  ))}
                  {guideline.classification && guideline.classification.keywords && 
                   guideline.classification.keywords.filter(k => {
                     const keywordValue = typeof k === 'object' ? k.keyword : k;
                     return !guideline.keywords || !guideline.keywords.includes(keywordValue);
                   }).map((keyword, index) => (
                    <span
                      key={`classified-${index}`}
                      className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded"
                    >
                      {typeof keyword === 'object' ? keyword.keyword : keyword}
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
      
      {/* 削除確認ダイアログ */}
      {guidelineToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <h3 className="text-xl font-semibold mb-4">ガイドラインを削除しますか？</h3>
            <p className="mb-6 text-gray-600">
              ガイドライン &quot;{guidelineToDelete.guideline_id}&quot; を削除してもよろしいですか？
              この操作は元に戻せません。
            </p>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setGuidelineToDelete(null)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100"
              >
                キャンセル
              </button>
              <button
                onClick={() => handleDeleteGuideline(guidelineToDelete)}
                className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
              >
                削除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


export default GuidelinesList;

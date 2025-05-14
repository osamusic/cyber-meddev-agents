import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axiosClient from '../../api/axiosClient';

const GuidelineForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [isEdit, setIsEdit] = useState(false);
  
  const [formData, setFormData] = useState({
    guideline_id: '',
    category: '',
    standard: '',
    control_text: '',
    source_url: '',
    region: 'International',
    keywords: []
  });
  
  const [keywordInput, setKeywordInput] = useState('');
  
  useEffect(() => {
    const fetchGuideline = async () => {
      if (!id) {
        setLoading(false);
        return;
      }
      
      try {
        setLoading(true);
        const response = await axiosClient.get('/guidelines');
        const found = response.data.find(g => g.id === parseInt(id));
        
        if (found) {
          setFormData({
            guideline_id: found.guideline_id,
            category: found.category,
            standard: found.standard,
            control_text: found.control_text,
            source_url: found.source_url,
            region: found.region,
            keywords: [...found.keywords] // Clone to avoid reference issues
          });
          setIsEdit(true);
        } else {
          setError('ガイドラインが見つかりません');
          navigate('/guidelines');
        }
      } catch (err) {
        console.error('Error fetching guideline:', err);
        setError('ガイドラインの取得中にエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };
    
    fetchGuideline();
  }, [id, navigate]);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const addKeyword = () => {
    if (keywordInput.trim() && !formData.keywords.includes(keywordInput.trim())) {
      setFormData(prev => ({
        ...prev,
        keywords: [...prev.keywords, keywordInput.trim()]
      }));
      setKeywordInput('');
    }
  };
  
  const removeKeyword = (keyword) => {
    setFormData(prev => ({
      ...prev,
      keywords: prev.keywords.filter(k => k !== keyword)
    }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.guideline_id || !formData.category || !formData.standard || !formData.control_text) {
      setError('必須項目をすべて入力してください');
      return;
    }
    
    try {
      setSaving(true);
      
      if (isEdit) {
        await axiosClient.put(`/guidelines/${formData.guideline_id}`, formData);
        navigate(`/guidelines/${id}`, { 
          state: { message: 'ガイドラインが正常に更新されました' } 
        });
      } else {
        const response = await axiosClient.post('/guidelines', formData);
        navigate(`/guidelines/${response.data.id}`, { 
          state: { message: 'ガイドラインが正常に作成されました' } 
        });
      }
    } catch (err) {
      console.error('Error saving guideline:', err);
      let errorMessage = 'ガイドラインの保存中にエラーが発生しました';
      if (err.response) {
        errorMessage = `エラー (${err.response.status}): ${err.response.data.detail || errorMessage}`;
      }
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h1 className="text-2xl font-bold mb-6">
        {isEdit ? 'ガイドラインを編集' : '新しいガイドラインを作成'}
      </h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-gray-700 font-medium mb-2" htmlFor="guideline_id">
              ガイドラインID *
            </label>
            <input
              type="text"
              id="guideline_id"
              name="guideline_id"
              value={formData.guideline_id}
              onChange={handleChange}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              disabled={isEdit} // 編集時はIDを変更できないようにする
            />
          </div>
          
          <div>
            <label className="block text-gray-700 font-medium mb-2" htmlFor="category">
              カテゴリ *
            </label>
            <input
              type="text"
              id="category"
              name="category"
              value={formData.category}
              onChange={handleChange}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-gray-700 font-medium mb-2" htmlFor="standard">
              標準 *
            </label>
            <input
              type="text"
              id="standard"
              name="standard"
              value={formData.standard}
              onChange={handleChange}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-gray-700 font-medium mb-2" htmlFor="region">
              地域
            </label>
            <input
              type="text"
              id="region"
              name="region"
              value={formData.region}
              onChange={handleChange}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-gray-700 font-medium mb-2" htmlFor="source_url">
              ソースURL
            </label>
            <input
              type="text"
              id="source_url"
              name="source_url"
              value={formData.source_url}
              onChange={handleChange}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-gray-700 font-medium mb-2" htmlFor="control_text">
              管理策テキスト *
            </label>
            <textarea
              id="control_text"
              name="control_text"
              value={formData.control_text}
              onChange={handleChange}
              rows="6"
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            ></textarea>
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-gray-700 font-medium mb-2">
              キーワード
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="新しいキーワードを入力..."
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyword())}
              />
              <button
                type="button"
                onClick={addKeyword}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                追加
              </button>
            </div>
            
            <div className="flex flex-wrap gap-2 mt-2">
              {formData.keywords.map((keyword, index) => (
                <span
                  key={index}
                  className="bg-gray-100 text-gray-800 px-3 py-1 rounded-full flex items-center"
                >
                  {keyword}
                  <button
                    type="button"
                    onClick={() => removeKeyword(keyword)}
                    className="ml-2 text-gray-500 hover:text-red-500"
                  >
                    ✕
                  </button>
                </span>
              ))}
              {formData.keywords.length === 0 && (
                <span className="text-gray-500 italic">キーワードがありません</span>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex justify-between mt-6">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100"
          >
            キャンセル
          </button>
          <button
            type="submit"
            disabled={saving}
            className={`px-6 py-2 rounded-lg text-white font-medium ${
              saving ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {saving ? '保存中...' : (isEdit ? '更新' : '作成')}
          </button>
        </div>
      </form>
    </div>
  );
};

export default GuidelineForm;

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
            keywords: [...found.keywords]
          });
          setIsEdit(true);
        } else {
          setError('Guideline not found');
          navigate('/guidelines');
        }
      } catch (err) {
        console.error('Error fetching guideline:', err);
        setError('An error occurred while fetching the guideline');
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
    const kw = keywordInput.trim();
    if (kw && !formData.keywords.includes(kw)) {
      setFormData(prev => ({
        ...prev,
        keywords: [...prev.keywords, kw]
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
      setError('Please fill in all required fields');
      return;
    }

    try {
      setSaving(true);

      if (isEdit) {
        await axiosClient.put(`/guidelines/${formData.guideline_id}`, formData);
        navigate(`/guidelines/${id}`, {
          state: { message: 'Guideline updated successfully' }
        });
      } else {
        const response = await axiosClient.post('/guidelines', formData);
        navigate(`/guidelines/${response.data.id}`, {
          state: { message: 'Guideline created successfully' }
        });
      }
    } catch (err) {
      console.error('Error saving guideline:', err);
      let msg = 'An error occurred while saving the guideline';
      if (err.response) {
        msg = `Error (${err.response.status}): ${err.response.data.detail || msg}`;
      }
      setError(msg);
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
        {isEdit ? 'Edit Guideline' : 'Create New Guideline'}
      </h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label htmlFor="guideline_id" className="block text-gray-700 font-medium mb-2">
              Guideline ID *
            </label>
            <input
              type="text"
              id="guideline_id"
              name="guideline_id"
              value={formData.guideline_id}
              onChange={handleChange}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              disabled={isEdit}
            />
          </div>
          <div>
            <label htmlFor="category" className="block text-gray-700 font-medium mb-2">
              Category *
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
            <label htmlFor="standard" className="block text-gray-700 font-medium mb-2">
              Standard *
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
            <label htmlFor="region" className="block text-gray-700 font-medium mb-2">
              Region
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
            <label htmlFor="source_url" className="block text-gray-700 font-medium mb-2">
              Source URL
            </label>
            <input
              type="url"
              id="source_url"
              name="source_url"
              value={formData.source_url}
              onChange={handleChange}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="md:col-span-2">
            <label htmlFor="control_text" className="block text-gray-700 font-medium mb-2">
              Control Text *
            </label>
            <textarea
              id="control_text"
              name="control_text"
              value={formData.control_text}
              onChange={handleChange}
              rows={6}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-gray-700 font-medium mb-2">
              Keywords
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addKeyword())}
                className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter keyword..."
              />
              <button
                type="button"
                onClick={addKeyword}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {formData.keywords.length > 0 ? (
                formData.keywords.map((keyword, idx) => (
                  <span key={idx} className="bg-gray-100 text-gray-800 px-3 py-1 rounded-full flex items-center">
                    {keyword}
                    <button
                      type="button"
                      onClick={() => removeKeyword(keyword)}
                      className="ml-2 text-gray-500 hover:text-red-500"
                    >
                      ×
                    </button>
                  </span>
                ))
              ) : (
                <span className="text-gray-500 italic">No keywords added</span>
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
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className={`px-6 py-2 rounded-lg text-white font-medium ${
              saving ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {saving ? 'Saving...' : (isEdit ? 'Update' : 'Create')}
          </button>
        </div>
      </form>
    </div>
  );
};

export default GuidelineForm;

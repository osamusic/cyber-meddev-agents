import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axiosClient from '../../api/axiosClient';

const GuidelineDetail = () => {
  const { id } = useParams();
  const [guideline, setGuideline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchGuideline = async () => {
      try {
        setLoading(true);
        const response = await axiosClient.get('/guidelines');
        const found = response.data.find(g => g.id === parseInt(id));
        
        if (found) {
          setGuideline(found);
        } else {
          setError('ガイドラインが見つかりません');
        }
      } catch (err) {
        console.error('Error fetching guideline:', err);
        setError('ガイドラインの取得中にエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    fetchGuideline();
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error || !guideline) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
        <p>{error || 'ガイドラインが見つかりません'}</p>
        <Link to="/guidelines" className="text-blue-600 hover:underline mt-2 inline-block">
          ガイドライン一覧に戻る
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-6">
        <Link to="/guidelines" className="text-blue-600 hover:underline">
          ← ガイドライン一覧に戻る
        </Link>
      </div>
      
      <div className="flex justify-between items-start mb-4">
        <h1 className="text-2xl font-bold">
          {guideline.standard}: {guideline.guideline_id}
        </h1>
        <span className="bg-blue-100 text-blue-800 text-sm font-medium px-2.5 py-0.5 rounded">
          {guideline.category}
        </span>
      </div>
      
      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-2">管理策</h2>
        <div className="bg-gray-50 p-4 rounded border">
          <p className="whitespace-pre-line">{guideline.control_text}</p>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <h2 className="text-lg font-semibold mb-2">詳細情報</h2>
          <table className="w-full">
            <tbody>
              <tr className="border-b">
                <td className="py-2 font-medium">標準</td>
                <td className="py-2">{guideline.standard}</td>
              </tr>
              <tr className="border-b">
                <td className="py-2 font-medium">ID</td>
                <td className="py-2">{guideline.guideline_id}</td>
              </tr>
              <tr className="border-b">
                <td className="py-2 font-medium">カテゴリ</td>
                <td className="py-2">{guideline.category}</td>
              </tr>
              <tr>
                <td className="py-2 font-medium">地域</td>
                <td className="py-2">{guideline.region}</td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div>
          <h2 className="text-lg font-semibold mb-2">ソース</h2>
          <div className="bg-gray-50 p-4 rounded border">
            <p className="mb-2">
              <span className="font-medium">URL: </span>
              <a 
                href={guideline.source_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline break-all"
              >
                {guideline.source_url}
              </a>
            </p>
          </div>
        </div>
      </div>
      
      <div>
        <h2 className="text-lg font-semibold mb-2">キーワード</h2>
        <div className="flex flex-wrap gap-2">
          {guideline.keywords.map((keyword, index) => (
            <span
              key={index}
              className="bg-gray-100 text-gray-800 px-3 py-1 rounded-full"
            >
              {keyword}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default GuidelineDetail;

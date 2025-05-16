import React from 'react';
import { FaSpinner } from 'react-icons/fa';
import { useProcess } from '../../contexts/ProcessContext';

const ProgressModal = () => {
  const { 
    classificationLoading,
    classificationError,
    classificationProgress,
    showProgressModal,
    closeProgressModal
  } = useProcess();
  
  if (!showProgressModal) {
    return null;
  }
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-lg max-w-lg w-full">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Processing Status</h3>
          <button 
            onClick={closeProgressModal}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
        
        {classificationError && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {classificationError}
          </div>
        )}
        
        {classificationLoading && (
          <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4 flex items-center">
            <FaSpinner className="animate-spin mr-2 text-xl" />
            <div>
              <p className="font-medium">Classification in progress...</p>
            </div>
          </div>
        )}
        
        {classificationProgress && (
          <div className="mb-4">
            <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
              <div 
                className="bg-blue-600 h-2.5 rounded-full" 
                style={{ width: `${(classificationProgress.current_count / classificationProgress.total_count) * 100}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600">
              {classificationProgress.status === 'initializing' && 'Initializing...'}
              {classificationProgress.status === 'in_progress' && `Processing... ${classificationProgress.current_count}/${classificationProgress.total_count} documents completed`}
              {classificationProgress.status === 'completed' && 'All documents have been classified'}
              {classificationProgress.status === 'error' && 'An error occurred during classification'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressModal;

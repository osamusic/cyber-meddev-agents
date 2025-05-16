import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import axiosClient from '../../api/axiosClient';
import { FaSpinner, FaChevronDown, FaChevronRight } from 'react-icons/fa';
import { useProcess } from '../../contexts/ProcessContext';

const ClassificationForm = ({ onClassifyComplete }) => {
  const { 
    classificationLoading: loading, 
    classificationError: error, 
    classificationProgress: progress, 
    startClassification 
  } = useProcess();
  
  const [documents, setDocuments] = useState([]);
  const [selectedDocuments, setSelectedDocuments] = useState([]);
  const [classifyAll, setClassifyAll] = useState(false);
  const [reclassifyMode, setReclassifyMode] = useState(false);  // State for reclassification mode
  const [success, setSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);
  const [expandedGroups, setExpandedGroups] = useState({});  // Manage group expand state
  
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await axiosClient.get('/admin/documents');
        setDocuments(response.data);
      } catch (err) {
        console.error('Error fetching documents:', err);
      }
    };
    
    fetchDocuments();
  }, []);
  
  const resetForm = () => {
    setSuccess(false);
    setSuccessMessage(null);
    setSelectedDocuments([]);
    setClassifyAll(false);
    setReclassifyMode(false);
  };

  const toggleGroup = (groupTitle) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupTitle]: !prev[groupTitle]
    }));
  };

  useEffect(() => {
    if (progress?.status === 'completed') {
      setSuccess(true);
      setSelectedDocuments([]);
      setClassifyAll(false);
      if (onClassifyComplete) {
        onClassifyComplete();
      }
    }
  }, [progress, onClassifyComplete]);

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    resetForm();
    setSuccessMessage('Classification process has started. Monitoring progress...');
    
    const requestData = {
      all_documents: classifyAll,
      document_ids: classifyAll ? [] : selectedDocuments,
      reclassify: reclassifyMode,
    };
    
    await startClassification(requestData);
  };
  
  const handleDocumentSelect = (e, docId) => {
    if (e.target.checked) {
      setSelectedDocuments(prev => [...prev, docId]);
    } else {
      setSelectedDocuments(prev => prev.filter(id => id !== docId));
    }
  };
  
  const handleGroupSelect = (e, docs) => {
    const selectableDocIds = docs
      .filter(doc => !doc.is_classified || reclassifyMode)
      .map(doc => doc.id);
    
    if (e.target.checked) {
      setSelectedDocuments(prev => [...new Set([...prev, ...selectableDocIds])]);
    } else {
      setSelectedDocuments(prev => prev.filter(id => !selectableDocIds.includes(id)));
    }
  };
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-md mt-4">
      <h2 className="text-lg font-semibold mb-4">Document Classification</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          Classification process has started. Results will be available shortly.
          {successMessage && <p className="mt-2">{successMessage}</p>}
        </div>
      )}
      
      {loading && (
        <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4 flex items-center">
          <FaSpinner className="animate-spin mr-2 text-xl" />
          <div>
            <p className="font-medium">Classification in progress...</p>
          </div>
        </div>
      )}
      
      {/* Progress display */}
      {progress && (
        <div className="mb-4">
          <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
            <div 
              className="bg-blue-600 h-2.5 rounded-full" 
              style={{ width: `${(progress.current_count / progress.total_count) * 100}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-600">
            {progress.status === 'initializing' && 'Initializing...'}
            {progress.status === 'in_progress' && `Processing... ${progress.current_count}/${progress.total_count} documents completed`}
            {progress.status === 'completed' && 'All documents have been classified'}
            {progress.status === 'error' && 'An error occurred during classification process'}
          </p>
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
            <span className="font-medium">Classify all documents</span>
          </label>
          
          <label className="flex items-center mb-2 mt-2">
            <input
              type="checkbox"
              checked={reclassifyMode}
              onChange={(e) => setReclassifyMode(e.target.checked)}
              className="mr-2"
            />
            <span className="font-medium">Reclassification mode (reclassify already classified documents)</span>
          </label>
        </div>
        
        {!classifyAll && (
          <div className="mb-4">
            <h3 className="font-medium mb-2">Select documents to classify:</h3>
            <div className="max-h-60 overflow-y-auto border rounded p-2">
              {documents.length === 0 ? (
                <p className="text-gray-500">No documents available</p>
              ) : (
                (() => {
                  const documentGroups = groupDocumentsByOriginalTitle();
                  return Object.entries(documentGroups).map(([groupTitle, docs]) => {
                    const allClassified = docs.every(doc => doc.is_classified);
                    const selectableDocIds = docs
                      .filter(doc => !doc.is_classified || reclassifyMode)
                      .map(doc => doc.id);
                    const allSelected = selectableDocIds.length > 0 && 
                      selectableDocIds.every(id => selectedDocuments.includes(id));
                    
                    return (
                      <div key={groupTitle} className={`mb-3 border-b pb-2 ${allClassified && !reclassifyMode ? 'opacity-60' : ''}`}>
                        <div className="flex items-center cursor-pointer mb-1" onClick={() => toggleGroup(groupTitle)}>
                          <div className="mr-2">
                            {expandedGroups[groupTitle] ? <FaChevronDown /> : <FaChevronRight />}
                          </div>
                          
                          <label className="flex items-center flex-grow cursor-pointer">
                            <input
                              type="checkbox"
                              onChange={(e) => handleGroupSelect(e, docs)}
                              checked={allSelected}
                              disabled={selectableDocIds.length === 0}
                              className="mr-2"
                              onClick={(e) => e.stopPropagation()}
                            />
                            <span className={`font-medium ${allClassified && !reclassifyMode ? 'text-gray-500' : ''}`}>{groupTitle} ({docs.length})</span>
                            {allClassified && <span className="ml-2 text-sm text-gray-500">(All classified)</span>}
                          </label>
                        </div>
                        
                        {expandedGroups[groupTitle] && (
                          <div className="pl-7 mt-1">
                            {docs.map(doc => (
                              <label key={doc.id} className={`flex items-center mb-2 ${doc.is_classified && !reclassifyMode ? 'text-gray-400' : ''}`}>
                                <input
                                  type="checkbox"
                                  onChange={(e) => handleDocumentSelect(e, doc.id)}
                                  checked={selectedDocuments.includes(doc.id)}
                                  disabled={doc.is_classified && !reclassifyMode}
                                  className="mr-2"
                                />
                                <span>{doc.title || doc.url}</span>
                                {doc.is_classified && <span className="ml-2 text-sm text-gray-500">(Classified)</span>}
                                {doc.is_classified && reclassifyMode && selectedDocuments.includes(doc.id) && <span className="ml-2 text-sm text-blue-500">(Reclassification pending)</span>}
                              </label>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  });
                })()
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
              {progress ? `Processing... ${progress.current_count}/${progress.total_count}` : 'Processing...'}
            </>
          ) : (
            'Start Classification'
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

import React, { createContext, useState, useContext, useEffect } from 'react';
import PropTypes from 'prop-types';
import axiosClient from '../api/axiosClient';

const ProcessContext = createContext(null);

export const ProcessProvider = ({ children }) => {
  const [classificationLoading, setClassificationLoading] = useState(false);
  const [classificationError, setClassificationError] = useState(null);
  const [classificationProgress, setClassificationProgress] = useState(null);
  const [pollInterval, setPollInterval] = useState(null);
  const [showProgressModal, setShowProgressModal] = useState(false);
  
  useEffect(() => {
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [pollInterval]);
  
  useEffect(() => {
    if (classificationLoading) {
      setShowProgressModal(true);
    } else if (classificationProgress?.status === 'completed' || classificationProgress?.status === 'error') {
      setTimeout(() => {
        setShowProgressModal(false);
      }, 3000);
    }
  }, [classificationLoading, classificationProgress]);
  
  const startClassificationProgressPolling = () => {
    if (pollInterval) {
      clearInterval(pollInterval);
    }
    
    const interval = setInterval(async () => {
      try {
        const progressResponse = await axiosClient.get('/classifier/progress');
        setClassificationProgress(progressResponse.data);
        
        if (['completed', 'error'].includes(progressResponse.data.status)) {
          stopProgressPolling();
          setClassificationLoading(false);
        }
      } catch (error) {
        console.error('Error fetching classification progress:', error);
      }
    }, 2000); // Poll every 2 seconds
    
    setPollInterval(interval);
  };
  
  const stopProgressPolling = () => {
    if (pollInterval) {
      clearInterval(pollInterval);
      setPollInterval(null);
    }
  };
  
  const startClassification = async (requestData) => {
    try {
      setClassificationLoading(true);
      setClassificationError(null);
      setClassificationProgress(null);
      
      await axiosClient.post('/classifier/classify', requestData);
      
      startClassificationProgressPolling();
      return true;
    } catch (err) {
      console.error('Error classifying documents:', err);
      setClassificationError(err.response?.data?.detail || '分類処理中にエラーが発生しました');
      stopProgressPolling();
      setClassificationLoading(false);
      return false;
    }
  };
  
  const closeProgressModal = () => {
    setShowProgressModal(false);
  };
  
  const value = {
    classificationLoading,
    classificationError,
    classificationProgress,
    showProgressModal,
    startClassification,
    closeProgressModal,
  };
  
  return (
    <ProcessContext.Provider value={value}>
      {children}
    </ProcessContext.Provider>
  );
};

export const useProcess = () => {
  const context = useContext(ProcessContext);
  if (!context) {
    throw new Error('useProcess must be used within a ProcessProvider');
  }
  return context;
};

ProcessProvider.propTypes = {
  children: PropTypes.node.isRequired
};

export default ProcessContext;

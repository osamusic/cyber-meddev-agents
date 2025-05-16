import React, { createContext, useState, useContext, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import axiosClient from '../api/axiosClient';

const ProcessContext = createContext(null);

export const ProcessProvider = ({ children }) => {
  const [classificationLoading, setClassificationLoading] = useState(false);
  const [classificationError, setClassificationError] = useState(null);
  const [classificationProgress, setClassificationProgress] = useState(null);
  const [showProgressModal, setShowProgressModal] = useState(false);

  const pollIntervalRef = useRef(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const startProgressPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    pollIntervalRef.current = setInterval(async () => {
      try {
        const res = await axiosClient.get('/classifier/progress');
        setClassificationProgress(res.data);

        if (['completed', 'error'].includes(res.data.status)) {
          stopProgressPolling();
          setClassificationLoading(false);
        }
      } catch (err) {
        console.error('Error retrieving progress:', err);
        stopProgressPolling();
        setClassificationError('Failed to retrieve progress');
        setClassificationLoading(false);
      }
    }, 5000);
  };

  const stopProgressPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  const startClassification = async (requestData) => {
    try {
      setClassificationLoading(true);
      setClassificationError(null);
      setClassificationProgress(null);

      await axiosClient.post('/classifier/classify', requestData);

      startProgressPolling();
      return true;
    } catch (err) {
      console.error('Classification error:', err);
      setClassificationError(
        err.response?.data?.detail || 'An error occurred during classification process'
      );
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

  return <ProcessContext.Provider value={value}>{children}</ProcessContext.Provider>;
};

export const useProcess = () => {
  const context = useContext(ProcessContext);
  if (!context) {
    throw new Error('useProcess must be used within a ProcessProvider');
  }
  return context;
};

ProcessProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

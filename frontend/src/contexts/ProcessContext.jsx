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

  // クリーンアップ
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);



  const startClassificationProgressPolling = () => {
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
        console.error('進捗取得エラー:', err);
        stopProgressPolling();
        setClassificationError('進捗取得に失敗しました');
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

      startClassificationProgressPolling();
      return true;
    } catch (err) {
      console.error('分類エラー:', err);
      setClassificationError(
        err.response?.data?.detail || '分類処理中にエラーが発生しました'
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

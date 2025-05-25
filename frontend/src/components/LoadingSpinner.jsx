import React from 'react';

const LoadingSpinner = ({ message = 'Загрузка...' }) => {
  return (
    <div className="loading-screen">
      <div className="loading-spinner"></div>
      <p className="text-muted">{message}</p>
    </div>
  );
};

export default LoadingSpinner;
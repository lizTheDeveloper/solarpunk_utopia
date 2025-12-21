import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  text = 'Loading...' 
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8', 
    lg: 'w-12 h-12'
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem'
    }}>
      <div 
        className={`${sizeClasses[size]} animate-spin`}
        style={{
          width: size === 'sm' ? '1rem' : size === 'md' ? '2rem' : '3rem',
          height: size === 'sm' ? '1rem' : size === 'md' ? '2rem' : '3rem',
          border: '2px solid #e5e7eb',
          borderTop: '2px solid #10b981',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}
      />
      {text && (
        <p style={{
          marginTop: '1rem',
          color: '#6b7280',
          fontSize: '0.875rem'
        }}>
          {text}
        </p>
      )}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

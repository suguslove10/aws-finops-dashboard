'use client';

import { useState } from 'react';
import { FaExclamationTriangle, FaSyncAlt } from 'react-icons/fa';
import { LoadingSpinner } from './LoadingSpinner';

interface ErrorFeedbackProps {
  title: string;
  message: string;
  onRetry?: () => Promise<void>;
  icon?: React.ReactNode;
  color?: 'red' | 'yellow' | 'blue';
}

export function ErrorFeedback({
  title,
  message,
  onRetry,
  icon = <FaExclamationTriangle className="text-red-600 dark:text-red-400" />,
  color = 'red'
}: ErrorFeedbackProps) {
  const [isRetrying, setIsRetrying] = useState(false);

  const colorClasses = {
    red: {
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-200 dark:border-red-800/50',
      title: 'text-red-800 dark:text-red-300',
      message: 'text-red-600 dark:text-red-400',
      iconBg: 'bg-red-100 dark:bg-red-800/50',
      button: 'bg-red-100 dark:bg-red-800/60 hover:bg-red-200 dark:hover:bg-red-800 text-red-700 dark:text-red-300'
    },
    yellow: {
      bg: 'bg-yellow-50 dark:bg-yellow-900/20',
      border: 'border-yellow-200 dark:border-yellow-800/50',
      title: 'text-yellow-800 dark:text-yellow-300',
      message: 'text-yellow-600 dark:text-yellow-400',
      iconBg: 'bg-yellow-100 dark:bg-yellow-800/50',
      button: 'bg-yellow-100 dark:bg-yellow-800/60 hover:bg-yellow-200 dark:hover:bg-yellow-800 text-yellow-700 dark:text-yellow-300'
    },
    blue: {
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      border: 'border-blue-200 dark:border-blue-800/50',
      title: 'text-blue-800 dark:text-blue-300',
      message: 'text-blue-600 dark:text-blue-400',
      iconBg: 'bg-blue-100 dark:bg-blue-800/50',
      button: 'bg-blue-100 dark:bg-blue-800/60 hover:bg-blue-200 dark:hover:bg-blue-800 text-blue-700 dark:text-blue-300'
    }
  };

  const classes = colorClasses[color];

  const handleRetry = async () => {
    if (!onRetry) return;

    setIsRetrying(true);
    try {
      await onRetry();
    } catch (error) {
      console.error('Retry failed:', error);
    } finally {
      setIsRetrying(false);
    }
  };

  return (
    <div 
      className={`${classes.bg} p-5 rounded-lg border ${classes.border} mb-6 shadow-sm animate-fade-in`}
    >
      <div className="flex items-start">
        <div className={`${classes.iconBg} p-3 rounded-full mr-3 shrink-0`}>
          {icon}
        </div>
        <div>
          <h3 className={`font-medium ${classes.title} mb-2`}>{title}</h3>
          <p className={`text-sm ${classes.message} mb-3`}>
            {message}
          </p>
          {onRetry && (
            <button
              onClick={handleRetry}
              disabled={isRetrying}
              className={`flex items-center text-sm px-4 py-2 ${classes.button} rounded-full transition-all hover:scale-105 active:scale-95`}
            >
              {isRetrying ? (
                <>
                  <LoadingSpinner size="sm" color="primary" className="mr-2" />
                  <span>Retrying...</span>
                </>
              ) : (
                <>
                  <FaSyncAlt className="mr-2" />
                  <span>Retry</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
} 
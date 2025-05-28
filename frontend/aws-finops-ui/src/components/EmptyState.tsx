'use client';

import { motion } from 'framer-motion';
import { FaCloudDownloadAlt, FaPlus } from 'react-icons/fa';
import { ReactNode } from 'react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  color?: 'blue' | 'green' | 'yellow' | 'purple' | 'gray';
}

export function EmptyState({
  icon = <FaCloudDownloadAlt className="text-blue-500 dark:text-blue-400" />,
  title,
  message,
  actionLabel,
  onAction,
  color = 'blue'
}: EmptyStateProps) {
  
  const colorClasses = {
    blue: {
      bg: 'bg-blue-50 dark:bg-blue-900/10',
      border: 'border-blue-200 dark:border-blue-800/50',
      iconBg: 'bg-blue-100 dark:bg-blue-800/30',
      title: 'text-blue-700 dark:text-blue-300',
      message: 'text-blue-600 dark:text-blue-400',
      button: 'bg-blue-100 dark:bg-blue-800/40 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-800/60'
    },
    green: {
      bg: 'bg-green-50 dark:bg-green-900/10',
      border: 'border-green-200 dark:border-green-800/50',
      iconBg: 'bg-green-100 dark:bg-green-800/30',
      title: 'text-green-700 dark:text-green-300',
      message: 'text-green-600 dark:text-green-400',
      button: 'bg-green-100 dark:bg-green-800/40 text-green-700 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-800/60'
    },
    yellow: {
      bg: 'bg-yellow-50 dark:bg-yellow-900/10',
      border: 'border-yellow-200 dark:border-yellow-800/50',
      iconBg: 'bg-yellow-100 dark:bg-yellow-800/30',
      title: 'text-yellow-700 dark:text-yellow-300',
      message: 'text-yellow-600 dark:text-yellow-400',
      button: 'bg-yellow-100 dark:bg-yellow-800/40 text-yellow-700 dark:text-yellow-300 hover:bg-yellow-200 dark:hover:bg-yellow-800/60'
    },
    purple: {
      bg: 'bg-purple-50 dark:bg-purple-900/10',
      border: 'border-purple-200 dark:border-purple-800/50',
      iconBg: 'bg-purple-100 dark:bg-purple-800/30',
      title: 'text-purple-700 dark:text-purple-300',
      message: 'text-purple-600 dark:text-purple-400',
      button: 'bg-purple-100 dark:bg-purple-800/40 text-purple-700 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-800/60'
    },
    gray: {
      bg: 'bg-gray-50 dark:bg-gray-800/50',
      border: 'border-gray-200 dark:border-gray-700',
      iconBg: 'bg-gray-100 dark:bg-gray-700',
      title: 'text-gray-700 dark:text-gray-300',
      message: 'text-gray-600 dark:text-gray-400',
      button: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
    }
  };
  
  const classes = colorClasses[color];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`${classes.bg} p-6 rounded-xl border ${classes.border} text-center`}
    >
      <div className="flex flex-col items-center">
        <div className={`${classes.iconBg} p-4 rounded-full mb-4 inline-flex`}>
          {icon}
        </div>
        
        <h3 className={`text-lg font-semibold ${classes.title} mb-2`}>
          {title}
        </h3>
        
        <p className={`${classes.message} mb-6 max-w-md mx-auto text-sm`}>
          {message}
        </p>
        
        {actionLabel && onAction && (
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={onAction}
            className={`${classes.button} px-4 py-2 rounded-full text-sm font-medium inline-flex items-center transition-colors`}
          >
            <FaPlus className="mr-2 text-xs" />
            {actionLabel}
          </motion.button>
        )}
      </div>
    </motion.div>
  );
} 
'use client';

import { motion } from 'framer-motion';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'white' | 'gray';
  className?: string;
}

export function LoadingSpinner({ 
  size = 'md', 
  color = 'primary',
  className = '' 
}: LoadingSpinnerProps) {
  
  const getSizeClass = () => {
    switch(size) {
      case 'sm': return 'w-5 h-5';
      case 'lg': return 'w-10 h-10';
      case 'md':
      default: return 'w-8 h-8';
    }
  };
  
  const getColorClass = () => {
    switch(color) {
      case 'white': return 'text-white';
      case 'gray': return 'text-gray-400 dark:text-gray-500';
      case 'primary':
      default: return 'text-blue-600 dark:text-blue-400';
    }
  };
  
  return (
    <div className={`flex justify-center items-center ${className}`}>
      <motion.div
        className={`${getSizeClass()} ${getColorClass()}`}
        animate={{ rotate: 360 }}
        transition={{ 
          duration: 1.5, 
          repeat: Infinity, 
          ease: "linear" 
        }}
      >
        <svg 
          className="w-full h-full" 
          viewBox="0 0 24 24" 
          fill="none" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle 
            className="opacity-25" 
            cx="12" 
            cy="12" 
            r="10" 
            stroke="currentColor" 
            strokeWidth="4"
          />
          <path 
            className="opacity-75" 
            fill="currentColor" 
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      </motion.div>
    </div>
  );
} 
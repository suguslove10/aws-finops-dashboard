'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchTasks, Task } from '@/lib/api';
import { Card, Title, Text } from '@tremor/react';
import { FaCog, FaCloudDownloadAlt, FaChartLine, FaSearch, FaExclamationTriangle, FaClipboardCheck, FaMoneyBillWave } from 'react-icons/fa';
import { motion } from 'framer-motion';

interface TaskSelectorProps {
  onSelectTask: (task: Task) => void;
  selectedTaskId?: string;
}

export function TaskSelector({ onSelectTask, selectedTaskId }: TaskSelectorProps) {
  const { data: tasks, isLoading, error } = useQuery({
    queryKey: ['tasks'],
    queryFn: fetchTasks,
  });

  if (isLoading) {
    return (
      <Card className="mb-6 shadow-md border border-gray-200 dark:border-gray-700">
        <div className="p-4">
          <div className="animate-pulse h-7 w-48 bg-gray-200 dark:bg-gray-700 mb-4 rounded"></div>
          <div className="animate-pulse h-5 w-64 bg-gray-200 dark:bg-gray-700 mb-6 rounded"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="animate-pulse h-28 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 p-6 rounded-lg border border-red-200 dark:border-red-800/50 mb-6">
        <h3 className="text-red-800 dark:text-red-400 font-medium flex items-center">
          <FaExclamationTriangle className="mr-2" /> Error loading tasks
        </h3>
        <p className="text-red-600 dark:text-red-300 text-sm mt-2">
          Please check your connection to the API server.
        </p>
      </div>
    );
  }

  const getTaskIcon = (taskId: string) => {
    switch (taskId) {
      case 'dashboard':
        return <FaChartLine size={24} className="text-blue-500" />;
      case 'trend':
        return <FaChartLine size={24} className="text-green-500" />;
      case 'audit':
        return <FaClipboardCheck size={24} className="text-purple-500" />;
      case 'anomalies':
        return <FaExclamationTriangle size={24} className="text-yellow-500" />;
      case 'optimize':
        return <FaMoneyBillWave size={24} className="text-green-500" />;
      case 'ri_optimizer':
        return <FaCog size={24} className="text-blue-500" />;
      case 'resource_analyzer':
        return <FaSearch size={24} className="text-indigo-500" />;
      default:
        return <FaCloudDownloadAlt size={24} className="text-gray-500" />;
    }
  };
  
  const getTaskGradient = (taskId: string) => {
    switch (taskId) {
      case 'dashboard':
        return 'from-blue-500/20 to-blue-600/10';
      case 'trend':
        return 'from-green-500/20 to-green-600/10';
      case 'audit':
        return 'from-purple-500/20 to-purple-600/10';
      case 'anomalies':
        return 'from-yellow-500/20 to-yellow-600/10';
      case 'optimize':
        return 'from-green-500/20 to-blue-500/10';
      case 'ri_optimizer':
        return 'from-blue-500/20 to-indigo-600/10';
      case 'resource_analyzer':
        return 'from-indigo-500/20 to-indigo-600/10';
      default:
        return 'from-gray-200 to-gray-100 dark:from-gray-700/30 dark:to-gray-800/20';
    }
  };

  return (
    <Card className="mb-6 shadow-lg border border-gray-200 dark:border-gray-700 transition-all duration-300">
      <div className="px-2 py-4">
        <Title className="text-xl font-bold text-gray-900 dark:text-white">Select Task</Title>
        <Text className="mt-2 mb-4 text-gray-600 dark:text-gray-300">Choose the AWS FinOps task you want to run</Text>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
          {tasks?.map((task) => (
            <div
              key={task.id}
              onClick={() => onSelectTask(task)}
              className={`
                relative overflow-hidden p-5 rounded-xl cursor-pointer transition-all duration-300
                ${selectedTaskId === task.id 
                  ? 'ring-2 ring-blue-500 dark:ring-blue-400 shadow-md bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/10' 
                  : 'hover:shadow-md bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
                }
              `}
            >
              <motion.div
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                style={{ width: '100%' }}
              >
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-indigo-600 opacity-0 transition-opacity duration-300 ease-in-out"></div>
                
                <div className="flex items-start space-x-4">
                  <div className={`p-3 rounded-lg bg-gradient-to-br ${getTaskGradient(task.id)} flex items-center justify-center`}>
                    {getTaskIcon(task.id)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-1">{task.name}</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300">{task.description}</p>
                  </div>
                </div>
                
                {selectedTaskId === task.id && (
                  <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-indigo-600"></div>
                )}
              </motion.div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
} 
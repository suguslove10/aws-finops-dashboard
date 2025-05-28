'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchRegions } from '@/lib/api';
import { Card, Title, Text } from '@tremor/react';
import { FaGlobe, FaGlobeAmericas, FaGlobeAsia, FaGlobeEurope, FaMapMarkerAlt, FaExclamationTriangle, FaCheckCircle } from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorFeedback } from './ErrorFeedback';

interface RegionSelectorProps {
  selectedRegions: string[];
  onSelectRegions: (regions: string[]) => void;
}

export function RegionSelector({ selectedRegions, onSelectRegions }: RegionSelectorProps) {
  const { data: regions, isLoading, error } = useQuery({
    queryKey: ['regions'],
    queryFn: fetchRegions,
  });
  
  const [activeRegion, setActiveRegion] = useState<string | null>(null);

  const handleRegionChange = (region: string) => {
    if (selectedRegions.includes(region)) {
      onSelectRegions(selectedRegions.filter((r) => r !== region));
    } else {
      onSelectRegions([...selectedRegions, region]);
    }
  };

  const handleSelectAll = () => {
    if (regions && regions.length > 0) {
      if (selectedRegions.length === regions.length) {
        onSelectRegions([]);
      } else {
        onSelectRegions([...regions]);
      }
    }
  };
  
  const handleSelectGroup = (groupRegions: string[]) => {
    const filteredGroupRegions = groupRegions.filter(region => regions?.includes(region));
    const allSelected = filteredGroupRegions.every(region => selectedRegions.includes(region));
    
    if (allSelected) {
      // Deselect all regions in this group
      onSelectRegions(selectedRegions.filter(region => !filteredGroupRegions.includes(region)));
    } else {
      // Select all regions in this group that aren't already selected
      const newRegions = [...selectedRegions];
      filteredGroupRegions.forEach(region => {
        if (!newRegions.includes(region)) {
          newRegions.push(region);
        }
      });
      onSelectRegions(newRegions);
    }
  };

  // Group regions by geographic area
  const groupedRegions = {
    'North America': ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ca-central-1'],
    'Europe': ['eu-west-1', 'eu-west-2', 'eu-central-1'],
    'Asia Pacific': ['ap-northeast-1', 'ap-northeast-2', 'ap-southeast-1', 'ap-southeast-2', 'ap-south-1'],
    'South America': ['sa-east-1'],
  };
  
  const regionIcons = {
    'North America': <FaGlobeAmericas className="text-blue-600 dark:text-blue-400" />,
    'Europe': <FaGlobeEurope className="text-green-600 dark:text-green-400" />,
    'Asia Pacific': <FaGlobeAsia className="text-purple-600 dark:text-purple-400" />,
    'South America': <FaGlobeAmericas className="text-yellow-600 dark:text-yellow-400" />,
  };
  
  const regionColors = {
    'North America': 'bg-blue-500/10 border-blue-200 dark:border-blue-800/60 hover:bg-blue-500/20',
    'Europe': 'bg-green-500/10 border-green-200 dark:border-green-800/60 hover:bg-green-500/20',
    'Asia Pacific': 'bg-purple-500/10 border-purple-200 dark:border-purple-800/60 hover:bg-purple-500/20',
    'South America': 'bg-yellow-500/10 border-yellow-200 dark:border-yellow-800/60 hover:bg-yellow-500/20',
  };

  if (isLoading) {
    return (
      <Card className="mb-6 shadow-md border border-gray-200 dark:border-gray-700">
        <div className="p-6">
          <div className="flex items-center mb-6">
            <div className="animate-pulse h-8 w-8 bg-blue-200 dark:bg-blue-800 rounded-lg mr-3"></div>
            <div className="animate-pulse h-7 w-48 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
          <div className="animate-pulse h-5 w-64 bg-gray-200 dark:bg-gray-700 mb-6 rounded"></div>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-6 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-3"></div>
                <div className="grid grid-cols-2 gap-3">
                  {[...Array(4)].map((_, j) => (
                    <div key={j} className="h-10 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <ErrorFeedback
        title="Error loading AWS regions"
        message="Please check your connection to the API server."
      />
    );
  }

  return (
    <Card className="mb-6 shadow-md border border-gray-200 dark:border-gray-700 transition-all duration-300 hover:shadow-lg">
      <div className="px-2 py-4">
        <div className="flex items-center mb-2">
          <div className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 p-2 rounded-lg mr-3">
            <FaGlobe className="text-blue-600 dark:text-blue-400 text-xl" />
          </div>
          <Title className="text-xl font-bold text-gray-900 dark:text-white">AWS Regions</Title>
        </div>
        <Text className="mt-2 mb-5 text-gray-600 dark:text-gray-300">Select the AWS regions to include in the analysis</Text>

        <div className="flex flex-wrap justify-between items-center mb-4 gap-2">
          <div className="text-xs text-gray-500 dark:text-gray-400 font-medium">
            {selectedRegions.length} of {regions?.length} regions selected
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSelectAll}
            className="text-sm text-blue-700 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium flex items-center bg-white dark:bg-gray-800 px-4 py-2 rounded-full shadow-sm"
          >
            <FaMapMarkerAlt className="mr-2" />
            {selectedRegions.length === regions?.length ? 'Deselect All' : 'Select All'}
          </motion.button>
        </div>

        <div className="space-y-5">
          {Object.entries(groupedRegions).map(([group, groupRegions]) => {
            const filteredGroupRegions = groupRegions.filter(region => regions?.includes(region));
            const allGroupSelected = filteredGroupRegions.every(region => selectedRegions.includes(region));
            const someGroupSelected = filteredGroupRegions.some(region => selectedRegions.includes(region));
            const selectionState = allGroupSelected ? 'all' : someGroupSelected ? 'some' : 'none';
            const selectedCount = filteredGroupRegions.filter(region => selectedRegions.includes(region)).length;
            
            return (
              <motion.div 
                key={group}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className={`bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700 ${
                  activeRegion === group ? 'ring-2 ring-blue-500 dark:ring-blue-400' : ''
                }`}
              >
                <div className="flex flex-wrap items-center justify-between mb-3 gap-2">
                  <div className="flex items-center flex-grow min-w-0 mr-2">
                    <motion.button 
                      className="flex items-center group text-left"
                      onClick={() => setActiveRegion(activeRegion === group ? null : group)}
                    >
                      <span className="flex-shrink-0 mr-2 text-xl">
                        {regionIcons[group as keyof typeof regionIcons]}
                      </span>
                      <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                        {group}
                      </h3>
                    </motion.button>
                    
                    <div className="ml-2 text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                      {filteredGroupRegions.length} regions
                    </div>
                    
                    {someGroupSelected && (
                      <div className="ml-2 text-xs px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400">
                        {selectedCount}/{filteredGroupRegions.length} selected
                      </div>
                    )}
                  </div>
                  
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleSelectGroup(groupRegions)}
                    className={`
                      flex items-center justify-center w-7 h-7 rounded-md transition-colors flex-shrink-0
                      ${selectionState === 'all' 
                        ? 'bg-blue-500 text-white' 
                        : selectionState === 'some' 
                        ? 'bg-blue-200 dark:bg-blue-800 text-blue-700 dark:text-blue-300' 
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 hover:bg-blue-100 dark:hover:bg-blue-900/30'
                      }
                    `}
                    aria-label={allGroupSelected ? `Deselect all ${group} regions` : `Select all ${group} regions`}
                  >
                    {selectionState === 'all' ? <FaCheckCircle size={14} /> : selectionState === 'some' ? '-' : '+'}
                  </motion.button>
                </div>
                
                <AnimatePresence>
                  {(activeRegion === group || activeRegion === null) && (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.2 }}
                      className={`
                        grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 overflow-hidden
                        ${filteredGroupRegions.length > 6 && activeRegion === group ? 'max-h-60 overflow-y-auto pr-1 pb-1' : ''}
                      `}
                    >
                      {filteredGroupRegions.map((region, index) => (
                        <motion.div 
                          key={region}
                          initial={{ opacity: 0, y: 5 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.2, delay: index * 0.03 }}
                          onClick={() => handleRegionChange(region)}
                          className={`
                            flex items-center p-2.5 rounded-lg transition-all cursor-pointer
                            ${selectedRegions.includes(region)
                              ? regionColors[group as keyof typeof regionColors] || 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800/60'
                              : 'bg-gray-50 dark:bg-gray-800/80 border border-gray-200 dark:border-gray-700 hover:border-blue-200 dark:hover:border-blue-800/60'
                            }
                          `}
                        >
                          <div className="relative flex items-center justify-center flex-shrink-0">
                            <input
                              type="checkbox"
                              id={`region-${region}`}
                              className="sr-only"
                              checked={selectedRegions.includes(region)}
                              onChange={() => {}} // handled by parent div click
                            />
                            <div 
                              className={`
                                h-5 w-5 flex items-center justify-center rounded transition-colors duration-200
                                ${selectedRegions.includes(region)
                                  ? 'bg-blue-600 border-blue-600 dark:bg-blue-500 dark:border-blue-500'
                                  : 'border border-gray-300 dark:border-gray-600'
                                }
                              `}
                            >
                              {selectedRegions.includes(region) && (
                                <FaCheckCircle className="text-white text-xs" />
                              )}
                            </div>
                          </div>
                          <label 
                            htmlFor={`region-${region}`} 
                            className="ml-3 text-sm text-gray-800 dark:text-gray-200 font-medium cursor-pointer truncate"
                          >
                            {region}
                          </label>
                        </motion.div>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      </div>
    </Card>
  );
} 
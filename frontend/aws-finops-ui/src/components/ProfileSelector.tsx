'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchProfiles, AwsProfile, fetchProfileDetails } from '@/lib/api';
import { Card, Title, Text, Switch } from '@tremor/react';
import { FaAws, FaUser, FaExclamationTriangle, FaSyncAlt, FaCheck, FaInfoCircle, FaPlus } from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorFeedback } from './ErrorFeedback';
import { AddCredentialsModal } from './AddCredentialsModal';

interface ProfileSelectorProps {
  selectedProfiles: string[];
  onSelectProfiles: (profiles: string[]) => void;
  combineProfiles: boolean;
  onCombineProfiles: (combine: boolean) => void;
}

export function ProfileSelector({
  selectedProfiles,
  onSelectProfiles,
  combineProfiles,
  onCombineProfiles,
}: ProfileSelectorProps) {
  const [isRetrying, setIsRetrying] = useState(false);
  const [showDetailedView, setShowDetailedView] = useState(false);
  const [hoveredProfile, setHoveredProfile] = useState<string | null>(null);
  const [profileDetails, setProfileDetails] = useState<Record<string, any>>({});
  const [isAddCredentialsModalOpen, setIsAddCredentialsModalOpen] = useState(false);
  
  const { 
    data: profiles, 
    isLoading, 
    error, 
    refetch 
  } = useQuery({
    queryKey: ['profiles', showDetailedView],
    queryFn: () => fetchProfiles(showDetailedView),
    retry: 1
  });
  
  // If detailed view fails, switch back to simple view
  useEffect(() => {
    if (error && showDetailedView) {
      console.error("Error fetching detailed profiles, falling back to simple view:", error);
      setShowDetailedView(false);
    }
  }, [error, showDetailedView]);

  const handleRetry = async () => {
    setIsRetrying(true);
    await refetch();
    setIsRetrying(false);
  };

  const handleToggleProfile = (profileName: string) => {
    if (selectedProfiles.includes(profileName)) {
      onSelectProfiles(selectedProfiles.filter((p) => p !== profileName));
    } else {
      onSelectProfiles([...selectedProfiles, profileName]);
    }
  };
  
  const handleSelectAll = () => {
    if (profiles && Array.isArray(profiles)) {
      if (typeof profiles[0] === 'string') {
        onSelectProfiles(profiles as string[]);
      } else {
        onSelectProfiles((profiles as AwsProfile[]).map(p => p.name));
      }
    }
  };
  
  const handleClearAll = () => {
    onSelectProfiles([]);
  };
  
  const loadProfileDetails = async (profileName: string) => {
    if (!profileDetails[profileName]) {
      try {
        const details = await fetchProfileDetails(profileName);
        setProfileDetails(prev => ({
          ...prev,
          [profileName]: details
        }));
      } catch (error) {
        console.error(`Error loading details for ${profileName}:`, error);
        setProfileDetails(prev => ({
          ...prev,
          [profileName]: { error: 'Failed to load profile details' }
        }));
      }
    }
  };

  // Format account ID for display (show last 4 digits)
  const formatAccountId = (accountId: string) => {
    if (!accountId) return '—';
    return `••••${accountId.slice(-4)}`;
  };
  
  const getProfileStatus = (profile: AwsProfile) => {
    switch (profile.status) {
      case 'active':
        return (
          <span className="flex items-center text-green-600 dark:text-green-400 text-xs font-medium">
            <FaCheck className="mr-1" /> Active
          </span>
        );
      case 'expired':
        return (
          <span className="flex items-center text-amber-600 dark:text-amber-400 text-xs font-medium">
            <FaExclamationTriangle className="mr-1" /> Expired
          </span>
        );
      case 'access_denied':
        return (
          <span className="flex items-center text-red-600 dark:text-red-400 text-xs font-medium">
            <FaExclamationTriangle className="mr-1" /> Access Denied
          </span>
        );
      default:
        return (
          <span className="flex items-center text-red-600 dark:text-red-400 text-xs font-medium">
            <FaExclamationTriangle className="mr-1" /> Error
          </span>
        );
    }
  };

  if (isLoading) {
    return (
      <Card className="mb-6 shadow-md border border-gray-200 dark:border-gray-700">
        <div className="p-6">
          <div className="flex items-center mb-4">
            <div className="animate-pulse h-8 w-8 bg-blue-200 dark:bg-blue-800 rounded-lg mr-3"></div>
            <div className="animate-pulse h-7 w-40 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
          <div className="animate-pulse h-5 w-64 bg-gray-200 dark:bg-gray-700 mb-6 rounded"></div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse h-12 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="mb-6 shadow-md border border-gray-200 dark:border-gray-700">
        <div className="px-2 py-4">
          <div className="flex items-center mb-2">
            <div className="bg-gradient-to-br from-red-500/20 to-red-600/10 p-2 rounded-lg mr-3">
              <FaAws className="text-red-600 dark:text-red-400 text-xl" />
            </div>
            <Title className="text-xl font-bold text-gray-900 dark:text-white">AWS Profiles</Title>
          </div>
          
          <ErrorFeedback
            title="Error loading AWS profiles"
            message="Please check your AWS configuration and credentials."
            onRetry={handleRetry}
            color="red"
          />
        </div>
      </Card>
    );
  }

  return (
    <>
      <Card className="mb-6 shadow-md border border-gray-200 dark:border-gray-700 transition-all duration-300 hover:shadow-lg">
        <div className="px-2 py-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center">
              <div className="bg-gradient-to-br from-blue-500/20 to-indigo-600/10 p-2 rounded-lg mr-3">
                <FaAws className="text-blue-600 dark:text-blue-400 text-xl" />
              </div>
              <Title className="text-xl font-bold text-gray-900 dark:text-white">AWS Profiles</Title>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowDetailedView(!showDetailedView)}
                className={`
                  text-xs px-2 py-1 rounded flex items-center gap-1
                  transition-colors
                  ${showDetailedView 
                    ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' 
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'}
                `}
              >
                <FaInfoCircle />
                {showDetailedView ? 'Simple View' : 'Detailed View'}
              </button>
            </div>
          </div>
          
          <Text className="mt-2 mb-3 text-gray-600 dark:text-gray-300">
            Select AWS profiles to include in the analysis
          </Text>
          
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center space-x-2">
              <button 
                onClick={handleSelectAll}
                className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
              >
                Select All
              </button>
              <span className="text-gray-300 dark:text-gray-600">|</span>
              <button 
                onClick={handleClearAll}
                className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
              >
                Clear
              </button>
            </div>
            
            <div className="flex items-center">
              <Switch
                id="combine-profiles"
                name="combine-profiles"
                checked={combineProfiles}
                onChange={onCombineProfiles}
                color="blue"
                className="mr-2"
              />
              <label htmlFor="combine-profiles" className="text-sm text-gray-600 dark:text-gray-400">
                Combine profiles from same account
              </label>
            </div>
          </div>
          
          {/* Add button for adding new credentials */}
          <button
            onClick={() => setIsAddCredentialsModalOpen(true)}
            className="flex items-center mb-4 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <FaPlus className="mr-2" />
            Add AWS Credentials
          </button>
          
          <div className="space-y-3 mt-4">
            {profiles && profiles.length > 0 ? (
              <>
                {showDetailedView ? (
                  // Detailed view with account info
                  (profiles as AwsProfile[]).map((profile) => (
                    <motion.div
                      key={profile.name}
                      whileHover={{ scale: 1.01, transition: { duration: 0.2 } }}
                      className={`
                        relative p-3 rounded-lg border cursor-pointer
                        ${selectedProfiles.includes(profile.name)
                          ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800/50'
                          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-blue-200 dark:hover:border-blue-800/30'}
                      `}
                      onClick={() => handleToggleProfile(profile.name)}
                      onMouseEnter={() => setHoveredProfile(profile.name)}
                      onMouseLeave={() => setHoveredProfile(null)}
                    >
                      <div className="flex justify-between items-center">
                        <div className="flex items-center space-x-3">
                          <div className={`
                            h-10 w-10 rounded-full flex items-center justify-center text-white
                            ${profile.status === 'active' 
                              ? 'bg-gradient-to-br from-blue-500 to-indigo-600' 
                              : 'bg-gradient-to-br from-gray-500 to-gray-600'}
                          `}>
                            <FaUser />
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white">
                              {profile.name}
                            </p>
                            <div className="flex items-center mt-1">
                              {getProfileStatus(profile)}
                              
                              {profile.account_id && (
                                <div className="ml-3 text-xs text-gray-500 dark:text-gray-400 flex items-center">
                                  <span className="font-mono">{formatAccountId(profile.account_id)}</span>
                                </div>
                              )}
                              
                              {profile.username && (
                                <div className="ml-3 text-xs text-gray-500 dark:text-gray-400 flex items-center">
                                  <FaUser className="mr-1 text-gray-400 dark:text-gray-500" size={10} />
                                  <span>{profile.username}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center">
                          {profile.status === 'active' && profile.regions && (
                            <span className="text-xs text-gray-500 dark:text-gray-400 mr-3">
                              {profile.regions.length} regions
                            </span>
                          )}
                          
                          <div className={`
                            h-5 w-5 rounded-full border-2 flex items-center justify-center transition-colors
                            ${selectedProfiles.includes(profile.name)
                              ? 'border-blue-500 bg-blue-500 dark:border-blue-400 dark:bg-blue-400'
                              : 'border-gray-300 dark:border-gray-600'}
                          `}>
                            {selectedProfiles.includes(profile.name) && (
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 text-white" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      {/* Error message if applicable */}
                      {profile.error && (
                        <div className="mt-2 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded border border-red-200 dark:border-red-800/30">
                          {profile.error}
                        </div>
                      )}
                      
                      {/* Show quick info on hover */}
                      {hoveredProfile === profile.name && profile.status === 'active' && (
                        <AnimatePresence>
                          <motion.div
                            initial={{ opacity: 0, y: 5 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 5 }}
                            className="absolute top-full left-0 mt-2 z-10 bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 w-72"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">Profile Info</p>
                            {profile.regions && (
                              <div className="mb-1">
                                <p className="text-xs text-gray-500 dark:text-gray-400">Available Regions:</p>
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {profile.regions.slice(0, 5).map(region => (
                                    <span key={region} className="text-xs bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">
                                      {region}
                                    </span>
                                  ))}
                                  {profile.regions.length > 5 && (
                                    <span className="text-xs bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">
                                      +{profile.regions.length - 5} more
                                    </span>
                                  )}
                                </div>
                              </div>
                            )}
                            {profile.account_id && (
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                Account ID: <span className="font-mono">{profile.account_id}</span>
                              </p>
                            )}
                          </motion.div>
                        </AnimatePresence>
                      )}
                    </motion.div>
                  ))
                ) : (
                  // Simple list view
                  (profiles as string[]).map((profile) => (
                    <motion.div
                      key={profile}
                      whileHover={{ scale: 1.01, transition: { duration: 0.2 } }}
                      className={`
                        p-3 rounded-lg border cursor-pointer flex justify-between items-center
                        ${selectedProfiles.includes(profile)
                          ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800/50'
                          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-blue-200 dark:hover:border-blue-800/30'}
                      `}
                      onClick={() => handleToggleProfile(profile)}
                    >
                      <span className="font-medium text-gray-800 dark:text-gray-200">{profile}</span>
                      <div className={`
                        h-5 w-5 rounded-full border-2 flex items-center justify-center transition-colors
                        ${selectedProfiles.includes(profile)
                          ? 'border-blue-500 bg-blue-500 dark:border-blue-400 dark:bg-blue-400'
                          : 'border-gray-300 dark:border-gray-600'}
                      `}>
                        {selectedProfiles.includes(profile) && (
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 text-white" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                    </motion.div>
                  ))
                )}
              </>
            ) : (
              <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
                <p className="text-gray-500 dark:text-gray-400">No AWS profiles found.</p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Make sure you have AWS CLI configured with profiles.
                </p>
              </div>
            )}
          </div>
          
          {selectedProfiles.length > 0 && (
            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/10 rounded-lg border border-blue-200 dark:border-blue-800/30">
              <p className="text-sm text-blue-800 dark:text-blue-300">
                {selectedProfiles.length} profile{selectedProfiles.length > 1 ? 's' : ''} selected
              </p>
            </div>
          )}
          
          {isRetrying && (
            <div className="flex justify-center mt-4">
              <LoadingSpinner size="sm" />
            </div>
          )}
        </div>
      </Card>
      
      {/* Add credentials modal */}
      <AddCredentialsModal 
        isOpen={isAddCredentialsModalOpen}
        onClose={() => setIsAddCredentialsModalOpen(false)}
        onSuccess={() => refetch()}
      />
    </>
  );
} 
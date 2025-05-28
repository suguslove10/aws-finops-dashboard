'use client';

import { useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { Button } from '@tremor/react';
import { FaAws, FaTimes } from 'react-icons/fa';
import api from '@/lib/api';

interface AddCredentialsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function AddCredentialsModal({ isOpen, onClose, onSuccess }: AddCredentialsModalProps) {
  const [profileName, setProfileName] = useState('');
  const [accessKey, setAccessKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [region, setRegion] = useState('us-east-1');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');
    
    try {
      console.log('Submitting credentials for profile:', profileName);
      const response = await api.post('/profiles/add', {
        profile_name: profileName,
        aws_access_key_id: accessKey,
        aws_secret_access_key: secretKey,
        region: region
      });
      
      console.log('Credentials added successfully:', response.data);
      setSuccess(true);
      setTimeout(() => {
        resetForm();
        onSuccess();
        onClose();
      }, 1500);
    } catch (err: any) {
      console.error('Error adding credentials:', err);
      const errorMessage = err.response?.data?.error || 
                           (err.message ? `Request failed: ${err.message}` : 
                           'Failed to add credentials');
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setProfileName('');
    setAccessKey('');
    setSecretKey('');
    setRegion('us-east-1');
    setError('');
    setSuccess(false);
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/25 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white dark:bg-gray-800 p-6 shadow-xl transition-all">
                <div className="absolute top-4 right-4">
                  <button
                    type="button"
                    className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
                    onClick={onClose}
                  >
                    <FaTimes className="h-5 w-5" />
                  </button>
                </div>

                <div className="flex items-center mb-4">
                  <div className="bg-blue-100 dark:bg-blue-900/30 p-2 rounded-lg mr-3">
                    <FaAws className="text-blue-600 dark:text-blue-400 h-6 w-6" />
                  </div>
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-medium leading-6 text-gray-900 dark:text-white"
                  >
                    Add AWS Credentials
                  </Dialog.Title>
                </div>

                {success ? (
                  <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800/30 rounded-lg p-4 mb-4">
                    <p className="text-green-700 dark:text-green-300">
                      AWS credentials added successfully!
                    </p>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit}>
                    {error && (
                      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/30 rounded-lg p-4 mb-4">
                        <p className="text-red-700 dark:text-red-300 font-medium mb-1">Failed to add credentials</p>
                        <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
                        
                        {error.includes('permission') && (
                          <div className="mt-2 text-sm text-gray-700 dark:text-gray-300">
                            <p className="font-medium">Possible solutions:</p>
                            <ul className="list-disc pl-5 mt-1 space-y-1">
                              <li>Run the AWS FinOps Dashboard with appropriate permissions</li>
                              <li>Manually create the AWS credentials file with correct permissions</li>
                              <li>Check if the <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">~/.aws</code> directory exists and is writable</li>
                            </ul>
                          </div>
                        )}
                      </div>
                    )}

                    <div className="mb-4">
                      <label
                        htmlFor="profileName"
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                      >
                        Profile Name
                      </label>
                      <input
                        type="text"
                        id="profileName"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                        placeholder="e.g., my-aws-profile"
                        value={profileName}
                        onChange={(e) => setProfileName(e.target.value)}
                        required
                      />
                    </div>

                    <div className="mb-4">
                      <label
                        htmlFor="accessKey"
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                      >
                        AWS Access Key ID
                      </label>
                      <input
                        type="text"
                        id="accessKey"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white font-mono"
                        placeholder="AKIAXXXXXXXXXXXXXXXX"
                        value={accessKey}
                        onChange={(e) => setAccessKey(e.target.value)}
                        required
                      />
                    </div>

                    <div className="mb-4">
                      <label
                        htmlFor="secretKey"
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                      >
                        AWS Secret Access Key
                      </label>
                      <input
                        type="password"
                        id="secretKey"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white font-mono"
                        placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                        value={secretKey}
                        onChange={(e) => setSecretKey(e.target.value)}
                        required
                      />
                    </div>

                    <div className="mb-6">
                      <label
                        htmlFor="region"
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                      >
                        Default Region
                      </label>
                      <select
                        id="region"
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                        value={region}
                        onChange={(e) => setRegion(e.target.value)}
                      >
                        <option value="us-east-1">US East (N. Virginia)</option>
                        <option value="us-east-2">US East (Ohio)</option>
                        <option value="us-west-1">US West (N. California)</option>
                        <option value="us-west-2">US West (Oregon)</option>
                        <option value="ca-central-1">Canada (Central)</option>
                        <option value="eu-west-1">EU (Ireland)</option>
                        <option value="eu-central-1">EU (Frankfurt)</option>
                        <option value="eu-west-2">EU (London)</option>
                        <option value="ap-south-1">Asia Pacific (Mumbai)</option>
                        <option value="ap-northeast-2">Asia Pacific (Seoul)</option>
                        <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
                        <option value="ap-southeast-2">Asia Pacific (Sydney)</option>
                        <option value="ap-northeast-1">Asia Pacific (Tokyo)</option>
                        <option value="sa-east-1">South America (São Paulo)</option>
                      </select>
                    </div>

                    <div className="flex justify-end space-x-3">
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={onClose}
                        disabled={isSubmitting}
                      >
                        Cancel
                      </Button>
                      <Button
                        type="submit"
                        loading={isSubmitting}
                        loadingText="Adding..."
                      >
                        Add Credentials
                      </Button>
                    </div>
                  </form>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
} 
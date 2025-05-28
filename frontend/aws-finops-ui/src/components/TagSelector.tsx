'use client';

import { useState } from 'react';
import { Card, Title, Text } from '@tremor/react';
import { FaTags, FaPlus, FaTimes } from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';

interface TagSelectorProps {
  selectedTags: string[];
  onSelectTags: (tags: string[]) => void;
}

export function TagSelector({ selectedTags, onSelectTags }: TagSelectorProps) {
  const [newTagKey, setNewTagKey] = useState('');
  const [newTagValue, setNewTagValue] = useState('');
  
  const handleAddTag = () => {
    if (newTagKey && newTagValue) {
      const newTag = `${newTagKey}=${newTagValue}`;
      if (!selectedTags.includes(newTag)) {
        onSelectTags([...selectedTags, newTag]);
      }
      setNewTagKey('');
      setNewTagValue('');
    }
  };
  
  const handleRemoveTag = (tagToRemove: string) => {
    onSelectTags(selectedTags.filter(tag => tag !== tagToRemove));
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAddTag();
    }
  };
  
  return (
    <Card className="mb-6 shadow-md border border-gray-200 dark:border-gray-700 transition-all duration-300 hover:shadow-lg">
      <div className="px-2 py-4">
        <div className="flex items-center mb-2">
          <div className="bg-gradient-to-br from-purple-500/20 to-indigo-600/10 p-2 rounded-lg mr-3">
            <FaTags className="text-purple-600 dark:text-purple-400 text-xl" />
          </div>
          <Title className="text-xl font-bold text-gray-900 dark:text-white">Cost Allocation Tags</Title>
        </div>
        <Text className="mt-2 mb-4 text-gray-600 dark:text-gray-300">
          Filter analysis by specific cost allocation tags (e.g., Team=DevOps, Environment=Production)
        </Text>
        
        <div className="mb-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="tagKey" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tag Key
            </label>
            <input
              type="text"
              id="tagKey"
              placeholder="e.g., Team, Environment, Project"
              value={newTagKey}
              onChange={(e) => setNewTagKey(e.target.value)}
              onKeyPress={handleKeyPress}
              className="block w-full rounded-lg border-gray-300 dark:border-gray-600 shadow-sm focus:border-purple-500 focus:ring-purple-500 dark:bg-gray-700 dark:text-white sm:text-sm transition-colors duration-200"
            />
          </div>
          <div>
            <label htmlFor="tagValue" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tag Value
            </label>
            <div className="flex">
              <input
                type="text"
                id="tagValue"
                placeholder="e.g., DevOps, Production, Phoenix"
                value={newTagValue}
                onChange={(e) => setNewTagValue(e.target.value)}
                onKeyPress={handleKeyPress}
                className="block w-full rounded-l-lg border-gray-300 dark:border-gray-600 shadow-sm focus:border-purple-500 focus:ring-purple-500 dark:bg-gray-700 dark:text-white sm:text-sm transition-colors duration-200"
              />
              <button
                onClick={handleAddTag}
                disabled={!newTagKey || !newTagValue}
                className={`px-3 rounded-r-lg flex items-center justify-center ${
                  !newTagKey || !newTagValue
                    ? 'bg-gray-300 dark:bg-gray-600 cursor-not-allowed'
                    : 'bg-purple-600 hover:bg-purple-700 dark:bg-purple-700 dark:hover:bg-purple-800 text-white'
                }`}
              >
                <FaPlus />
              </button>
            </div>
          </div>
        </div>
        
        {selectedTags.length > 0 && (
          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Selected Tags:</h3>
            <div className="flex flex-wrap gap-2">
              <AnimatePresence>
                {selectedTags.map((tag) => (
                  <motion.div
                    key={tag}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 border border-purple-200 dark:border-purple-800/50"
                  >
                    <span className="text-sm">{tag}</span>
                    <button
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-1 text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-200 focus:outline-none"
                    >
                      <FaTimes size={12} />
                    </button>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        )}
        
        {selectedTags.length === 0 && (
          <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 text-sm">
            No tags selected. Add tags to filter your analysis by specific cost allocation tags.
          </div>
        )}
      </div>
    </Card>
  );
} 
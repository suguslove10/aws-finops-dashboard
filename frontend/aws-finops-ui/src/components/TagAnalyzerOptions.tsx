'use client';

import { useState, useEffect } from 'react';
import { Card, Title, Text, Select, SelectItem, Button, Grid, TextInput } from '@tremor/react';
import { FaTags, FaPlus, FaTrash, FaInfoCircle } from 'react-icons/fa';

interface TagAnalyzerOptionsProps {
  onSubmit: (options: TagAnalyzerOptions) => void;
}

export interface TagAnalyzerOptions {
  tags: Array<{ key: string, value: string }>;
  timeRange: number;
  reportFormat: string[];
  currency: string;
}

export default function TagAnalyzerOptions({ onSubmit }: TagAnalyzerOptionsProps) {
  const [tags, setTags] = useState<Array<{ key: string, value: string }>>([{ key: '', value: '' }]);
  const [timeRange, setTimeRange] = useState<number>(30);
  const [reportFormat, setReportFormat] = useState<string[]>(['csv']);
  const [currency, setCurrency] = useState<string>('USD');
  
  // Load saved preferences from localStorage on component mount
  useEffect(() => {
    const savedCurrency = localStorage.getItem('selectedCurrency');
    if (savedCurrency) {
      setCurrency(savedCurrency);
    }
    
    const savedTimeRange = localStorage.getItem('timeRange');
    if (savedTimeRange) {
      setTimeRange(parseInt(savedTimeRange));
    }
  }, []);
  
  const handleSubmit = () => {
    // Save preferences to localStorage
    localStorage.setItem('selectedCurrency', currency);
    localStorage.setItem('timeRange', timeRange.toString());
    
    // Filter out empty tags
    const filteredTags = tags.filter(tag => tag.key.trim() !== '');
    
    onSubmit({
      tags: filteredTags,
      timeRange,
      reportFormat,
      currency
    });
  };

  const addTag = () => {
    setTags([...tags, { key: '', value: '' }]);
  };

  const removeTag = (index: number) => {
    const updatedTags = [...tags];
    updatedTags.splice(index, 1);
    setTags(updatedTags);
  };

  const updateTag = (index: number, field: 'key' | 'value', value: string) => {
    const updatedTags = [...tags];
    updatedTags[index][field] = value;
    setTags(updatedTags);
  };

  const toggleFormat = (format: string) => {
    if (reportFormat.includes(format)) {
      setReportFormat(reportFormat.filter(f => f !== format));
    } else {
      setReportFormat([...reportFormat, format]);
    }
  };

  return (
    <Card className="space-y-6" id="tag-analyzer-form">
      <div className="flex items-center gap-2 mb-4">
        <FaTags className="text-blue-500" />
        <Title className="text-lg font-semibold">Tag-Based Cost Analysis</Title>
      </div>
      
      <Text className="text-sm text-gray-600 dark:text-gray-400">
        Analyze your AWS costs based on specific tags. This helps you understand costs by projects, teams, environments, or any other tag-based categorization you use.
      </Text>
      
      <Card className="p-4 shadow-md">
        <Title className="text-lg font-semibold mb-4">Tags</Title>
        <Text className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Select the tags to analyze. You can add multiple tags to filter and group costs.
        </Text>
        
        {tags.map((tag, index) => (
          <div key={index} className="flex items-center gap-2 mb-4">
            <div className="flex-1">
              <TextInput
                placeholder="Tag Key (e.g., Environment, Project)"
                value={tag.key}
                onChange={(e) => updateTag(index, 'key', e.target.value)}
                className="mb-2"
              />
            </div>
            <div className="flex-1">
              <TextInput
                placeholder="Tag Value (optional, e.g., Production)"
                value={tag.value}
                onChange={(e) => updateTag(index, 'value', e.target.value)}
              />
            </div>
            <Button
              color="red"
              size="xs"
              icon={FaTrash}
              variant="light"
              tooltip="Remove tag"
              onClick={() => removeTag(index)}
              disabled={tags.length === 1}
            />
          </div>
        ))}
        
        <Button
          color="blue"
          size="xs"
          icon={FaPlus}
          variant="light"
          className="mt-2"
          onClick={addTag}
        >
          Add Another Tag
        </Button>
      </Card>

      <Card className="p-4 shadow-md">
        <Title className="text-lg font-semibold mb-4">Time Range</Title>
        <Text className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Set the time period for cost analysis.
        </Text>
        
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Time Range (days)
          </label>
          <div className="flex items-center">
            <input
              type="range"
              min="7"
              max="90"
              step="1"
              value={timeRange}
              onChange={(e) => setTimeRange(parseInt(e.target.value))}
              className="w-full h-2 bg-blue-100 rounded-lg appearance-none cursor-pointer dark:bg-blue-900/30"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 w-12 text-center">{timeRange}</span>
          </div>
          
          <div className="grid grid-cols-4 gap-2 mt-2">
            {[7, 14, 30, 90].map((days) => (
              <button
                key={days}
                onClick={() => setTimeRange(days)}
                className={`
                  text-xs py-1 px-2 rounded 
                  ${timeRange === days 
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' 
                    : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'}
                `}
              >
                {days} days
              </button>
            ))}
          </div>
        </div>
      </Card>

      <Card className="p-4 shadow-md">
        <Title className="text-lg font-semibold mb-4">Report Settings</Title>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Report Formats
          </label>
          <div className="flex flex-wrap gap-3">
            {['csv', 'json', 'pdf'].map((format) => (
              <button
                key={format}
                onClick={() => toggleFormat(format)}
                className={`
                  px-3 py-1.5 text-sm font-medium rounded-md
                  ${reportFormat.includes(format)
                    ? 'bg-blue-100 text-blue-700 border border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800/30'
                    : 'bg-gray-100 text-gray-700 border border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700'}
                `}
              >
                {format.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Currency
          </label>
          <Select
            value={currency}
            onValueChange={(value) => setCurrency(value)}
            className="w-full"
          >
            <SelectItem value="USD">USD (US Dollar)</SelectItem>
            <SelectItem value="INR">INR (Indian Rupee)</SelectItem>
            <SelectItem value="EUR">EUR (Euro)</SelectItem>
            <SelectItem value="GBP">GBP (British Pound)</SelectItem>
            <SelectItem value="JPY">JPY (Japanese Yen)</SelectItem>
            <SelectItem value="AUD">AUD (Australian Dollar)</SelectItem>
            <SelectItem value="CAD">CAD (Canadian Dollar)</SelectItem>
            <SelectItem value="CNY">CNY (Chinese Yuan)</SelectItem>
          </Select>
        </div>
      </Card>

      <div className="flex justify-end mt-6">
        <Button
          size="lg"
          color="blue"
          onClick={handleSubmit}
        >
          Run Analysis
        </Button>
      </div>
      
      <Card className="p-4 shadow-md bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800/20">
        <div className="flex items-start gap-2">
          <FaInfoCircle className="text-blue-500 mt-1" />
          <div>
            <Title className="text-sm font-semibold text-blue-700 dark:text-blue-300 mb-1">
              Tips for Tag Analysis
            </Title>
            <Text className="text-xs text-blue-600 dark:text-blue-400">
              1. Ensure your resources are properly tagged in AWS for accurate analysis.<br />
              2. Common tags include: Project, Environment, Team, Department, Cost Center.<br />
              3. If you leave the tag value empty, all resources with that tag key will be analyzed.
            </Text>
          </div>
        </div>
      </Card>
    </Card>
  );
} 
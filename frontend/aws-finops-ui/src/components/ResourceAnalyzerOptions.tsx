'use client';

import { useState } from 'react';
import { Card, Title, Text, Select, SelectItem, Divider, Button } from '@tremor/react';
import { FaServer, FaHdd, FaNetworkWired, FaDownload } from 'react-icons/fa';

interface ResourceAnalyzerOptionsProps {
  cpuThreshold: number;
  setCpuThreshold: (value: number) => void;
  lookbackDays: number;
  setLookbackDays: (value: number) => void;
}

export function ResourceAnalyzerOptions({
  cpuThreshold,
  setCpuThreshold,
  lookbackDays,
  setLookbackDays,
}: ResourceAnalyzerOptionsProps) {
  const [selectedResourceTypes, setSelectedResourceTypes] = useState<string[]>(['ec2', 'ebs', 'eip']);
  const [showDebugOutput, setShowDebugOutput] = useState(false);

  const resourceTypes = [
    { id: 'ec2', name: 'EC2 Instances', icon: <FaServer className="text-blue-500" /> },
    { id: 'ebs', name: 'EBS Volumes', icon: <FaHdd className="text-green-500" /> },
    { id: 'eip', name: 'Elastic IPs', icon: <FaNetworkWired className="text-purple-500" /> },
  ];

  const toggleResourceType = (type: string) => {
    if (selectedResourceTypes.includes(type)) {
      setSelectedResourceTypes(selectedResourceTypes.filter(t => t !== type));
    } else {
      setSelectedResourceTypes([...selectedResourceTypes, type]);
    }
  };

  const predefinedThresholds = [
    { value: 1, label: 'Very Low (1% - Most Aggressive)' },
    { value: 2, label: 'Low (2%)' },
    { value: 5, label: 'Standard (5%)' },
    { value: 10, label: 'Medium (10%)' },
    { value: 20, label: 'High (20%)' },
    { value: 40, label: 'Very High (40% - Most Conservative)' },
  ];

  return (
    <div className="space-y-6" id="resource-analyzer-form">
      <Card className="p-4 shadow-md">
        <Title className="text-lg font-semibold mb-4">Resource Types to Analyze</Title>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {resourceTypes.map((type) => (
            <div
              key={type.id}
              className={`
                flex items-center p-3 rounded-lg cursor-pointer transition-all
                ${selectedResourceTypes.includes(type.id)
                  ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800/50'
                  : 'bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700'}
              `}
            >
              <input 
                type="checkbox"
                name="resource-type"
                value={type.id}
                id={`resource-type-${type.id}`}
                checked={selectedResourceTypes.includes(type.id)}
                onChange={() => toggleResourceType(type.id)}
                className="mr-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label 
                htmlFor={`resource-type-${type.id}`}
                className="flex items-center cursor-pointer"
              >
                <div className="mr-3">{type.icon}</div>
                <div>
                  <div className="font-medium">{type.name}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {selectedResourceTypes.includes(type.id) ? 'Selected' : 'Click to select'}
                  </div>
                </div>
              </label>
            </div>
          ))}
        </div>
      </Card>

      <Card className="p-4 shadow-md">
        <Title className="text-lg font-semibold mb-4">CPU Utilization Threshold</Title>
        <Text className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Set the CPU utilization threshold below which an EC2 instance is considered underutilized.
          Lower values will find more underutilized instances.
        </Text>
        
        <div className="mb-4">
          <Select
            value={cpuThreshold.toString()}
            onValueChange={(value) => setCpuThreshold(Number(value))}
            className="w-full"
          >
            {predefinedThresholds.map((threshold) => (
              <SelectItem key={threshold.value} value={threshold.value.toString()}>
                {threshold.label}
              </SelectItem>
            ))}
          </Select>
        </div>

        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Custom CPU Threshold (%)
          </label>
          <div className="flex items-center">
            <input
              type="range"
              min="1"
              max="50"
              step="1"
              value={cpuThreshold}
              onChange={(e) => setCpuThreshold(parseInt(e.target.value))}
              className="w-full h-2 bg-blue-100 rounded-lg appearance-none cursor-pointer dark:bg-blue-900/30"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 w-12 text-center">{cpuThreshold}%</span>
          </div>
        </div>
      </Card>

      <Card className="p-4 shadow-md">
        <Title className="text-lg font-semibold mb-4">Analysis Period</Title>
        <Text className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Set how many days to look back for resource utilization data.
          Longer periods provide more accurate insights but may take longer to analyze.
        </Text>
        
        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Lookback Period (days)
          </label>
          <div className="flex items-center">
            <input
              type="range"
              min="7"
              max="90"
              step="1"
              value={lookbackDays}
              onChange={(e) => setLookbackDays(parseInt(e.target.value))}
              className="w-full h-2 bg-blue-100 rounded-lg appearance-none cursor-pointer dark:bg-blue-900/30"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 w-12 text-center">{lookbackDays}</span>
          </div>
          
          <div className="grid grid-cols-4 gap-2 mt-2">
            {[7, 14, 30, 60].map((days) => (
              <button
                key={days}
                onClick={() => setLookbackDays(days)}
                className={`
                  text-xs py-1 px-2 rounded 
                  ${lookbackDays === days 
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
        <Title className="text-lg font-semibold mb-4">Advanced Settings</Title>
        
        <div className="flex items-center mb-4">
          <input
            type="checkbox"
            id="debug-output"
            checked={showDebugOutput}
            onChange={() => setShowDebugOutput(!showDebugOutput)}
            className="mr-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="debug-output" className="text-sm text-gray-700 dark:text-gray-300">
            Show Debug Output (helpful for troubleshooting)
          </label>
        </div>
        
        <Divider />
        
        <div className="mt-4">
          <Text className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            Resource Analyzer Command Preview:
          </Text>
          <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700 font-mono text-sm overflow-x-auto">
            aws-finops --profiles [selected-profiles] --resource-analyzer --regions [selected-regions] --lookback-days {lookbackDays} --cpu-utilization-threshold {cpuThreshold} {showDebugOutput ? 'AWS_DEBUG=1' : ''}
          </div>
        </div>
      </Card>
    </div>
  );
} 
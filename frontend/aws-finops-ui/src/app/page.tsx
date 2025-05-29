'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/Header';
import { TaskSelector } from '@/components/TaskSelector';
import { ProfileSelector } from '@/components/ProfileSelector';
import { RegionSelector } from '@/components/RegionSelector';
import { CurrencySelector } from '@/components/CurrencySelector';
import { TagSelector } from '@/components/TagSelector';
import { TaskOutput } from '@/components/TaskOutput';
import { ResourceAnalyzerOptions } from '@/components/ResourceAnalyzerOptions';
import { Task, runTask } from '@/lib/api';
import { Button, Card, Title, Text, Switch } from '@tremor/react';
import { motion } from 'framer-motion';
import { FaCog, FaChartLine, FaCalendarAlt, FaLightbulb, FaBookmark } from 'react-icons/fa';

export default function Home() {
  const router = useRouter();
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [selectedProfiles, setSelectedProfiles] = useState<string[]>([]);
  const [selectedRegions, setSelectedRegions] = useState<string[]>([]);
  const [combineProfiles, setCombineProfiles] = useState(false);
  const [isTaskRunning, setIsTaskRunning] = useState(false);
  const [reportName, setReportName] = useState(`report_${new Date().toISOString().split('T')[0]}`);
  const [selectedFormats, setSelectedFormats] = useState<string[]>(['csv']);
  const [selectedCurrency, setSelectedCurrency] = useState('USD');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [timeRange, setTimeRange] = useState(30);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [enhancedPdf, setEnhancedPdf] = useState(false);
  const [skipRiAnalysis, setSkipRiAnalysis] = useState(false);
  const [skipSavingsPlans, setSkipSavingsPlans] = useState(false);
  const [cpuThreshold, setCpuThreshold] = useState(40);
  const [anomalySensitivity, setAnomalySensitivity] = useState(0.05);
  const [lookbackDays, setLookbackDays] = useState(30);
  const [wizardStep, setWizardStep] = useState(1);
  const [showPresets, setShowPresets] = useState(false);
  
  const presets = [
    {
      name: "Monthly Cost Summary",
      description: "Get a quick overview of this month's costs",
      task: "dashboard",
      timeRange: 30,
      formats: ["pdf"],
      enhancedPdf: true,
    },
    {
      name: "Savings Opportunity",
      description: "Find all possible cost optimizations",
      task: "optimize",
      timeRange: 90,
      formats: ["pdf", "csv"],
      enhancedPdf: true,
      skipRiAnalysis: false,
      skipSavingsPlans: false,
    },
    {
      name: "FinOps Health Check",
      description: "Comprehensive audit of your AWS environment",
      task: "audit",
      timeRange: 30,
      formats: ["pdf"],
      enhancedPdf: true,
    }
  ];
  
  const applyPreset = (preset: typeof presets[0]) => {
    setSelectedTask({ id: preset.task, name: '', description: '' });
    setTimeRange(preset.timeRange);
    setSelectedFormats(preset.formats);
    setEnhancedPdf(preset.enhancedPdf);
    if ('skipRiAnalysis' in preset) setSkipRiAnalysis(preset.skipRiAnalysis ?? false);
    if ('skipSavingsPlans' in preset) setSkipSavingsPlans(preset.skipSavingsPlans ?? false);
    setShowPresets(false);
  };
  
  const nextStep = () => {
    if (wizardStep < 3) {
      setWizardStep(wizardStep + 1);
    }
  };
  
  const prevStep = () => {
    if (wizardStep > 1) {
      setWizardStep(wizardStep - 1);
    }
  };
  
  const isStepValid = () => {
    switch (wizardStep) {
      case 1:
        return !!selectedTask;
      case 2:
        return selectedProfiles.length > 0 && selectedRegions.length > 0;
      case 3:
        return true;
      default:
        return false;
    }
  };

  const runTaskHandler = async () => {
    if (!selectedTask || selectedProfiles.length === 0 || selectedRegions.length === 0) {
      alert('Please complete all required fields');
      return;
    }

    setIsTaskRunning(true);

    try {
      // Get resource types from ResourceAnalyzerOptions component if it's the selected task
      const resourceTypes = 
        selectedTask.id === 'resource_analyzer' && 
        document.getElementById('resource-analyzer-form')
          ? Array.from(document.querySelectorAll('#resource-analyzer-form input[name="resource-type"]:checked'))
              .map((el) => (el as HTMLInputElement).value)
          : ['all'];
      
      // Get debug mode from ResourceAnalyzerOptions component
      const debugMode = 
        selectedTask.id === 'resource_analyzer' &&
        document.getElementById('debug-output')
          ? (document.getElementById('debug-output') as HTMLInputElement).checked
          : false;

      const result = await runTask({
        task_type: selectedTask.id,
        profiles: selectedProfiles,
        regions: selectedRegions,
        combine: combineProfiles,
        report_name: reportName,
        formats: selectedFormats,
        currency: selectedCurrency,
        tag: selectedTags,
        time_range: timeRange,
        enhanced_pdf: enhancedPdf,
        skip_ri_analysis: skipRiAnalysis,
        skip_savings_plans: skipSavingsPlans,
        cpu_threshold: cpuThreshold,
        anomaly_sensitivity: anomalySensitivity,
        lookback_days: lookbackDays,
        resource_types: resourceTypes,
        debug_mode: debugMode,
      });

      // The rest of the function remains the same...
    } catch (error) {
      console.error('Error running task:', error);
      setIsTaskRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <Header />
      
      <main className="container mx-auto px-4 py-6 sm:py-10">
        <div className={`${isTaskRunning ? 'max-w-[95vw]' : 'max-w-6xl'} mx-auto`}>
          <div className="bg-white dark:bg-gray-800 p-6 sm:p-8 rounded-2xl shadow-lg mb-8 border border-gray-200 dark:border-gray-700 transition-all duration-300 hover:shadow-xl">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">AWS FinOps Dashboard</h1>
                <p className="text-gray-600 dark:text-gray-300 max-w-2xl">
                  Configure your AWS FinOps Dashboard settings below and run a task to analyze your AWS costs.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowPresets(!showPresets)}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-300 rounded-lg border border-blue-200 dark:border-blue-800/50 transition-colors hover:bg-blue-100 dark:hover:bg-blue-800/30"
                >
                  <FaLightbulb className="text-blue-500" />
                  Presets
                </button>
                <img 
                  src="/aws-logo.svg" 
                  alt="AWS Logo" 
                  className="hidden md:block w-16 h-16 mt-4 md:mt-0 object-contain" 
                  onError={(e) => e.currentTarget.style.display = 'none'} 
                />
              </div>
            </div>
            
            {showPresets && (
              <div className="mt-6 bg-blue-50 dark:bg-blue-900/10 p-4 rounded-xl border border-blue-200 dark:border-blue-800/30 animate-fadeIn">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center gap-2">
                    <FaBookmark className="text-blue-500" />
                    Quick Start Presets
                  </h3>
                  <button 
                    onClick={() => setShowPresets(false)}
                    className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    &times;
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {presets.map((preset, index) => (
                    <div 
                      key={index}
                      className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => applyPreset(preset)}
                    >
                      <h4 className="font-medium text-gray-900 dark:text-white mb-1">{preset.name}</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-300">{preset.description}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                          {preset.task.replace('_', ' ')}
                        </span>
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
                          {preset.timeRange} days
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {!isTaskRunning && (
              <div className="mt-6 mb-2">
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-sm font-medium ${wizardStep >= 1 ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}`}>Task Type</span>
                  <span className={`text-sm font-medium ${wizardStep >= 2 ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}`}>Profiles & Regions</span>
                  <span className={`text-sm font-medium ${wizardStep >= 3 ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'}`}>Report Options</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                  <div className="bg-blue-600 dark:bg-blue-500 h-2.5 rounded-full transition-all duration-300" style={{ width: `${(wizardStep / 3) * 100}%` }}></div>
                </div>
              </div>
            )}
          </div>
          
          <div className="grid grid-cols-1 gap-8">
            {!isTaskRunning ? (
              <>
                {wizardStep === 1 && (
                  <div className="animate-slideIn">
                    <TaskSelector 
                      onSelectTask={setSelectedTask} 
                      selectedTaskId={selectedTask?.id} 
                    />
                    
                    <div className="flex justify-end mt-6">
                      <Button
                        size="lg"
                        color="blue"
                        disabled={!isStepValid()}
                        onClick={nextStep}
                        className="px-8"
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
                
                {wizardStep === 2 && (
                  <div className="animate-slideIn">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <ProfileSelector 
                        selectedProfiles={selectedProfiles}
                        onSelectProfiles={setSelectedProfiles}
                        combineProfiles={combineProfiles}
                        onCombineProfiles={setCombineProfiles}
                      />
                      
                      <RegionSelector 
                        selectedRegions={selectedRegions}
                        onSelectRegions={setSelectedRegions}
                      />
                    </div>
                    
                    <div className="flex justify-between mt-6">
                      <Button
                        size="lg"
                        color="gray"
                        onClick={prevStep}
                        className="px-8"
                      >
                        Back
                      </Button>
                      <Button
                        size="lg"
                        color="blue"
                        disabled={!isStepValid()}
                        onClick={nextStep}
                        className="px-8"
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
                
                {wizardStep === 3 && (
                  <div className="animate-slideIn">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <CurrencySelector 
                        selectedCurrency={selectedCurrency}
                        onSelectCurrency={setSelectedCurrency}
                      />
                    
                      <Card className="shadow-md border border-gray-200 dark:border-gray-700 transition-all duration-300 hover:shadow-lg">
                        <div className="px-1 py-2">
                          <Title className="text-xl font-bold text-gray-900 dark:text-white">Report Options</Title>
                          <Text className="mt-2 mb-4 text-gray-600 dark:text-gray-300">Configure how you want your report generated</Text>
                          
                          <div className="mb-6">
                            <label htmlFor="reportName" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                              Report Name
                            </label>
                            <input
                              type="text"
                              id="reportName"
                              value={reportName}
                              onChange={(e) => setReportName(e.target.value)}
                              className="block w-full rounded-lg border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm transition-colors duration-200"
                            />
                          </div>
                          
                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Report Formats</label>
                            <div className="flex flex-wrap gap-4">
                              {['csv', 'json', 'pdf'].map((format) => (
                                <div key={format} className="flex items-center">
                                  <input
                                    type="checkbox"
                                    id={`format-${format}`}
                                    checked={selectedFormats.includes(format)}
                                    onChange={(e) => {
                                      if (e.target.checked) {
                                        setSelectedFormats([...selectedFormats, format]);
                                      } else {
                                        setSelectedFormats(selectedFormats.filter((f) => f !== format));
                                      }
                                    }}
                                    className="mr-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700"
                                  />
                                  <label htmlFor={`format-${format}`} className="text-sm text-gray-800 dark:text-gray-200 uppercase">
                                    {format}
                                  </label>
                                </div>
                              ))}
                            </div>
                          </div>
                          
                          <div className="mt-6">
                            <label className="flex items-center justify-between text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                              <span>Time Range (days)</span>
                              <span className="text-blue-600 dark:text-blue-400">{timeRange} days</span>
                            </label>
                            <input
                              type="range"
                              min="7"
                              max="90"
                              step="1"
                              value={timeRange}
                              onChange={(e) => setTimeRange(parseInt(e.target.value))}
                              className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
                            />
                            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                              <span>7</span>
                              <span>30</span>
                              <span>60</span>
                              <span>90</span>
                            </div>
                          </div>
                        </div>
                      </Card>
                    </div>
                    
                    <TagSelector
                      selectedTags={selectedTags}
                      onSelectTags={setSelectedTags}
                    />
                    
                    <div className="mb-6">
                      <button
                        onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
                        className="flex items-center gap-2 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
                      >
                        <FaCog className={`transition-transform ${showAdvancedOptions ? 'rotate-90' : ''}`} />
                        {showAdvancedOptions ? 'Hide Advanced Options' : 'Show Advanced Options'}
                      </button>
                      
                      {showAdvancedOptions && (
                        <div className="space-y-6 mt-6 border-t border-gray-200 dark:border-gray-700 pt-6">
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Advanced Options</h3>
                          
                          {selectedTask?.id === 'resource_analyzer' ? (
                            <ResourceAnalyzerOptions 
                              cpuThreshold={cpuThreshold}
                              setCpuThreshold={setCpuThreshold}
                              lookbackDays={lookbackDays}
                              setLookbackDays={setLookbackDays}
                            />
                          ) : (
                            <>
                              {(selectedTask?.id === 'optimize' || selectedTask?.id === 'dashboard') && (
                                <div className="space-y-4">
                                  <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                      CPU Threshold (%)
                                    </label>
                                    <div className="flex items-center">
                                      <input
                                        type="range"
                                        min="5"
                                        max="80"
                                        step="5"
                                        value={cpuThreshold}
                                        onChange={(e) => setCpuThreshold(parseInt(e.target.value))}
                                        className="w-full h-2 bg-blue-100 rounded-lg appearance-none cursor-pointer dark:bg-blue-900/30"
                                      />
                                      <span className="ml-2 text-sm text-gray-700 dark:text-gray-300 w-10 text-center">{cpuThreshold}%</span>
                                    </div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                      Threshold for EC2 underutilization
                                    </p>
                                  </div>
                                  
                                  {selectedTask?.id === 'optimize' && (
                                    <div className="space-y-3">
                                      <div className="flex items-center justify-between">
                                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                          Skip Reserved Instance Analysis
                                        </label>
                                        <Switch
                                          checked={skipRiAnalysis}
                                          onChange={setSkipRiAnalysis}
                                          color="blue"
                                        />
                                      </div>
                                      <div className="flex items-center justify-between">
                                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                          Skip Savings Plans Analysis
                                        </label>
                                        <Switch
                                          checked={skipSavingsPlans}
                                          onChange={setSkipSavingsPlans}
                                          color="blue"
                                        />
                                      </div>
                                    </div>
                                  )}
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex justify-between mt-8">
                      <Button
                        size="lg"
                        color="gray"
                        onClick={prevStep}
                        className="px-8"
                      >
                        Back
                      </Button>
                      <Button
                        size="lg"
                        color="blue"
                        disabled={!isStepValid()}
                        onClick={runTaskHandler}
                        className={`
                          relative overflow-hidden group flex items-center gap-3 px-8 py-3.5 
                          font-medium text-white rounded-xl shadow-lg
                          transition-all duration-300 hover:scale-105 active:scale-95
                          ${!isStepValid()
                            ? 'bg-gray-400 dark:bg-gray-600 cursor-not-allowed opacity-60'
                            : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700'
                          }
                        `}
                      >
                        <span className="relative z-10 flex items-center">
                          <svg 
                            className="w-5 h-5 mr-2" 
                            fill="none" 
                            viewBox="0 0 24 24" 
                            stroke="currentColor"
                          >
                            <path 
                              strokeLinecap="round" 
                              strokeLinejoin="round" 
                              strokeWidth={2} 
                              d="M13 10V3L4 14h7v7l9-11h-7z" 
                            />
                          </svg>
                          Run Task
                        </span>
                        <div className="absolute inset-0 w-full h-full bg-gradient-to-r from-indigo-500 to-blue-500 opacity-0 group-hover:opacity-20 transition-opacity duration-300"></div>
                        <div className="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-white/20 to-transparent transform translate-x-12 group-hover:translate-x-0 transition-transform duration-300"></div>
                      </Button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <TaskOutput 
                taskType={selectedTask?.id || ''} 
                onViewResults={() => router.push('/previous-results')}
              />
            )}
          </div>
        </div>
      </main>
      
      <footer className="bg-white dark:bg-gray-800 py-6 mt-12 border-t border-gray-200 dark:border-gray-700 shadow-inner">
        <div className="container mx-auto px-4">
          <p className="text-center text-gray-600 dark:text-gray-400 text-sm">
            AWS FinOps Dashboard | Built with Next.js and Flask
          </p>
        </div>
      </footer>
    </div>
  );
}

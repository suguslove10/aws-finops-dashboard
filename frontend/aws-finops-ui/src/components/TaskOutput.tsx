'use client';

import { useEffect, useRef, useState } from 'react';
import { Card, Title, Badge, Button } from '@tremor/react';
import { useQuery } from '@tanstack/react-query';
import { fetchTaskStatus, getDownloadUrl, TaskResult } from '@/lib/api';
import { FaDownload, FaSync, FaCheckCircle, FaExclamationTriangle, FaSpinner, FaExternalLinkAlt, FaFilePdf, FaFileCsv, FaFileAlt, FaFile } from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal } from '@xterm/xterm';
import '@xterm/xterm/css/xterm.css';

interface TaskOutputProps {
  taskType: string;
  onViewResults: () => void;
}

export function TaskOutput({ taskType, onViewResults }: TaskOutputProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<Terminal | null>(null);
  const [isTerminalReady, setIsTerminalReady] = useState(false);
  const [lastOutput, setLastOutput] = useState('');
  
  const { data, isLoading, error, refetch } = useQuery<TaskResult>({
    queryKey: ['taskStatus', taskType],
    queryFn: () => fetchTaskStatus(taskType),
    refetchInterval: 2000,
    refetchIntervalInBackground: false,
    enabled: !!taskType,
  });

  // Initialize xterm.js
  useEffect(() => {
    // Only run once
    if (!terminalRef.current || isTerminalReady) return;

    const initTerminal = async () => {
      const term = new Terminal({
        fontFamily: 'Menlo, Monaco, Consolas, "Courier New", monospace',
        fontSize: 12,
        letterSpacing: 0,
        lineHeight: 1.2,
        theme: {
          background: '#1a1a1a',
          foreground: '#f8f8f8',
          cursor: '#aeafad',
          cursorAccent: '#000000',
          selectionBackground: '#5DA5D533',
          black: '#1a1a1a',
          red: '#ff6b68',
          green: '#a8c023',
          yellow: '#d6bf55',
          blue: '#5394ec',
          magenta: '#ae8abe',
          cyan: '#299999',
          white: '#f8f8f8',
          brightBlack: '#5c5c5c',
          brightRed: '#ff8080',
          brightGreen: '#b8e466',
          brightYellow: '#ffff80',
          brightBlue: '#80a6ff',
          brightMagenta: '#d580ff',
          brightCyan: '#80ffff',
          brightWhite: '#ffffff'
        },
        cursorBlink: true,
        scrollback: 1000,
        allowTransparency: true,
        convertEol: true,
        cols: 250,
        rows: 40,
        rightClickSelectsWord: true,
        wordSeparator: ' ()[]{}\'",;:',
        disableStdin: true,
      });

      xtermRef.current = term;
      
      if (terminalRef.current) {
        term.open(terminalRef.current);
        
        // Resize terminal to fit container width
        const resizeObserver = new ResizeObserver((entries) => {
          if (!xtermRef.current) return;
          
          const containerWidth = terminalRef.current?.clientWidth || 0;
          const charWidth = 7.2; // Approximate width of monospace char in pixels
          const cols = Math.floor(containerWidth / charWidth);
          
          if (cols > 80) {
            xtermRef.current.resize(cols, term.rows);
          }
        });
        
        if (terminalRef.current) {
          resizeObserver.observe(terminalRef.current);
        }
        
        // Add some padding inside the terminal
        const xtermElement = terminalRef.current.querySelector('.xterm') as HTMLElement;
        if (xtermElement) {
          xtermElement.style.padding = '0';
          xtermElement.style.height = '100%';
          xtermElement.style.width = '100%';
          
          // Also adjust the terminal inner elements
          const xtermViewport = terminalRef.current.querySelector('.xterm-viewport') as HTMLElement;
          if (xtermViewport) {
            xtermViewport.style.paddingLeft = '0';
          }
          
          const xtermScreen = terminalRef.current.querySelector('.xterm-screen') as HTMLElement;
          if (xtermScreen) {
            xtermScreen.style.marginLeft = '0';
            xtermScreen.style.width = '100%';
          }
          
          // Fix canvas width to match parent width
          const canvas = terminalRef.current.querySelector('canvas');
          if (canvas) {
            canvas.style.width = '100%';
          }
        }
        
        setIsTerminalReady(true);
        
        // Cleanup for resize observer
        return () => {
          resizeObserver.disconnect();
        };
      }
    };

    initTerminal();

    // Cleanup function
    return () => {
      if (xtermRef.current) {
        xtermRef.current.dispose();
      }
    };
  }, []);

  // Process the output and write to terminal
  useEffect(() => {
    if (!isTerminalReady || !xtermRef.current || !data?.output) return;

    // Only update if the output has changed
    if (data.output !== lastOutput) {
      // Clear terminal first
      xtermRef.current.clear();
      
      // Write raw output with ANSI escape codes
      xtermRef.current.write(data.output);
      
      // Store the last output
      setLastOutput(data.output);
    }
  }, [data?.output, isTerminalReady, lastOutput]);

  // Stop polling when task is complete
  useEffect(() => {
    if (data?.status === 'completed' || data?.status === 'error') {
      // Cancel refetch interval
      refetch({ cancelRefetch: true });
    }
  }, [data?.status, refetch]);

  // Get status color based on current status
  const getStatusColor = () => {
    if (!data) return 'gray';
    
    switch (data.status) {
      case 'running': return 'blue';
      case 'completed': return 'green';
      case 'error': return 'red';
      default: return 'gray';
    }
  };
  
  // Get status text based on current status
  const getStatusText = () => {
    if (!data) return 'Waiting';
    
    switch (data.status) {
      case 'running': return 'Running';
      case 'completed': return 'Completed';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  };
  
  const statusColor = getStatusColor();

  const getStatusBadge = () => {
    switch (data?.status) {
      case 'running':
        return (
          <Badge color="blue" className="inline-flex items-center gap-1 px-3 py-1.5">
            <FaSpinner className="animate-spin" />
            <span>Running</span>
          </Badge>
        );
      case 'completed':
        return (
          <Badge color="green" className="inline-flex items-center gap-1 px-3 py-1.5">
            <FaCheckCircle />
            <span>Completed</span>
          </Badge>
        );
      case 'error':
        return (
          <Badge color="red" className="inline-flex items-center gap-1 px-3 py-1.5">
            <FaExclamationTriangle />
            <span>Error</span>
          </Badge>
        );
      default:
        return <Badge color="gray" className="px-3 py-1.5">Not Started</Badge>;
    }
  };

  const renderOutputContent = () => {
    if (!data || data.status === 'not_found') {
      return null;
    }

    // Special formatting for resource analyzer content
    if (taskType === 'resource_analyzer' && data.status === 'completed') {
      return (
        <div className="mt-4">
          <div className="overflow-auto max-h-[600px] p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            {/* Parse and format tables */}
            {parseResourceAnalyzerOutput(data.output)}
          </div>

          {/* Download buttons for reports */}
          {data.files && data.files.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-3">Download Reports</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {data.files.map((file, index) => (
                  <a
                    key={index}
                    href={getDownloadUrl(file)}
                    className="flex items-center gap-2 p-3 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md border border-gray-200 dark:border-gray-700 transition-all duration-200"
                    download
                  >
                    <div className="p-2 rounded-full bg-blue-50 dark:bg-blue-900/20">
                      {getFileIcon(file)}
                    </div>
                    <div className="overflow-hidden">
                      <p className="font-medium text-sm truncate">{file}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {getFileType(file)}
                      </p>
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      );
    }

    // Default output rendering
    return (
      <div className="mt-4">
        <pre className="overflow-auto max-h-[600px] p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 text-sm font-mono whitespace-pre-wrap">
          {data.output}
        </pre>
      </div>
    );
  };

  // Helper function to get file icon based on extension
  const getFileIcon = (filename: string) => {
    const extension = filename.split('.').pop()?.toLowerCase();
    
    switch (extension) {
      case 'pdf':
        return <FaFilePdf className="text-red-500" size={20} />;
      case 'csv':
        return <FaFileCsv className="text-green-500" size={20} />;
      case 'json':
        return <FaFileAlt className="text-orange-500" size={20} />;
      default:
        return <FaFile className="text-gray-500" size={20} />;
    }
  };

  // Helper function to get file type description
  const getFileType = (filename: string) => {
    const extension = filename.split('.').pop()?.toLowerCase();
    
    switch (extension) {
      case 'pdf':
        return 'PDF Report';
      case 'csv':
        return 'CSV Spreadsheet';
      case 'json':
        return 'JSON Data';
      default:
        return 'File';
    }
  };

  // Helper function to parse resource analyzer output
  const parseResourceAnalyzerOutput = (output: string) => {
    try {
      // Split output into sections based on table headers
      const sections = output.split(/===[^\n]+===/g).filter(section => section.trim());
      
      return (
        <>
          {/* Display any EC2 instance tables */}
          {output.includes('Unused or Underutilized EC2 Instances') && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold mb-4">Unused or Underutilized EC2 Instances</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-100 dark:bg-gray-800">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Instance ID</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Name</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Region</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">State</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">CPU Usage</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Cost</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Recommendation</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                    {extractEc2TableData(output).map((row, index) => (
                      <tr key={index} className={index % 2 === 0 ? 'bg-white dark:bg-gray-900' : 'bg-gray-50 dark:bg-gray-800'}>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100 font-mono">{row.id}</td>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">{row.name}</td>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">{row.region}</td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            row.state === 'running' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' : 
                            row.state === 'stopped' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300' : 
                            row.state.startsWith('underutil') ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300' :
                            'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                          }`}>
                            {row.state}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">{row.usage}</td>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">{row.cost}</td>
                        <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{row.recommendation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          
          {/* Display summary information */}
          {output.includes('Summary:') && (
            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800/50">
              <h3 className="text-lg font-semibold mb-2 text-blue-900 dark:text-blue-300">Summary</h3>
              {extractSummaryData(output).map((item, index) => (
                <div key={index} className="flex justify-between py-2 border-b border-blue-200 dark:border-blue-800/50 last:border-0">
                  <span className="text-gray-700 dark:text-gray-300">{item.label}</span>
                  <span className="font-semibold text-blue-700 dark:text-blue-300">{item.value}</span>
                </div>
              ))}
            </div>
          )}
        </>
      );
    } catch (error) {
      console.error('Error parsing resource analyzer output:', error);
      return (
        <pre className="overflow-auto max-h-[600px] p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 text-sm font-mono whitespace-pre-wrap">
          {output}
        </pre>
      );
    }
  };

  // Helper function to extract EC2 instance data from output
  const extractEc2TableData = (output: string) => {
    try {
      // This is a simplified parser - in a real implementation you'd want more robust parsing
      const lines = output.split('\n');
      const startIndex = lines.findIndex(line => line.includes('Unused or Underutilized EC2 Instances'));
      if (startIndex === -1) return [];
      
      // Find table rows (simplified)
      const tableData = [];
      for (let i = startIndex + 3; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line || line.startsWith('No unused') || line.startsWith('Summary:')) break;
        
        // Basic line parsing - in real impl you'd use regex or better parsing
        const parts = line.split(/\s{2,}/);
        if (parts.length >= 6) {
          tableData.push({
            id: parts[0],
            name: parts[1],
            region: parts[2],
            state: parts[3], // Don't lowercase the state to preserve full text
            usage: parts[4],
            cost: parts[5],
            recommendation: parts.slice(6).join(' ')
          });
        }
      }
      
      return tableData;
    } catch (error) {
      console.error('Error extracting EC2 table data:', error);
      return [];
    }
  };

  // Helper function to extract summary data
  const extractSummaryData = (output: string) => {
    try {
      const lines = output.split('\n');
      const startIndex = lines.findIndex(line => line.includes('Summary:'));
      if (startIndex === -1) return [];
      
      const summaryData = [];
      for (let i = startIndex + 1; i < lines.length && i < startIndex + 5; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        const parts = line.split(':');
        if (parts.length >= 2) {
          summaryData.push({
            label: parts[0].trim(),
            value: parts.slice(1).join(':').trim()
          });
        }
      }
      
      return summaryData;
    } catch (error) {
      console.error('Error extracting summary data:', error);
      return [];
    }
  };

  return (
    <Card className="mt-8 shadow-md border border-gray-200 dark:border-gray-700">
      <div className="p-4">
        <div className="flex justify-between items-center mb-4">
          <div>
            <Title className="text-xl font-bold">Task Output</Title>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Results will appear here once processing is complete
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button 
              size="xs"
              color="gray"
              onClick={() => refetch()}
              icon={FaSync}
              disabled={isLoading}
            >
              Refresh
            </Button>
            {data?.status === 'completed' && data.files.length > 0 && (
              <Button
                size="xs"
                color="blue"
                onClick={onViewResults}
                icon={FaExternalLinkAlt}
              >
                View All Files
              </Button>
            )}
          </div>
        </div>
        
        {/* Status indicator */}
        <div className="mb-6">
          <div className="flex items-center mb-2">
            <Badge color={statusColor} size="sm" className="mr-2">
              {getStatusText()}
            </Badge>
            
            {isLoading && (
              <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center">
                <FaSpinner className="animate-spin mr-1" />
                Refreshing...
              </span>
            )}
          </div>
          
          {/* Progress indicator for running tasks */}
          {data?.status === 'running' && (
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 mb-4">
              <div className="bg-blue-600 h-2.5 rounded-full animate-pulse" style={{ width: '100%' }}></div>
            </div>
          )}
        </div>
        
        {/* Task output content */}
        {renderOutputContent()}
      </div>
    </Card>
  );
} 
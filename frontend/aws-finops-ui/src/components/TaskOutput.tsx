'use client';

import { useEffect, useRef, useState } from 'react';
import { Card, Title, Badge, Button } from '@tremor/react';
import { useQuery } from '@tanstack/react-query';
import { fetchTaskStatus, getDownloadUrl, TaskResult } from '@/lib/api';
import { FaDownload, FaSync, FaCheckCircle, FaExclamationTriangle, FaSpinner, FaExternalLinkAlt } from 'react-icons/fa';
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

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-[98vw] mx-auto"
    >
      <Card className="mb-6 border border-gray-200 dark:border-gray-700 shadow-lg transition-all duration-300 w-full px-1 sm:px-2">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-6 gap-4">
          <div className="flex items-center gap-3">
            <Title className="text-xl font-bold text-gray-900 dark:text-white">Task: {taskType.charAt(0).toUpperCase() + taskType.slice(1).replace('_', ' ')}</Title>
            {getStatusBadge()}
          </div>
          <div className="flex items-center gap-2">
            <Button 
              variant="secondary" 
              icon={FaSync} 
              size="sm"
              onClick={() => refetch()}
              className="self-end sm:self-auto"
            >
              Refresh
            </Button>
            
            {data?.status === 'completed' && (
              <Button
                variant="light"
                icon={FaDownload}
                size="sm"
                onClick={() => {
                  // Create a Blob from the terminal text
                  const blob = new Blob([data.output || ''], { type: 'text/plain' });
                  const url = URL.createObjectURL(blob);
                  
                  // Create a link and trigger download
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${taskType}_output.txt`;
                  document.body.appendChild(a);
                  a.click();
                  
                  // Cleanup
                  document.body.removeChild(a);
                  URL.revokeObjectURL(url);
                }}
                color="blue"
              >
                Save Output
              </Button>
            )}
          </div>
        </div>

        <AnimatePresence>
          {data?.status === 'running' && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="flex items-center space-x-3 mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200 rounded-lg border border-blue-200 dark:border-blue-800/30"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-800/50">
                <FaSpinner className="h-5 w-5 animate-spin text-blue-600 dark:text-blue-300" />
              </div>
              <div>
                <p className="font-medium">Task is running</p>
                <p className="text-sm text-blue-700 dark:text-blue-300">This might take a few moments depending on the selected profiles and regions.</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        
        {data?.status === 'completed' && (
          <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/10 rounded-lg border border-green-200 dark:border-green-800/30">
            <div className="flex items-center gap-2">
              <FaCheckCircle className="text-green-600 dark:text-green-400" />
              <p className="text-sm text-green-800 dark:text-green-300">
                Task completed successfully! You can view the results below or download the generated files.
              </p>
            </div>
            <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
              Tip: You can click "Save Output" to download the terminal output as a text file.
            </div>
          </div>
        )}

        <div className="relative -mx-1 sm:-mx-2 w-full overflow-x-auto">
          <div
            ref={terminalRef}
            className="terminal-container bg-gray-900 text-gray-100 rounded-lg font-mono text-sm overflow-hidden"
            style={{ 
              height: '70vh',
              minHeight: '500px',
              width: '100%',
              maxWidth: '100%',
              overflowX: 'auto'
            }}
          />
          {!isTerminalReady && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-80 rounded-lg">
              <div className="flex flex-col items-center">
                <FaSpinner className="animate-spin text-blue-400 mb-4 h-8 w-8" />
                <p className="text-gray-300">Initializing terminal...</p>
              </div>
            </div>
          )}
          {data?.status === 'running' && (
            <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-gray-900 to-transparent pointer-events-none"></div>
          )}
        </div>

        <AnimatePresence>
          {data?.files && data.files.length > 0 && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="mt-6"
            >
              <h3 className="text-sm font-semibold mb-3 text-gray-800 dark:text-gray-200 flex items-center gap-2">
                <FaDownload className="text-blue-500" />
                Generated Files
              </h3>
              <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
                {data.files.map((file, index) => (
                  <motion.div 
                    key={file}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                    className={`
                      flex items-center justify-between p-3
                      ${index < data.files.length - 1 ? 'border-b border-gray-200 dark:border-gray-700' : ''}
                    `}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <div className="flex-shrink-0">
                        {file.endsWith('.pdf') ? (
                          <div className="bg-red-100 dark:bg-red-900/30 h-8 w-8 rounded flex items-center justify-center">
                            <span className="text-xs font-medium text-red-800 dark:text-red-300">PDF</span>
                          </div>
                        ) : file.endsWith('.csv') ? (
                          <div className="bg-green-100 dark:bg-green-900/30 h-8 w-8 rounded flex items-center justify-center">
                            <span className="text-xs font-medium text-green-800 dark:text-green-300">CSV</span>
                          </div>
                        ) : file.endsWith('.json') ? (
                          <div className="bg-blue-100 dark:bg-blue-900/30 h-8 w-8 rounded flex items-center justify-center">
                            <span className="text-xs font-medium text-blue-800 dark:text-blue-300">JSON</span>
                          </div>
                        ) : (
                          <div className="bg-gray-100 dark:bg-gray-700 h-8 w-8 rounded flex items-center justify-center">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-300">FILE</span>
                          </div>
                        )}
                      </div>
                      <div className="truncate">
                        <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                          {file}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          Generated on {new Date().toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Button
                        variant="light"
                        size="xs"
                        color="blue"
                        onClick={() => window.open(getDownloadUrl(file), '_blank')}
                        icon={FaExternalLinkAlt}
                      >
                        View
                      </Button>
                      <Button
                        variant="light"
                        size="xs"
                        color="gray"
                        onClick={() => {
                          const a = document.createElement('a');
                          a.href = getDownloadUrl(file);
                          a.download = file;
                          document.body.appendChild(a);
                          a.click();
                          document.body.removeChild(a);
                        }}
                        icon={FaDownload}
                      >
                        Download
                      </Button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        
        {data?.status === 'completed' && (
          <div className="mt-6 flex justify-end">
            <Button
              size="lg"
              color="blue"
              onClick={onViewResults}
              icon={FaExternalLinkAlt}
            >
              View All Reports
            </Button>
          </div>
        )}
      </Card>
    </motion.div>
  );
} 
'use client';

import { useEffect, useRef, useState } from 'react';
import { Card, Title, Badge, Button } from '@tremor/react';
import { useQuery } from '@tanstack/react-query';
import { fetchTaskStatus, getDownloadUrl, TaskResult, runAwsCli } from '@/lib/api';
import { FaDownload, FaSync, FaCheckCircle, FaExclamationTriangle, FaSpinner, FaExternalLinkAlt, FaTerminal } from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';
// Import Terminal type only, not the actual implementation
import type { Terminal as TerminalType } from '@xterm/xterm';
// Import CSS normally
import '@xterm/xterm/css/xterm.css';

interface TaskOutputProps {
  taskType: string;
  onViewResults: () => void;
}

export function TaskOutput({ taskType = 'dashboard', onViewResults }: TaskOutputProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<TerminalType | null>(null);
  const [isTerminalReady, setIsTerminalReady] = useState(false);
  const [lastOutput, setLastOutput] = useState('');
  const [isRunningCommand, setIsRunningCommand] = useState(false);
  const [commandOutput, setCommandOutput] = useState<string | null>(null);

  // Keep the query but don't rely on it for UI state
  const { refetch } = useQuery<TaskResult>({
    queryKey: ['taskStatus', taskType],
    queryFn: () => fetchTaskStatus(taskType),
    refetchInterval: 3000,
    refetchIntervalInBackground: false,
    enabled: !!taskType,
  });

  // Simplified terminal initialization with dynamic imports
  useEffect(() => {
    if (!terminalRef.current) return;

    async function setupTerminal() {
      try {
        // Dynamically import browser-only modules
        const xtermModule = await import('@xterm/xterm');
        const fitAddonModule = await import('@xterm/addon-fit');
        const webLinksAddonModule = await import('@xterm/addon-web-links');
        
        const Terminal = xtermModule.Terminal;
        const FitAddon = fitAddonModule.FitAddon;
        const WebLinksAddon = webLinksAddonModule.WebLinksAddon;
        
        // Clear any existing terminal
        if (xtermRef.current) {
          xtermRef.current.dispose();
          xtermRef.current = null;
        }
        
        console.log("Initializing terminal...");
        
        // Create terminal with better settings for ASCII tables
        const term = new Terminal({
          fontFamily: 'Courier, monospace',
          fontSize: 14,
          letterSpacing: 0,
          lineHeight: 1,
          theme: {
            background: '#000000',
            foreground: '#ffffff',
            black: '#000000',
            red: '#ff0000',
            green: '#33ff33',
            yellow: '#ffff33',
            blue: '#3333ff',
            magenta: '#ff33ff',
            cyan: '#33ffff',
            white: '#ffffff',
          },
          cursorBlink: false,
          scrollback: 10000,
          convertEol: true,
          cols: 132,
          rows: 40
        });
        
        // Create fit addon
        const fitAddon = new FitAddon();
        term.loadAddon(fitAddon);
        term.loadAddon(new WebLinksAddon());
        
        // Store reference
        xtermRef.current = term;
        
        // Open terminal - ensure terminalRef is not null before accessing
        if (terminalRef.current) {
          term.open(terminalRef.current);
          
          // Fit terminal to container
          setTimeout(() => {
            fitAddon.fit();
            console.log("Terminal ready");
            setIsTerminalReady(true);
            
            // Write initial message
            term.write('Terminal initialized. Click "Run Dashboard Task" to start.\r\n\r\n');
          }, 500);

          // Set up resize handler
          if (typeof window !== 'undefined') {
            const resizeObserver = new ResizeObserver(() => {
              if (xtermRef.current) {
                fitAddon.fit();
              }
            });
            
            // Ensure terminalRef is still not null before observing
            if (terminalRef.current) {
              resizeObserver.observe(terminalRef.current);
              
              // Cleanup
              return () => {
                resizeObserver.disconnect();
                term.dispose();
              };
            }
          }
        }
      } catch (error) {
        console.error("Failed to initialize terminal:", error);
      }
    }
    
    setupTerminal();
  }, []);

  // Update terminal when output changes
  useEffect(() => {
    if (commandOutput && xtermRef.current && isTerminalReady) {
      xtermRef.current.clear();
      xtermRef.current.write(commandOutput);
    }
  }, [commandOutput, isTerminalReady]);

  // Run the AWS command
  const startDashboardTask = async () => {
    if (!isTerminalReady || !xtermRef.current) {
      console.error("Terminal not ready");
      return;
    }
    
    try {
      setIsRunningCommand(true);
      
      // Clear terminal and show starting message
      xtermRef.current.clear();
      xtermRef.current.write('Starting AWS FinOps Dashboard...\r\n\r\n');
      
      // Call API endpoint
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/run_aws_cli`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          command: 'aws-finops --profiles suguresh --force-color',
          task_type: 'dashboard'
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log("Command output length:", result.output?.length);
      
      if (result.output) {
        setCommandOutput(result.output);
      } else {
        xtermRef.current.write('No output received from command.\r\n');
      }
      
      refetch();
    } catch (error) {
      console.error("Error running command:", error);
      if (xtermRef.current) {
        xtermRef.current.write(`\r\nError: ${error}\r\n`);
      }
    } finally {
      setIsRunningCommand(false);
    }
  };

  return (
    <div className="w-full max-w-[98vw] mx-auto">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <Card className="mb-6 border border-gray-200 dark:border-gray-700 shadow-lg transition-all duration-300 w-full px-1 sm:px-2">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-6 gap-4">
            <div className="flex items-center gap-3">
              <Title className="text-xl font-bold text-gray-900 dark:text-white">AWS FinOps Dashboard</Title>
              {isRunningCommand && (
                <Badge color="blue" className="inline-flex items-center gap-1 px-3 py-1.5">
                  <FaSpinner className="animate-spin" />
                  <span>Running</span>
                </Badge>
              )}
              {commandOutput && !isRunningCommand && (
                <Badge color="green" className="inline-flex items-center gap-1 px-3 py-1.5">
                  <FaCheckCircle />
                  <span>Completed</span>
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button 
                variant="secondary" 
                icon={FaSync} 
                size="sm"
                onClick={() => {
                  if (xtermRef.current && isTerminalReady) {
                    startDashboardTask();
                  } else {
                    window.location.reload();
                  }
                }}
                className="self-end sm:self-auto"
              >
                {isTerminalReady ? 'Run Again' : 'Refresh Page'}
              </Button>
              
              {commandOutput && (
                <Button
                  variant="light"
                  icon={FaDownload}
                  size="sm"
                  onClick={() => {
                    // Create a Blob from the terminal text
                    const blob = new Blob([commandOutput], { type: 'text/plain' });
                    const url = URL.createObjectURL(blob);
                    
                    // Create a link and trigger download
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `aws_finops_output.txt`;
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

          {/* Terminal Container */}
          <div className="relative -mx-1 sm:-mx-2 w-full overflow-hidden">
            <div
              ref={terminalRef}
              className="terminal-container bg-black text-gray-100 rounded-lg font-mono text-sm overflow-hidden"
              style={{ 
                height: '70vh',
                minHeight: '600px',
                width: '100%',
                maxWidth: '100%',
                overflow: 'hidden'
              }}
            />
            
            {/* Terminal Loading State */}
            {!isTerminalReady && (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-80 rounded-lg">
                <div className="flex flex-col items-center">
                  <FaSpinner className="animate-spin text-blue-400 mb-4 h-8 w-8" />
                  <p className="text-gray-300">Initializing terminal...</p>
                </div>
              </div>
            )}
            
            {/* Empty State (Terminal Ready but No Command Run) */}
            {isTerminalReady && !commandOutput && !isRunningCommand && (
              <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-70 rounded-lg">
                <div className="flex flex-col items-center text-center px-4">
                  <FaTerminal className="text-blue-400 mb-4 h-12 w-12" />
                  <h3 className="text-white text-xl font-bold mb-2">Terminal Ready</h3>
                  <p className="text-gray-300 mb-6">Click the button below to run the dashboard</p>
                  <Button
                    size="lg"
                    onClick={startDashboardTask}
                    icon={isRunningCommand ? FaSpinner : FaTerminal}
                    disabled={isRunningCommand}
                    className="bg-blue-600 hover:bg-blue-700 text-white py-4 px-8 rounded-md text-lg font-bold shadow-lg transition-all"
                  >
                    {isRunningCommand ? 'Running Command...' : 'Run Dashboard Task'}
                  </Button>
                </div>
              </div>
            )}
            
            {/* Running State Overlay */}
            {isRunningCommand && (
              <div className="absolute top-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-md shadow-lg">
                <div className="flex items-center gap-2">
                  <FaSpinner className="animate-spin" />
                  <span>Running AWS FinOps command...</span>
                </div>
              </div>
            )}
          </div>
        </Card>
      </motion.div>
    </div>
  );
} 
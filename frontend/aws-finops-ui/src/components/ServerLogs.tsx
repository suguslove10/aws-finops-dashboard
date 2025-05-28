'use client';

import { useState, useEffect, useRef } from 'react';
import { connectToLogStream } from '@/lib/api';
import { Card, Title, Badge } from '@tremor/react';
import { FaServer, FaTerminal } from 'react-icons/fa';
import { TerminalOutput } from './TerminalOutput';

export function ServerLogs() {
  const [logs, setLogs] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Connect to log stream when component mounts
    setIsConnected(true);
    
    const disconnect = connectToLogStream((message) => {
      setLogs(prev => [...prev, message].slice(-500)); // Keep last 500 logs
    });
    
    return () => {
      setIsConnected(false);
      disconnect();
    };
  }, []);
  
  // Auto-scroll to bottom when logs update
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);
  
  const formattedLogs = logs.join('\n');
  
  return (
    <Card className="mt-4 dark:bg-gray-900 border dark:border-gray-700">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <FaServer className="text-blue-500" />
          <Title>API Server Logs</Title>
          <Badge color={isConnected ? 'green' : 'red'}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
        </div>
        <div className="flex items-center">
          <FaTerminal className="mr-2 text-gray-400" />
          <span className="text-sm text-gray-500">Live feed</span>
        </div>
      </div>
      
      <div className="terminal-wrapper">
        <TerminalOutput 
          content={formattedLogs || 'Waiting for logs...'}
          height="300px" 
          className="server-logs" 
        />
        <div ref={logEndRef} />
      </div>
    </Card>
  );
} 
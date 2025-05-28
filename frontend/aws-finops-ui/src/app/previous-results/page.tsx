'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/Header';
import { Card, Title, Text, Badge, Button } from '@tremor/react';
import { useQuery } from '@tanstack/react-query';
import { fetchFiles, getDownloadUrl } from '@/lib/api';
import { FaDownload, FaChevronLeft } from 'react-icons/fa';

export default function PreviousResults() {
  const router = useRouter();
  
  const { data: files, isLoading, error, refetch } = useQuery({
    queryKey: ['files'],
    queryFn: fetchFiles,
  });
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="animate-pulse bg-gray-200 h-48 rounded-lg"></div>
        </main>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="bg-red-50 p-4 rounded-lg border border-red-200">
            <h3 className="text-red-800 font-medium">Error loading results</h3>
            <p className="text-red-600 text-sm">Please check your connection to the API server.</p>
            
            <Button 
              className="mt-4"
              variant="secondary"
              icon={FaChevronLeft}
              onClick={() => router.push('/')}
            >
              Back to Dashboard
            </Button>
          </div>
        </main>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Previous Task Results</h1>
          <div className="flex space-x-2">
            <Button 
              variant="secondary"
              icon={FaChevronLeft}
              onClick={() => router.push('/')}
            >
              Back to Dashboard
            </Button>
            <Button
              variant="secondary"
              onClick={() => refetch()}
            >
              Refresh
            </Button>
          </div>
        </div>
        
        {files && files.length > 0 ? (
          <Card>
            <Title>Generated Files</Title>
            <Text className="mt-2 mb-4">Files generated from all previous tasks</Text>
            
            <div className="divide-y">
              {files.map((file) => (
                <div key={file} className="py-3 flex justify-between items-center">
                  <div>
                    <p className="font-medium text-gray-900">{file}</p>
                    <p className="text-sm text-gray-500">
                      {file.split('.').pop()?.toUpperCase()} format
                    </p>
                  </div>
                  <a
                    href={getDownloadUrl(file)}
                    className="flex items-center space-x-1 text-blue-600 hover:text-blue-800"
                    download
                  >
                    <FaDownload />
                    <span>Download</span>
                  </a>
                </div>
              ))}
            </div>
          </Card>
        ) : (
          <div className="bg-yellow-50 p-8 rounded-lg border border-yellow-200 text-center">
            <h3 className="text-yellow-800 font-medium mb-2">No files found</h3>
            <p className="text-yellow-700 mb-4">No previous task results were found.</p>
            <Button onClick={() => router.push('/')}>Run a New Task</Button>
          </div>
        )}
      </main>
    </div>
  );
} 
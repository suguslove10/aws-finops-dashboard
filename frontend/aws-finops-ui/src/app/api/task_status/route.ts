import { NextResponse } from 'next/server';

/**
 * API route handler for getting task status
 * This proxies the request to the Python backend
 */
export async function GET(request: Request) {
  try {
    // Get API URL from environment variable or use default
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
    
    // Get the search params
    const { searchParams } = new URL(request.url);
    const taskType = searchParams.get('task_type');
    const format = searchParams.get('format');
    
    if (!taskType) {
      return NextResponse.json(
        { error: 'Missing task_type parameter' },
        { status: 400 }
      );
    }
    
    // Log the request for debugging
    console.log(`API Request to /api/task_status with task_type=${taskType}, format=${format}`);
    
    // Forward the request to the Python backend
    let url = `${apiUrl}/api/task_status?task_type=${taskType}`;
    if (format) {
      url += `&format=${format}`;
    }
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Backend error: ${response.status} ${response.statusText}`);
    }
    
    // Get the response data
    const data = await response.json();
    console.log('Response received from backend:', data);
    
    // Return the response
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in task_status API route:', error);
    return NextResponse.json(
      { 
        error: 'Failed to fetch task status',
        message: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
} 
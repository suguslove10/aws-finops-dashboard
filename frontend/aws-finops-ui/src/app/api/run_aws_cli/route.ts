import { NextResponse } from 'next/server';

/**
 * API route handler for running AWS CLI commands
 * This proxies the request to the Python backend
 */
export async function POST(request: Request) {
  try {
    // Get API URL from environment variable or use default
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
    
    // Log the request for debugging
    console.log('API Request to /api/run_aws_cli with URL:', apiUrl);
    
    // Get the request body
    const body = await request.json();
    console.log('Request body:', body);
    
    // Forward the request to the Python backend
    const response = await fetch(`${apiUrl}/api/run_aws_cli`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    if (!response.ok) {
      throw new Error(`Backend error: ${response.status} ${response.statusText}`);
    }
    
    // Get the response data
    const data = await response.json();
    console.log('Response received from backend:', data);
    
    // Return the response
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in run_aws_cli API route:', error);
    return NextResponse.json(
      { 
        error: 'Failed to run AWS CLI command',
        message: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
} 
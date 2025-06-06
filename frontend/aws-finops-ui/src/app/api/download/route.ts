import { NextRequest, NextResponse } from 'next/server';

/**
 * API route handler for downloading files
 * This proxies the request to the Python backend
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { filename: string } }
) {
  try {
    // Get API URL from environment variable or use default
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
    
    // Get filename from query params
    const url = new URL(request.url);
    const filename = url.pathname.split('/').pop();
    
    if (!filename) {
      return NextResponse.json(
        { error: 'Missing filename parameter' },
        { status: 400 }
      );
    }
    
    // Log the request for debugging
    console.log(`API Request to download file: ${filename}`);
    
    // Forward the request to the Python backend
    const response = await fetch(`${apiUrl}/api/download/${encodeURIComponent(filename)}`);
    
    if (!response.ok) {
      throw new Error(`Backend error: ${response.status} ${response.statusText}`);
    }
    
    // Get the file content
    const data = await response.blob();
    
    // Create a response with the file content
    const headers = new Headers();
    headers.set('Content-Disposition', `attachment; filename=${filename}`);
    headers.set('Content-Type', response.headers.get('Content-Type') || 'application/octet-stream');
    
    return new NextResponse(data, { 
      status: 200, 
      headers
    });
  } catch (error) {
    console.error('Error in download API route:', error);
    return NextResponse.json(
      { 
        error: 'Failed to download file',
        message: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
} 
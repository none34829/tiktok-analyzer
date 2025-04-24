import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

// API base URL from environment variable or default to production URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://tiktok-analyzer-production.up.railway.app';

export async function GET(request: NextRequest) {
  try {
    // Get the video URL from the query parameter
    const searchParams = request.nextUrl.searchParams;
    const url = searchParams.get('url');
    const proxy = searchParams.get('proxy') === 'true';

    if (!url) {
      return NextResponse.json({ error: 'Missing video URL parameter' }, { status: 400 });
    }
    
    // If proxy=true, fetch the video and return it directly to avoid CORS issues
    if (proxy) {
      try {
        console.log(`Proxying video download for: ${url}`);
        const response = await axios.get(url, {
          responseType: 'arraybuffer',
          timeout: 30000
        });
        
        // Get content type from response or default to mp4
        const contentType = response.headers['content-type'] || 'video/mp4';
        
        // Return the video data directly with appropriate headers
        return new NextResponse(response.data, {
          status: 200,
          headers: {
            'Content-Type': contentType,
            'Content-Disposition': 'attachment; filename="tiktok-video.mp4"'
          }
        });
      } catch (proxyError) {
        console.error('Error proxying video:', proxyError);
        return NextResponse.json(
          { error: 'Failed to proxy video download', url: url },
          { status: 502 }
        );
      }
    }
    
    // If the URL is already a CDN URL, return it directly
    if (url.includes('tiktokcdn')) {
      console.log('Direct CDN URL detected in API route, returning directly');
      return NextResponse.json({ url: url, source: 'direct_cdn' });
    }

    // Proxy the request to the backend API
    const response = await axios.get(`${API_BASE_URL}/download-video?video_url=${encodeURIComponent(url)}`, {
      timeout: 15000, // 15 second timeout
    });
    
    // Standardize the response format to always use 'url' as the key
    const responseData = { ...response.data };
    if (responseData.play_url && !responseData.url) {
      responseData.url = responseData.play_url;
    }

    // Return the response data from the backend
    return NextResponse.json(responseData);
  } catch (error) {
    console.error('Error downloading video:', error);
    
    // Handle different types of errors
    if (axios.isAxiosError(error)) {
      if (error.code === 'ECONNABORTED') {
        return NextResponse.json({ error: 'Request timeout' }, { status: 504 });
      }
      
      if (error.response) {
        return NextResponse.json(
          { error: error.response.data?.detail || 'Error from backend API' },
          { status: error.response.status }
        );
      }
    }
    
    return NextResponse.json({ error: 'Failed to download video' }, { status: 500 });
  }
} 
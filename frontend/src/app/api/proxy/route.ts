import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const body = await request.json();
  const endpoint = request.nextUrl.searchParams.get('endpoint') || '';
  
  try {
    const response = await fetch(`https://tiktok-analyzer-production.up.railway.app/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json({ error: 'API request failed' }, { status: 500 });
  }
}

export async function GET(request: NextRequest) {
  const endpoint = request.nextUrl.searchParams.get('endpoint') || '';
  const url = new URL(request.url);
  
  try {
    const response = await fetch(`https://tiktok-analyzer-production.up.railway.app/${endpoint}${url.search}`);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json({ error: 'API request failed' }, { status: 500 });
  }
}

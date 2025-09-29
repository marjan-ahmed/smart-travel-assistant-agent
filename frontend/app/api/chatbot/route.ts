import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const { message } = await req.json();

  // Forward the message to the backend API (assume running at localhost:8001/chat)
  try {
    const backendRes = await fetch('http://localhost:8001/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    if (!backendRes.ok) {
      throw new Error('Backend error');
    }
    const data = await backendRes.json();
    return NextResponse.json({ response: data.response });
  } catch (err) {
    console.error('Backend error:', err);
    return NextResponse.json({ response: 'Sorry, there was an error connecting to the travel assistant.' }, { status: 500 });
  }
}
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface AnalysisResponse {
  data: Record<string, unknown>;
  status: string;
  message?: string;
}

export interface TikTokUser {
  id: string;
  username: string;
  display_name: string;
  bio: string;
  follower_count: number;
  following_count: number;
  likes_count: number;
  verified: boolean;
  profile_pic: string;
  analysis_result?: {
    score: number;
    explanation: string;
  };
}

export async function analyzeUserContent(userId: string, query: string): Promise<AnalysisResponse> {
  try {
    const response = await fetch(`${BASE_URL}/analyze-content`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        query: query,
      }),
    });

    if (!response.ok) {
      throw new Error(`Analysis failed: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error('Error analyzing user content:', error);
    throw error;
  }
}

export interface SmartSearchResponse {
  username: string;
  confidence: number;
  explanation: string;
}

export async function smartSearch(query: string): Promise<SmartSearchResponse> {
  try {
    // Format the query to be more specific for finding exact users
    const formattedQuery = `Find the exact TikTok username for: ${query}. If you know the exact username, return it. If not, say "No specific user found".`;
    
    const response = await fetch(`${BASE_URL}/smart-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: formattedQuery,
      }),
    });

    if (!response.ok) {
      throw new Error(`Smart search failed: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error('Error performing smart search:', error);
    throw error;
  }
}

export async function getUserByUsername(username: string): Promise<TikTokUser> {
  try {
    const response = await fetch(`${BASE_URL}/user-details/${username}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get user details: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error('Error getting user details:', error);
    throw error;
  }
} 
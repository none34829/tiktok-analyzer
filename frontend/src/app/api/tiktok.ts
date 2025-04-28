// Use this flag to toggle between local and production
const USE_LOCAL_API = true; // Set to false when you want to use Railway

// Determine which backend to use
const PRODUCTION_URL = 'https://tiktok-analyzer-production.up.railway.app';
const LOCAL_URL = 'http://localhost:8000';

// If environment variable is set, it overrides the above
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || (USE_LOCAL_API ? LOCAL_URL : PRODUCTION_URL);

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

export interface VideoInfo {
  id: string;
  caption: string;
  thumbnail_url: string;
  thumbnail_analysis?: string;
  relevance_score?: number;
}

export interface EnhancedUserResult {
  username: string;
  display_name: string;
  sec_user_id: string;
  user_id: string;
  bio: string;
  follower_count: number;
  following_count: number;
  likes_count: number;
  verified: boolean;
  profile_pic: string;
  profile_analysis?: string;
  bio_analysis?: string;
  videos?: VideoInfo[];
  overall_relevance_score?: number;
  overall_analysis?: string;
}

export interface EnhancedSearchResponse {
  original_query: string;
  enhanced_query: string;
  users: EnhancedUserResult[];
  search_explanation: string;
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

export async function enhancedSearch(query: string, count: number = 5, detailedAnalysis: boolean = true): Promise<EnhancedSearchResponse> {
  try {
    const response = await fetch(`${BASE_URL}/enhanced-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query,
        count: count,
        detailed_analysis: detailedAnalysis
      }),
    });

    if (!response.ok) {
      throw new Error(`Enhanced search failed: ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error('Error performing enhanced search:', error);
    throw error;
  }
}

export interface PreciseUserMatch {
  username: string;
  display_name: string;
  bio: string;
  follower_count: number;
  profile_pic: string;
  why_matches: string;
  relevance_score: number;
  videos?: Array<{caption: string; thumbnail: string}>;
}

// This interface represents what the backend actually returns
interface BackendPreciseSearchResponse {
  query: string;
  account_type: string;
  required_criteria: string[];
  search_keywords: string[];
  search_strategies: string[];
  exact_matches: {
    user: {
      username: string;
      display_name: string;
      bio: string;
      follower_count: number;
      profile_pic: string;
    };
    relevance_score: number;
    explanation: string;
    videos: Array<{caption: string; thumbnail: string}>;
    has_verified_videos: boolean;
  }[];
  partial_matches: {
    user: {
      username: string;
      display_name: string;
      bio: string;
      follower_count: number;
      profile_pic: string;
    };
    relevance_score: number;
    explanation: string;
    videos: Array<{caption: string; thumbnail: string}>;
    has_verified_videos: boolean;
  }[];
}

// This is what our frontend components expect
export interface TikTokVideo {
  caption?: string;
  desc?: string;
  thumbnail?: string;
  thumbnail_url?: string;
}

export interface WebEnhancedUserMatch {
  username: string;
  display_name: string;
  bio: string;
  follower_count: number;
  profile_pic: string;
  why_matches: string;
  relevance_score: number;
  discovery_method: string;
  videos?: Array<TikTokVideo | {caption: string; thumbnail: string}>;
}

export interface WebEnhancedSearchResponse {
  query: string;
  required_criteria: string[];
  matches: WebEnhancedUserMatch[];
  search_strategy: string;
  usernames_found: number;
  profiles_analyzed: number;
}

export interface PreciseSearchResponse {
  query: string;
  required_criteria: string[];
  matches: PreciseUserMatch[];
  search_strategy: string;
}

export async function webEnhancedSearch(query: string, maxResults: number = 5, minRelevanceScore: number = 0.5): Promise<WebEnhancedSearchResponse> {
  try {
    const response = await fetch(`${BASE_URL}/web-enhanced-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query,
        max_results: maxResults,
        min_relevance_score: minRelevanceScore
      }),
    });

    if (!response.ok) {
      throw new Error(`Web-enhanced search failed: ${response.status}`);
    }

    const data = await response.json();
    
    // Format videos if needed
    if (data.matches && Array.isArray(data.matches)) {
      data.matches.forEach((match: WebEnhancedUserMatch) => {
        if (match.videos && Array.isArray(match.videos)) {
          // Transform video format if necessary
          match.videos = match.videos.map((video: TikTokVideo) => ({
            caption: video.caption || video.desc || '',
            thumbnail: video.thumbnail || video.thumbnail_url || ''
          }));
        }
      });
    }

    return data;
  } catch (error) {
    console.error('Error performing web-enhanced search:', error);
    throw error;
  }
}

export async function preciseSearch(query: string, maxResults: number = 5): Promise<PreciseSearchResponse> {
  try {
    const response = await fetch(`${BASE_URL}/precise-search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query,
        max_results: maxResults
      }),
    });

    if (!response.ok) {
      throw new Error(`Precise search failed: ${response.status}`);
    }

    const data: BackendPreciseSearchResponse = await response.json();
    
    // Transform backend response to match our frontend interface
    const transformedData: PreciseSearchResponse = {
      query: data.query,
      required_criteria: data.required_criteria,
      search_strategy: data.search_strategies?.join(', ') || 'Multiple strategies',
      matches: []
    };

    // Add exact matches first
    if (data.exact_matches && Array.isArray(data.exact_matches)) {
      data.exact_matches.forEach(match => {
        transformedData.matches.push({
          username: match.user.username,
          display_name: match.user.display_name,
          bio: match.user.bio,
          follower_count: match.user.follower_count,
          profile_pic: match.user.profile_pic,
          why_matches: match.explanation,
          relevance_score: match.relevance_score,
          videos: match.videos
        });
      });
    }

    // Optionally add partial matches if we don't have enough results
    if (transformedData.matches.length < maxResults && data.partial_matches && Array.isArray(data.partial_matches)) {
      data.partial_matches.forEach(match => {
        // Only add if we still need more results
        if (transformedData.matches.length < maxResults) {
          transformedData.matches.push({
            username: match.user.username,
            display_name: match.user.display_name,
            bio: match.user.bio,
            follower_count: match.user.follower_count,
            profile_pic: match.user.profile_pic,
            why_matches: `Partial match: ${match.explanation}`,
            relevance_score: match.relevance_score,
            videos: match.videos
          });
        }
      });
    }

    return transformedData;
  } catch (error) {
    console.error('Error performing precise search:', error);
    throw error;
  }
}
"use client";

import { useState } from "react";
import { useForm, SubmitHandler } from "react-hook-form";
import axios, { AxiosError } from "axios";
import Image from "next/image";

// Types
interface UserCriteria {
  min_followers?: number;
  max_followers?: number;
  min_following?: number;
  max_following?: number;
  min_likes?: number;
  max_likes?: number;
  verified?: boolean;
}

interface SearchFormInputs {
  query: string;
  min_followers: string;
  max_followers: string;
  min_following: string;
  max_following: string;
  min_likes: string;
  max_likes: string;
  verified: string;
  count: string;
  deep_analysis: boolean;
}

interface AnalysisResult {
  relevant: boolean;
  score: number;
  explanation: string;
  image_analysis?: string;
  thumbnail_analysis?: string;
}

interface TikTokUser {
  id: string;
  username: string;
  display_name: string;
  bio: string;
  follower_count: number;
  following_count: number;
  likes_count: number;
  verified: boolean;
  profile_pic: string;
  analysis_result?: AnalysisResult;
}

interface TikTokPost {
  id: string;
  desc: string;
  create_time: number;
  video: {
    cover: string | { url_list?: string[] };
    download_addr: string | { url_list?: string[] };
    play_addr: string | { url_list?: string[] };
  };
  statistics: {
    comment_count: number;
    digg_count: number;
    share_count: number;
    play_count: number;
  };
  author?: {
    nickname?: string;
    unique_id?: string;
    avatar_thumb?: {
      url_list?: string[];
    };
    avatar_base64?: string;
  };
}

interface TrendingCreator {
  user_info?: {
    uniqueId?: string;
    unique_id?: string;
    nickname?: string;
    avatarMedium?: string;
    avatar_medium?: string;
    followerCount?: number;
    follower_count?: number;
    heartCount?: number;
    heart_count?: number;
    diggCount?: number;
    digg_count?: number;
    verified?: boolean;
  };
  uniqueId?: string;
  unique_id?: string;
  nickname?: string;
  avatarMedium?: string;
  avatar_medium?: string;
  followerCount?: number;
  follower_count?: number;
  heartCount?: number;
  heart_count?: number;
  diggCount?: number;
  digg_count?: number;
  verified?: boolean;
}

// API error response interface
interface ApiErrorResponse {
  detail?: string;
  message?: string;
}

// API URL
const API_BASE_URL = "http://localhost:8000";

// Add this interface where appropriate in your file, possibly near other interfaces
interface DownloadAddr {
  url_list?: string[];
  [key: string]: unknown;
}

interface PostSearchFormInputs {
  keyword: string;
  count: string;
  publish_time: string;
  sort_type: string;
}

interface AnalysisResponse {
  user_id: string;
  query: string;
  analysis: AnalysisResult;
  status?: "success" | "limited" | "error";
  error?: string;
}

export default function Home() {
  const [searchResults, setSearchResults] = useState<TikTokUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exportFormat, setExportFormat] = useState<"json" | "csv">("json");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activeTab, setActiveTab] = useState<'search' | 'trending' | 'posts'>('search');
  const [trendingCreators, setTrendingCreators] = useState<TrendingCreator[]>([]);
  const [loadingTrending, setLoadingTrending] = useState(false);
  const [userPosts, setUserPosts] = useState<{[key: string]: TikTokPost[]}>({});
  const [loadingPosts, setLoadingPosts] = useState<{[key: string]: boolean}>({});
  const [downloadingVideo, setDownloadingVideo] = useState<{[key: string]: boolean}>({});
  const [downloadDisabled, setDownloadDisabled] = useState(false);
  const [postSearchResults, setPostSearchResults] = useState<TikTokPost[]>([]);
  const [loadingPostSearch, setLoadingPostSearch] = useState(false);
  const [selectedUser, setSelectedUser] = useState<TikTokUser | null>(null);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<SearchFormInputs>();

  const {
    register: registerPostSearch,
    handleSubmit: handleSubmitPostSearch,
    formState: { errors: postSearchErrors },
  } = useForm<PostSearchFormInputs>();

  const queryValue = watch("query");

  const onSubmit: SubmitHandler<SearchFormInputs> = async (data) => {
    setLoading(true);
    setError(null);
    setSearchResults([]);
    console.log("Search submitted with query:", data.query);

    try {
      // Prepare the criteria object
      const criteria: UserCriteria = {};
      
      if (data.min_followers) criteria.min_followers = parseInt(data.min_followers);
      if (data.max_followers) criteria.max_followers = parseInt(data.max_followers);
      if (data.min_following) criteria.min_following = parseInt(data.min_following);
      if (data.max_following) criteria.max_following = parseInt(data.max_following);
      if (data.min_likes) criteria.min_likes = parseInt(data.min_likes);
      if (data.max_likes) criteria.max_likes = parseInt(data.max_likes);
      if (data.verified === "true") criteria.verified = true;
      if (data.verified === "false") criteria.verified = false;

      console.log("Sending request to:", `${API_BASE_URL}/search-users`);
      
      const response = await axios.post(`${API_BASE_URL}/search-users`, {
        query: data.query,
        criteria,
        count: data.count ? parseInt(data.count) : 20,
        deep_analysis: data.deep_analysis
      });

      console.log("Received response:", response.data);
      
      if (Array.isArray(response.data) && response.data.length === 0) {
        setError("No results found. Try a different search query.");
      }
      
      setSearchResults(response.data);
    } catch (err: unknown) {
      const axiosError = err as AxiosError<ApiErrorResponse>;
      console.error("Full error:", axiosError);
      const errorMessage = axiosError.response?.data?.detail || 
                          axiosError.response?.data?.message || 
                          "An error occurred while searching";
      setError(errorMessage);
      console.error("Search error:", err);
    } finally {
      setLoading(false);
    }
  };

  const onPostSearchSubmit: SubmitHandler<PostSearchFormInputs> = async (data) => {
    setLoadingPostSearch(true);
    setError(null);
    setPostSearchResults([]);
    console.log("Post search submitted with keyword:", data.keyword);

    try {
      const response = await axios.post(`${API_BASE_URL}/search-posts`, {
        keyword: data.keyword,
        count: data.count ? parseInt(data.count) : 20,
        publish_time: data.publish_time ? parseInt(data.publish_time) : 0,
        sort_type: data.sort_type ? parseInt(data.sort_type) : 0,
        offset: 0,
        use_filters: 0,
      });

      console.log("Received post search response:", response.data);
      
      if (response.data && response.data.aweme_list && Array.isArray(response.data.aweme_list)) {
        setPostSearchResults(response.data.aweme_list);
        if (response.data.aweme_list.length === 0) {
          setError(`No posts found for "${data.keyword}". Try different keywords or filters.`);
        }
      } else {
        setError("Invalid response format. Could not find posts.");
      }
    } catch (err: unknown) {
      const axiosError = err as AxiosError<ApiErrorResponse>;
      console.error("Full error:", axiosError);
      const errorMessage = axiosError.response?.data?.detail || 
                          axiosError.response?.data?.message || 
                          "An error occurred while searching posts";
      setError(errorMessage);
      console.error("Post search error:", err);
    } finally {
      setLoadingPostSearch(false);
    }
  };

  const exportData = () => {
    if (searchResults.length === 0) return;

    let content: string;
    let filename: string;
    
    if (exportFormat === "json") {
      content = JSON.stringify(searchResults, null, 2);
      filename = "tiktok_users.json";
    } else {
      // Create CSV content
      const headers = "username,display_name,follower_count,following_count,likes_count,verified,relevance_score,relevant\n";
      const rows = searchResults.map(user => 
        `${user.username},${user.display_name.replace(/,/g, " ")},${user.follower_count},${user.following_count},${user.likes_count},${user.verified},${user.analysis_result?.score || 0},${user.analysis_result?.relevant || false}`
      ).join("\n");
      
      content = headers + rows;
      filename = "tiktok_users.csv";
    }
    
    // Create download
    const blob = new Blob([content], { type: exportFormat === "json" ? "application/json" : "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const fetchTrendingCreators = async () => {
    setLoadingTrending(true);
    setError(null);
    
    try {
      const response = await axios.get(`${API_BASE_URL}/trending-creators`);
      console.log("Trending creators:", response.data);
      
      if (response.data && Array.isArray(response.data.user_list)) {
        setTrendingCreators(response.data.user_list);
      } else {
        setTrendingCreators([]);
        setError("Could not find trending creators data");
      }
    } catch (err: unknown) {
      const axiosError = err as AxiosError<ApiErrorResponse>;
      const errorMessage = axiosError.response?.data?.detail || 
                          axiosError.response?.data?.message || 
                          "An error occurred while fetching trending creators";
      setError(errorMessage);
      console.error("Error fetching trending creators:", err);
    } finally {
      setLoadingTrending(false);
    }
  };

  const fetchUserPosts = async (userId: string) => {
    setLoadingPosts(prev => ({ ...prev, [userId]: true }));
    
    try {
      const response = await axios.get(`${API_BASE_URL}/user-posts/${userId}?count=5`);
      console.log(`Posts for user ${userId}:`, response.data);
      
      // Handle different response formats
      let posts: TikTokPost[] = [];
      if (response.data && response.data.aweme_list) {
        posts = response.data.aweme_list;
      }
      
      setUserPosts(prev => ({ ...prev, [userId]: posts }));
    } catch (err) {
      console.error(`Error fetching posts for user ${userId}:`, err);
    } finally {
      setLoadingPosts(prev => ({ ...prev, [userId]: false }));
    }
  };

  async function downloadVideo(videoUrl: string, postKey: string) {
    try {
      setDownloadDisabled(true);
      
      // Update download state for this video
      setDownloadingVideo(prev => ({
        ...prev,
        [postKey]: true
      }));
      
      console.log(`Downloading video for post ${postKey}`);
      
      // For direct CDN URLs, trigger proper download instead of just opening
      if (videoUrl.includes('tiktokcdn')) {
        console.log('Direct CDN URL detected, triggering download');
        // Create a downloadable link
        const filename = `tiktok-video-${postKey}.mp4`;
        triggerDownload(videoUrl, filename);
        return;
      }
      
      // First try the local API route
      try {
        const response = await fetch(`/api/download?url=${encodeURIComponent(videoUrl)}`);
        
        if (response.ok) {
          const data = await response.json();
          const videoDownloadUrl = data.url;
          
          if (videoDownloadUrl) {
            console.log(`Success - downloading URL: ${videoDownloadUrl.substring(0, 50)}...`);
            
            // Create proper download with filename
            const filename = `tiktok-video-${postKey}.mp4`;
            triggerDownload(videoDownloadUrl, filename);
            return;
          }
        }
        
        // If we get here, the API route failed but didn't throw
        console.log('API route failed, trying backend directly');
      } catch (apiError) {
        console.error('Error with API route:', apiError);
        console.log('Falling back to direct backend call');
      }
      
      // Fallback to direct backend call
      const backendResponse = await axios.get(`${API_BASE_URL}/download-video?video_url=${encodeURIComponent(videoUrl)}`);
      console.log("Backend response:", backendResponse.data);
      
      // Handle different response formats - now standardized to always use 'url'
      const backendVideoUrl = backendResponse.data.url;
      
      if (!backendVideoUrl) {
        throw new Error('No video URL found in response');
      }
      
      // Create proper download instead of just opening in a tab
      const filename = `tiktok-video-${postKey}.mp4`;
      triggerDownload(backendVideoUrl, filename);
      
    } catch (error) {
      console.error('Error downloading video:', error);
      alert(`Error downloading video. Please try again later.`);
    } finally {
      setDownloadingVideo(prev => ({ ...prev, [postKey]: false }));
      setDownloadDisabled(false);
    }
  }
  
  // Helper function to trigger an actual download using blob
  function triggerDownload(url: string, filename: string) {
    // Use our proxy API endpoint instead of fetching directly to avoid CORS issues
    console.log(`Triggering download via proxy: ${filename}`);
    
    // Create a download link that goes through our proxy
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = `/api/download?url=${encodeURIComponent(url)}&proxy=true`;
    a.download = filename;
    
    // Append to the document and trigger click
    document.body.appendChild(a);
    a.click();
    
    // Clean up
    setTimeout(() => {
      document.body.removeChild(a);
    }, 100);
  }

  const runDeepAnalysis = async (userId: string, query: string) => {
    setIsAnalyzing(true);
    try {
      const response = await axios.post<AnalysisResponse>(`${API_BASE_URL}/analyze-content`, {
        user_id: userId,
        query: query || queryValue || ""
      });
      
      // Update UI based on status
      const analysisResponse = response.data;
      
      // Show API quota warning if needed
      if (analysisResponse.status === "limited") {
        setError("OpenAI API quota exceeded. Using basic analysis instead.");
      } else if (analysisResponse.status === "error") {
        setError(`Analysis error: ${analysisResponse.error}`);
      }
      
      // Find the user in searchResults and update
      const updatedResults = searchResults.map(user => {
        if (user.id === userId) {
          return {
            ...user,
            analysis_result: analysisResponse.analysis
          };
        }
        return user;
      });
      
      setSearchResults(updatedResults);
      
      // If we have a selected user, update it too
      if (selectedUser && selectedUser.id === userId) {
        setSelectedUser({
          ...selectedUser,
          analysis_result: analysisResponse.analysis
        });
      }
      
    } catch (error) {
      console.error("Error running deep analysis:", error);
      setError("Failed to run analysis. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const openAnalysisModal = (user: TikTokUser) => {
    setSelectedUser(user);
    setShowAnalysisModal(true);
  };

  const closeAnalysisModal = () => {
    setShowAnalysisModal(false);
    setSelectedUser(null);
  };

  return (
    <main className="min-h-screen bg-gray-100">
      {/* Analysis Modal */}
      {showAnalysisModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-xl font-semibold text-black">AI Analysis for @{selectedUser.username}</h2>
                <button 
                  onClick={closeAnalysisModal}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <span className="text-2xl">&times;</span>
                </button>
              </div>
              
              <div className="mb-6 flex items-center">
                {selectedUser.profile_pic && (
                  <div className="relative w-16 h-16 rounded-full overflow-hidden mr-4">
                    <Image 
                      src={`data:image/jpeg;base64,${selectedUser.profile_pic}`}
                      alt={`${selectedUser.display_name} profile`}
                      width={64}
                      height={64}
                      className="object-cover"
                      unoptimized
                    />
                  </div>
                )}
                <div>
                  <h3 className="text-lg font-semibold text-black">{selectedUser.display_name}</h3>
                  <p className="text-gray-600">@{selectedUser.username} {selectedUser.verified && "✓"}</p>
                </div>
              </div>
              
              {selectedUser.analysis_result ? (
                <div className="space-y-6">
                  <div className={`p-4 rounded-md ${
                    selectedUser.analysis_result.relevant ? 'bg-green-50 border border-green-100' : 'bg-red-50 border border-red-100'
                  }`}>
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium text-black">
                        {selectedUser.analysis_result.relevant ? 'Relevant' : 'Not Relevant'}
                      </span>
                      <span className="font-semibold text-black">
                        Score: {(selectedUser.analysis_result.score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-800">{selectedUser.analysis_result.explanation}</p>
                    
                    {selectedUser.analysis_result.explanation.includes("quota exceeded") && (
                      <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
                        <p><strong>Note:</strong> OpenAI API quota has been exceeded. Using basic keyword matching instead of AI analysis.</p>
                      </div>
                    )}
                  </div>
                  
                  {selectedUser.analysis_result.image_analysis && 
                   selectedUser.analysis_result.image_analysis !== "Image analysis failed" && 
                   selectedUser.analysis_result.image_analysis !== "OpenAI API quota exceeded" && (
                    <div className="bg-blue-50 border border-blue-100 p-4 rounded-md">
                      <h4 className="font-medium text-black mb-2">Profile Image Analysis</h4>
                      <p className="text-sm text-gray-800 whitespace-pre-line">{selectedUser.analysis_result.image_analysis}</p>
                    </div>
                  )}
                  
                  {selectedUser.analysis_result.thumbnail_analysis && 
                   selectedUser.analysis_result.thumbnail_analysis !== "Thumbnail analysis failed" && 
                   selectedUser.analysis_result.thumbnail_analysis !== "OpenAI API quota exceeded" && (
                    <div className="bg-purple-50 border border-purple-100 p-4 rounded-md">
                      <h4 className="font-medium text-black mb-2">Content Thumbnail Analysis</h4>
                      <p className="text-sm text-gray-800 whitespace-pre-line">{selectedUser.analysis_result.thumbnail_analysis}</p>
                    </div>
                  )}
                  
                  {(selectedUser.analysis_result.image_analysis === "OpenAI API quota exceeded" || 
                    selectedUser.analysis_result.thumbnail_analysis === "OpenAI API quota exceeded") && (
                    <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-md">
                      <h4 className="font-medium text-yellow-800 mb-2">OpenAI API Quota Limit</h4>
                      <p className="text-sm text-yellow-800">
                        The OpenAI API quota has been exceeded. Advanced image analysis is unavailable.
                        Please update your OpenAI API key or billing details to continue using advanced analysis features.
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
                  <p className="text-gray-600">Analyzing user content...</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8 text-center text-black">TikTok Analyzer</h1>
        
        <div className="mb-6 flex justify-center">
          <div className="inline-flex rounded-md shadow-sm" role="group">
            <button
              type="button"
              className={`px-6 py-2 text-sm font-medium ${activeTab === 'search' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-50'} border border-gray-200 ${
                  activeTab === 'search' ? 'rounded-l-md' : 'border-l'
                }`}
              onClick={() => setActiveTab('search')}
            >
              Search Users
            </button>
            <button
              type="button"
              className={`px-6 py-2 text-sm font-medium ${activeTab === 'posts' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-50'} border border-gray-200`}
              onClick={() => setActiveTab('posts')}
            >
              Search Posts
            </button>
            <button
              type="button"
              className={`px-6 py-2 text-sm font-medium ${activeTab === 'trending' 
                ? 'bg-blue-600 text-white' 
                : 'bg-white text-gray-700 hover:bg-gray-50'} border border-gray-200 rounded-r-md`}
              onClick={() => {
                setActiveTab('trending');
                fetchTrendingCreators();
              }}
            >
              Trending Creators
            </button>
          </div>
        </div>
        
        {activeTab === 'search' && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <form onSubmit={handleSubmit(onSubmit)}>
              <div className="mb-4">
                <label htmlFor="query" className="block text-sm font-medium text-black mb-1">
                  Search Query
                </label>
                <input
                  id="query"
                  type="text"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                  placeholder="Enter search query (e.g., fashion, cooking, travel)"
                  {...register("query", { required: "Search query is required" })}
                />
                {errors.query && (
                  <p className="mt-1 text-sm text-red-600">{errors.query.message}</p>
                )}
              </div>

              <div className="mb-4">
                <label htmlFor="count" className="block text-sm font-medium text-black mb-1">
                  Number of Results
                </label>
                <input
                  id="count"
                  type="number"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                  placeholder="20"
                  defaultValue="20"
                  {...register("count")}
                />
              </div>

              <div className="mb-4">
                <button 
                  type="button" 
                  className="text-sm text-blue-600 hover:underline"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                >
                  {showAdvanced ? "Hide" : "Show"} Advanced Filters
                </button>
              </div>

              {showAdvanced && (
                <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="min_followers" className="block text-sm font-medium text-black mb-1">
                      Min Followers
                    </label>
                    <input
                      id="min_followers"
                      type="number"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                      placeholder="0"
                      {...register("min_followers")}
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="max_followers" className="block text-sm font-medium text-black mb-1">
                      Max Followers
                    </label>
                    <input
                      id="max_followers"
                      type="number"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                      placeholder="No limit"
                      {...register("max_followers")}
                    />
                  </div>

                  <div>
                    <label htmlFor="min_following" className="block text-sm font-medium text-black mb-1">
                      Min Following
                    </label>
                    <input
                      id="min_following"
                      type="number"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                      placeholder="0"
                      {...register("min_following")}
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="max_following" className="block text-sm font-medium text-black mb-1">
                      Max Following
                    </label>
                    <input
                      id="max_following"
                      type="number"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                      placeholder="No limit"
                      {...register("max_following")}
                    />
                  </div>

                  <div>
                    <label htmlFor="min_likes" className="block text-sm font-medium text-black mb-1">
                      Min Likes
                    </label>
                    <input
                      id="min_likes"
                      type="number"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                      placeholder="0"
                      {...register("min_likes")}
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="max_likes" className="block text-sm font-medium text-black mb-1">
                      Max Likes
                    </label>
                    <input
                      id="max_likes"
                      type="number"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                      placeholder="No limit"
                      {...register("max_likes")}
                    />
                  </div>

                  <div>
                    <label htmlFor="verified" className="block text-sm font-medium text-black mb-1">
                      Verified Status
                    </label>
                    <select
                      id="verified"
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                      {...register("verified")}
                    >
                      <option value="">Any</option>
                      <option value="true">Verified Only</option>
                      <option value="false">Non-Verified Only</option>
                    </select>
                  </div>
                  
                  <div className="md:col-span-2 mt-2">
                    <div className="flex items-center">
                      <input
                        id="deep_analysis"
                        type="checkbox"
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        {...register("deep_analysis")}
                      />
                      <label htmlFor="deep_analysis" className="ml-2 block text-sm text-gray-900">
                        Enable deep AI analysis (profile images, thumbnails)
                      </label>
                    </div>
                  </div>
                </div>
              )}

              <button
                type="submit"
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                disabled={loading}
              >
                {loading ? "Searching..." : "Search"}
              </button>
            </form>
          </div>
        )}

        {/* Error message */}
        {error && activeTab !== 'posts' && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-8">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {activeTab === 'trending' && (
          <div className="mb-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4 text-black">Trending TikTok Creators</h2>
              {loadingTrending ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {trendingCreators.map((creator, index) => {
                    // Extract data from potentially different response formats
                    const user = creator.user_info || creator;
                    const username = user.uniqueId || user.unique_id || "";
                    const displayName = user.nickname || "Unknown";
                    const avatar = user.avatarMedium || user.avatar_medium || "";
                    const followers = user.followerCount || user.follower_count || 0;
                    
                    // Extract likes count from various possible fields
                    const likes = user.heartCount || user.heart_count || user.diggCount || user.digg_count || 0;
                    
                    return (
                      <div key={index} className="bg-white rounded-lg shadow border overflow-hidden">
                        <div className="p-5">
                          <div className="flex items-center mb-4">
                            {avatar && (
                              <div className="relative w-16 h-16 rounded-full overflow-hidden mr-4">
                                <Image 
                                  src={avatar}
                                  alt={`${displayName} profile`}
                                  width={64}
                                  height={64}
                                  className="object-cover"
                                  unoptimized
                                />
                              </div>
                            )}
                            <div>
                              <h3 className="text-lg font-semibold text-black">{displayName}</h3>
                              <p className="text-gray-800">@{username} {user.verified && "✓"}</p>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-2 mb-4 text-center">
                            <div>
                              <p className="text-lg font-semibold text-black">{followers.toLocaleString()}</p>
                              <p className="text-xs text-gray-800">Followers</p>
                            </div>
                            <div>
                              <p className="text-lg font-semibold text-black">{likes.toLocaleString()}</p>
                              <p className="text-xs text-gray-800">Likes</p>
                            </div>
                          </div>
                          
                          <div className="mt-4">
                            {username ? (
                              <a 
                                href={`https://www.tiktok.com/@${username}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline text-sm"
                              >
                                View TikTok Profile →
                              </a>
                            ) : (
                              <span className="text-gray-400 text-sm">Profile link unavailable</span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'search' && searchResults.length > 0 && (
          <div className="mb-6 flex justify-between items-center">
            <h2 className="text-xl font-semibold text-black">Search Results: {searchResults.length} users found</h2>
            <div className="flex space-x-2">
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as "json" | "csv")}
                className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 text-black"
              >
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
              </select>
              <button
                onClick={exportData}
                className="bg-green-600 text-white px-4 py-1 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors"
              >
                Export
              </button>
            </div>
          </div>
        )}

        {activeTab === 'search' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {searchResults.map((user) => (
              <div key={user.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                <div className="p-5">
                  <div className="flex items-center mb-4">
                    {user.profile_pic && (
                      <div className="relative w-16 h-16 rounded-full overflow-hidden mr-4">
                        <Image 
                          src={`data:image/jpeg;base64,${user.profile_pic}`}
                          alt={`${user.display_name} profile`}
                          width={64}
                          height={64}
                          className="object-cover"
                          unoptimized
                        />
                      </div>
                    )}
                    <div>
                      <h3 className="text-lg font-semibold text-black">{user.display_name}</h3>
                      <p className="text-gray-800">@{user.username} {user.verified && "✓"}</p>
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-800 mb-4 h-12 overflow-hidden">{user.bio}</p>
                  
                  <div className="grid grid-cols-3 gap-2 mb-4 text-center">
                    <div>
                      <p className="text-lg font-semibold text-black">{user.follower_count.toLocaleString()}</p>
                      <p className="text-xs text-gray-800">Followers</p>
                    </div>
                    <div>
                      <p className="text-lg font-semibold text-black">{user.following_count.toLocaleString()}</p>
                      <p className="text-xs text-gray-800">Following</p>
                    </div>
                    <div>
                      <p className="text-lg font-semibold text-black">{user.likes_count.toLocaleString()}</p>
                      <p className="text-xs text-gray-800">Likes</p>
                    </div>
                  </div>
                  
                  {user.analysis_result && (
                    <div className={`p-3 rounded-md ${
                      user.analysis_result.relevant ? 'bg-green-50 border border-green-100' : 'bg-red-50 border border-red-100'
                    }`}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-medium text-black">
                          {user.analysis_result.relevant ? 'Relevant' : 'Not Relevant'}
                        </span>
                        <span className="font-semibold text-black">
                          Score: {(user.analysis_result.score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-xs text-gray-800">{user.analysis_result.explanation}</p>
                      
                      {(user.analysis_result.image_analysis || user.analysis_result.thumbnail_analysis) && (
                        <button
                          onClick={() => openAnalysisModal(user)}
                          className="mt-2 text-xs text-blue-600 hover:underline"
                        >
                          View detailed AI analysis
                        </button>
                      )}
                    </div>
                  )}
                  
                  <div className="mt-4 flex flex-wrap gap-2">
                    {user.username && (
                      <a 
                        href={`https://www.tiktok.com/@${user.username}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline text-sm"
                      >
                        View TikTok Profile →
                      </a>
                    )}
                    
                    {user.id && !userPosts[user.id] && (
                      <button
                        onClick={() => fetchUserPosts(user.id)}
                        className="text-sm px-3 py-1 rounded bg-purple-600 text-white hover:bg-purple-700 focus:outline-none"
                        disabled={loadingPosts[user.id]}
                      >
                        {loadingPosts[user.id] ? 'Loading...' : 'View Recent Posts'}
                      </button>
                    )}
                    
                    {user.id && (
                      <button
                        onClick={() => runDeepAnalysis(user.id, queryValue)}
                        className="text-sm px-3 py-1 rounded bg-indigo-600 text-white hover:bg-indigo-700 focus:outline-none"
                        disabled={isAnalyzing}
                      >
                        {isAnalyzing ? 'Analyzing...' : 'Run Deep Analysis'}
                      </button>
                    )}
                  </div>
                  
                  {/* Display user posts */}
                  {user.id && userPosts[user.id] && userPosts[user.id].length > 0 && (
                    <div className="mt-4 border-t pt-4">
                      <h4 className="text-md font-medium text-black mb-2">Recent Posts</h4>
                      <div className="space-y-3">
                        {userPosts[user.id].map((post, index) => {
                          // Create a unique, stable key for each post
                          const postKey = post.id || `post-${user.id}-${index}`;
                          let videoUrl: string | undefined;
                          if (post.video && post.video.download_addr) {
                            if (typeof post.video.download_addr === 'string') {
                              videoUrl = post.video.download_addr;
                            } else if (
                              typeof post.video.download_addr === 'object' && 
                              post.video.download_addr !== null
                            ) {
                              const downloadAddr = post.video.download_addr as DownloadAddr;
                              if (downloadAddr.url_list && Array.isArray(downloadAddr.url_list) && downloadAddr.url_list.length > 0) {
                                videoUrl = downloadAddr.url_list[0];
                              }
                            }
                          }
                          return (
                            <div key={postKey} className="border rounded-md p-2">
                              <p className="text-xs text-gray-800 mb-2 line-clamp-2">{post.desc}</p>
                              <div className="flex justify-between items-center">
                                <div className="text-xs text-gray-700">
                                  <span className="mr-2">♥ {post.statistics?.digg_count?.toLocaleString() || 0}</span>
                                  <span className="mr-2">💬 {post.statistics?.comment_count?.toLocaleString() || 0}</span>
                                  <span>▶ {post.statistics?.play_count?.toLocaleString() || 0}</span>
                                </div>
                                <button 
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    if (videoUrl) {
                                      downloadVideo(videoUrl, postKey);
                                    }
                                  }}
                                  disabled={downloadingVideo[postKey] || downloadDisabled || !videoUrl}
                                  className="text-xs px-2 py-1 rounded bg-green-600 text-white hover:bg-green-700 focus:outline-none"
                                >
                                  {downloadingVideo[postKey] ? 'Downloading...' : 'Download'}
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                      <button 
                        onClick={() => setUserPosts(prev => ({ ...prev, [user.id]: [] }))}
                        className="mt-2 text-xs text-gray-500 hover:underline"
                      >
                        Hide posts
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        
        {searchResults.length > 0 && activeTab === 'search' && (
          <div className="mt-8 text-center text-sm text-gray-800">
            <p>AI-powered analysis is performed using profile data and image content</p>
          </div>
        )}
        
        {(loading || loadingTrending) && (
          <div className="flex justify-center my-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        )}

        {/* Post search form */}
        {activeTab === 'posts' && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <form onSubmit={handleSubmitPostSearch(onPostSearchSubmit)}>
              <div className="mb-4">
                <label htmlFor="keyword" className="block text-sm font-medium text-black mb-1">
                  Search Posts
                </label>
                <input
                  id="keyword"
                  type="text"
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                  placeholder="Enter keywords to search for posts"
                  {...registerPostSearch("keyword", { required: "Keyword is required" })}
                />
                {postSearchErrors.keyword && (
                  <p className="mt-1 text-sm text-red-600">{postSearchErrors.keyword.message}</p>
                )}
              </div>

              <div className="mb-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label htmlFor="count" className="block text-sm font-medium text-black mb-1">
                    Number of Results
                  </label>
                  <input
                    id="count"
                    type="number"
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                    placeholder="20"
                    defaultValue="20"
                    {...registerPostSearch("count")}
                  />
                </div>

                <div>
                  <label htmlFor="publish_time" className="block text-sm font-medium text-black mb-1">
                    Time Period
                  </label>
                  <select
                    id="publish_time"
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                    {...registerPostSearch("publish_time")}
                  >
                    <option value="0">All Time</option>
                    <option value="1">Yesterday</option>
                    <option value="7">This Week</option>
                    <option value="30">This Month</option>
                    <option value="90">Last 3 Months</option>
                    <option value="180">Last 6 Months</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="sort_type" className="block text-sm font-medium text-black mb-1">
                    Sort By
                  </label>
                  <select
                    id="sort_type"
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
                    {...registerPostSearch("sort_type")}
                  >
                    <option value="0">Relevance</option>
                    <option value="1">Most Liked</option>
                    <option value="3">Date</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                disabled={loadingPostSearch}
              >
                {loadingPostSearch ? "Searching..." : "Search Posts"}
              </button>
            </form>
          </div>
        )}

        {/* Post search results */}
        {activeTab === 'posts' && (
          <div className="mb-8">
            {postSearchResults.length > 0 ? (
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-xl font-semibold mb-4 text-black">Search Results: {postSearchResults.length} posts found</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {postSearchResults.map((post, index) => {
                    const postId = post.id || `post-${index}`;
                    const videoUrl = post.video?.download_addr && typeof post.video.download_addr === 'string' 
                      ? post.video.download_addr 
                      : (post.video?.download_addr as { url_list?: string[] })?.url_list?.[0] || '';
                    const coverUrl = post.video?.cover && typeof post.video.cover === 'string'
                      ? post.video.cover
                      : (post.video?.cover as { url_list?: string[] })?.url_list?.[0] || '';
                    
                    return (
                      <div key={postId} className="bg-white rounded-lg shadow-md overflow-hidden border">
                        <div className="relative aspect-video bg-gray-100">
                          {coverUrl && (
                            <Image
                              src={coverUrl}
                              alt={post.desc || "TikTok video"}
                              fill
                              className="object-cover"
                              unoptimized
                            />
                          )}
                        </div>
                        <div className="p-4">
                          {post.author && (
                            <div className="flex items-center mb-3">
                              <div className="h-8 w-8 rounded-full overflow-hidden bg-gray-200 mr-2">
                                {post.author.avatar_base64 ? (
                                  <Image
                                    src={`data:image/jpeg;base64,${post.author.avatar_base64}`}
                                    alt="Author"
                                    width={32}
                                    height={32}
                                    className="object-cover"
                                    unoptimized
                                  />
                                ) : post.author.avatar_thumb?.url_list?.[0] ? (
                                  <Image
                                    src={post.author.avatar_thumb.url_list[0]}
                                    alt="Author"
                                    width={32}
                                    height={32}
                                    className="object-cover"
                                    unoptimized
                                  />
                                ) : null}
                              </div>
                              <div>
                                <p className="text-sm font-medium text-black">{post.author.nickname || "Unknown"}</p>
                                {post.author.unique_id && (
                                  <p className="text-xs text-gray-600">@{post.author.unique_id}</p>
                                )}
                              </div>
                            </div>
                          )}
                          
                          <p className="text-sm text-gray-800 mb-3 line-clamp-2">{post.desc || "No description"}</p>
                          
                          <div className="flex justify-between items-center mb-3">
                            <div className="text-xs text-gray-700">
                              <span className="mr-2">♥ {post.statistics?.digg_count?.toLocaleString() || 0}</span>
                              <span className="mr-2">💬 {post.statistics?.comment_count?.toLocaleString() || 0}</span>
                              <span>▶ {post.statistics?.play_count?.toLocaleString() || 0}</span>
                            </div>
                            <div className="text-xs text-gray-500">
                              {post.create_time ? new Date(post.create_time * 1000).toLocaleDateString() : "Unknown date"}
                            </div>
                          </div>
                          
                          <div className="flex gap-2">
                            <button
                              onClick={() => videoUrl && downloadVideo(videoUrl, postId)}
                              disabled={!videoUrl || downloadingVideo[postId] || downloadDisabled}
                              className="text-xs px-3 py-1.5 rounded bg-green-600 text-white hover:bg-green-700 focus:outline-none disabled:opacity-50"
                            >
                              {downloadingVideo[postId] ? 'Downloading...' : 'Download'}
                            </button>
                            
                            {post.author?.unique_id && (
                              <a
                                href={`https://www.tiktok.com/@${post.author.unique_id}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs px-3 py-1.5 rounded border border-blue-600 text-blue-600 hover:bg-blue-50"
                              >
                                View Profile
                              </a>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              error && (
                <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-8">
                  <p className="text-red-700">{error}</p>
                </div>
              )
            )}
          </div>
        )}
      </div>
    </main>
  );
}

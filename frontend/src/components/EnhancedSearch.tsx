import React, { useState } from 'react';
import Image from 'next/image';
import { enhancedSearch, EnhancedSearchResponse, EnhancedUserResult } from '../app/api/tiktok';

export default function EnhancedSearch() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [searchResponse, setSearchResponse] = useState<EnhancedSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<EnhancedUserResult | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }
    
    setIsLoading(true);
    setSearchResponse(null);
    setSelectedUser(null);
    setError(null);
    
    try {
      const results = await enhancedSearch(query);
      setSearchResponse(results);
    } catch (err) {
      console.error('Error:', err);
      setError('Failed to connect to the server');
    } finally {
      setIsLoading(false);
    }
  };
  
  const selectUser = (user: EnhancedUserResult) => {
    setSelectedUser(selectedUser?.username === user.username ? null : user);
  };
  
  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Enhanced TikTok Search</h2>
        <p className="text-gray-600">
          Find relevant TikTok creators with AI-powered content analysis
        </p>
      </div>
      
      <div className="p-4 border border-gray-200 rounded-lg bg-white">
        <div className="space-y-4">
          <p className="text-md">Try searching for:</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
            <div 
              className="p-3 border border-gray-200 rounded-md cursor-pointer hover:bg-gray-50"
              onClick={() => setQuery("a cricketer who promotes cricket products on tiktok")}
            >
              <p>A cricketer who promotes cricket products on TikTok</p>
            </div>
            <div 
              className="p-3 border border-gray-200 rounded-md cursor-pointer hover:bg-gray-50"
              onClick={() => setQuery("fitness trainer who shows workout routines")}
            >
              <p>Fitness trainer who shows workout routines</p>
            </div>
            <div 
              className="p-3 border border-gray-200 rounded-md cursor-pointer hover:bg-gray-50"
              onClick={() => setQuery("tech reviewer who talks about smartphones")}
            >
              <p>Tech reviewer who talks about smartphones</p>
            </div>
            <div 
              className="p-3 border border-gray-200 rounded-md cursor-pointer hover:bg-gray-50"
              onClick={() => setQuery("chef who makes easy recipes under 30 minutes")}
            >
              <p>Chef who makes easy recipes under 30 minutes</p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="relative">
        <input
          className="w-full p-3 pr-16 border border-gray-300 rounded-md"
          placeholder="Describe the type of TikTok creator you're looking for..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button 
          className="absolute right-2 top-1/2 transform -translate-y-1/2 px-3 py-1 bg-blue-600 text-white rounded-md"
          onClick={handleSearch}
          disabled={isLoading}
        >
          {isLoading ? (
            <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="h-4 w-4" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          )}
        </button>
      </div>
      
      {error && (
        <div className="p-4 bg-red-100 text-red-800 rounded-md">
          {error}
        </div>
      )}
      
      {isLoading && (
        <div className="flex justify-center py-10">
          <div className="text-center">
            <div className="h-10 w-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="mt-4 text-lg">Using AI to find relevant TikTok creators...</p>
          </div>
        </div>
      )}
      
      {searchResponse && (
        <div className="space-y-6">
          <div className="p-6 border border-gray-200 rounded-lg bg-white">
            <h3 className="text-xl font-semibold mb-3">Search Results</h3>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div>
                <span className="text-sm text-gray-500">Original Query:</span>
                <p className="font-medium">{searchResponse.original_query}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Enhanced Query:</span>
                <p className="font-medium">{searchResponse.enhanced_query}</p>
              </div>
            </div>
            <div className="mt-4">
              <span className="text-sm text-gray-500">What we&apos;re looking for:</span>
              <p className="font-medium">{searchResponse.search_explanation}</p>
            </div>
          </div>
          
          {searchResponse.users.length === 0 ? (
            <div className="p-6 border border-gray-200 rounded-lg bg-white text-center">
              <p className="text-lg">No relevant TikTok creators found.</p>
              <p className="text-sm text-gray-500 mt-2">Try a different search query or criteria.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {searchResponse.users.map((user) => (
                <div 
                  key={user.username}
                  className={`p-4 border rounded-lg hover:shadow-md cursor-pointer transition-all duration-200 ${
                    selectedUser?.username === user.username 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 bg-white'
                  }`}
                  onClick={() => selectUser(user)}
                >
                  <div className="flex items-start space-x-3">
                    {user.profile_pic && (
                      <Image 
                        src={user.profile_pic} 
                        alt={user.username} 
                        className="rounded-full object-cover"
                        width={64}
                        height={64}
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.src = "/placeholder-avatar.png";
                        }}
                        unoptimized
                      />
                    )}
                    <div className="flex-1">
                      <h4 className="text-lg font-semibold">@{user.username}</h4>
                      <p className="text-gray-700">{user.display_name}</p>
                      {user.overall_relevance_score !== undefined && (
                        <div className="flex items-center mt-1">
                          <div className="relative w-full h-2 bg-gray-200 rounded-full">
                            <div 
                              className={`absolute top-0 left-0 h-2 rounded-full ${
                                user.overall_relevance_score > 0.7 
                                  ? 'bg-green-500' 
                                  : user.overall_relevance_score > 0.4 
                                    ? 'bg-yellow-500' 
                                    : 'bg-red-500'
                              }`}
                              style={{ width: `${user.overall_relevance_score * 100}%` }}
                            ></div>
                          </div>
                          <span className="ml-2 text-sm font-medium">
                            {Math.round(user.overall_relevance_score * 100)}%
                          </span>
                        </div>
                      )}
                      <div className="mt-2 flex items-center space-x-3 text-xs text-gray-500">
                        <span>{user.follower_count.toLocaleString()} followers</span>
                        <span>{user.likes_count.toLocaleString()} likes</span>
                      </div>
                    </div>
                  </div>
                  
                  {user.bio && (
                    <div className="mt-3">
                      <p className="text-sm">{user.bio}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      {selectedUser && (
        <div className="p-6 border border-gray-200 rounded-lg bg-white">
          <h3 className="text-xl font-semibold mb-4">@{selectedUser.username} Analysis</h3>
          
          <div className="space-y-6">
            {selectedUser.bio_analysis && (
              <div className="p-4 rounded-md bg-gray-50">
                <h4 className="font-medium mb-2">Bio Analysis</h4>
                <p className="text-sm">{selectedUser.bio_analysis}</p>
              </div>
            )}
            
            {selectedUser.profile_analysis && (
              <div className="p-4 rounded-md bg-gray-50">
                <h4 className="font-medium mb-2">Profile Image Analysis</h4>
                <p className="text-sm">{selectedUser.profile_analysis}</p>
              </div>
            )}
            
            {selectedUser.videos && selectedUser.videos.length > 0 && (
              <div>
                <h4 className="font-medium mb-3">Recent Videos Analysis</h4>
                <div className="grid grid-cols-1 gap-4">
                  {selectedUser.videos.map((video) => (
                    <div key={video.id} className="p-4 border border-gray-100 rounded-md">
                      <div className="flex flex-col md:flex-row gap-4">
                        {video.thumbnail_url && (
                          <div className="flex-shrink-0">
                            <Image 
                              src={video.thumbnail_url} 
                              alt="Thumbnail" 
                              className="rounded-md object-cover"
                              width={192}
                              height={108}
                              onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.src = "/placeholder-thumbnail.png";
                              }}
                              unoptimized
                            />
                          </div>
                        )}
                        <div className="flex-1">
                          <p className="font-medium text-sm mb-2">{video.caption}</p>
                          
                          {video.relevance_score !== undefined && (
                            <div className="flex items-center mt-1 mb-2">
                              <div className="relative w-full h-2 bg-gray-200 rounded-full">
                                <div 
                                  className={`absolute top-0 left-0 h-2 rounded-full ${
                                    video.relevance_score > 0.7 
                                      ? 'bg-green-500' 
                                      : video.relevance_score > 0.4 
                                        ? 'bg-yellow-500' 
                                        : 'bg-red-500'
                                  }`}
                                  style={{ width: `${video.relevance_score * 100}%` }}
                                ></div>
                              </div>
                              <span className="ml-2 text-sm font-medium">
                                {Math.round(video.relevance_score * 100)}%
                              </span>
                            </div>
                          )}
                          
                          {video.thumbnail_analysis && (
                            <div className="mt-2">
                              <span className="text-xs text-gray-500">Thumbnail Analysis:</span>
                              <p className="text-xs">{video.thumbnail_analysis}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {selectedUser.overall_analysis && (
              <div className="p-4 rounded-md bg-blue-50 border border-blue-100">
                <h4 className="font-medium mb-2">Overall Analysis</h4>
                <p>{selectedUser.overall_analysis}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

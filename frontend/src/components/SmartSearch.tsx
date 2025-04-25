import React, { useState } from 'react';
import Link from 'next/link';
import { smartSearch, getUserByUsername, TikTokUser } from '../../app/api/tiktok';

interface SmartSearchResult {
  username: string;
  confidence: number;
  explanation: string;
}

export default function SmartSearch() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [searchResult, setSearchResult] = useState<SmartSearchResult | null>(null);
  const [specificUser, setSpecificUser] = useState<TikTokUser | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }
    
    setIsLoading(true);
    setSearchResult(null);
    setSpecificUser(null);
    setError(null);
    
    try {
      // First, use smart search to find the specific username
      const smartResult = await smartSearch(query);
      setSearchResult(smartResult);
      
      // If we found a specific username, fetch the user details
      if (smartResult.username !== "No specific user found" && smartResult.confidence > 0.5) {
        try {
          const userDetails = await getUserByUsername(smartResult.username);
          setSpecificUser(userDetails);
        } catch (userError) {
          console.error('Error fetching user details:', userError);
          // We still show the smart search result even if user details failed
        }
      }
    } catch (err) {
      console.error('Error:', err);
      setError('Failed to connect to the server');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Smart TikTok User Search</h2>
        <p className="text-gray-600">
          Describe the TikTok user you&apos;re looking for in natural language
        </p>
      </div>
      
      <div className="p-4 border border-gray-200 rounded-lg bg-white">
        <div className="space-y-4">
          <p className="text-md">Examples:</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
            <div 
              className="p-3 border border-gray-200 rounded-md cursor-pointer hover:bg-gray-50"
              onClick={() => setQuery("Find Khaby Lame, the famous TikToker known for his silent comedy")}
            >
              <p>Find Khaby Lame, the famous TikToker known for his silent comedy</p>
            </div>
            <div 
              className="p-3 border border-gray-200 rounded-md cursor-pointer hover:bg-gray-50"
              onClick={() => setQuery("I&apos;m looking for that TikTok doctor who explains medical concepts")}
            >
              <p>I&apos;m looking for that TikTok doctor who explains medical concepts</p>
            </div>
            <div 
              className="p-3 border border-gray-200 rounded-md cursor-pointer hover:bg-gray-50"
              onClick={() => setQuery("Who&apos;s that famous makeup artist on TikTok with over 10 million followers?")}
            >
              <p>Who&apos;s that famous makeup artist on TikTok with over 10 million followers?</p>
            </div>
            <div 
              className="p-3 border border-gray-200 rounded-md cursor-pointer hover:bg-gray-50"
              onClick={() => setQuery("Find the official NBA TikTok account")}
            >
              <p>Find the official NBA TikTok account</p>
            </div>
          </div>
        </div>
      </div>
      
      <div className="relative">
        <input
          className="w-full p-3 pr-16 border border-gray-300 rounded-md"
          placeholder="Describe the TikTok user you're looking for..."
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
            <p className="mt-4 text-lg">Using AI to find the perfect match...</p>
          </div>
        </div>
      )}
      
      {searchResult && (
        <div className="p-6 border border-gray-200 rounded-lg bg-white">
          <div className="space-y-4">
            <h3 className="text-xl font-medium">
              {searchResult.username === "No specific user found" 
                ? "No specific user found" 
                : "Found a potential match!"}
            </h3>
            
            {searchResult.username !== "No specific user found" && (
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold">@{searchResult.username}</h2>
                  <span className={`inline-block px-2 py-1 text-xs font-semibold rounded-full ${
                    searchResult.confidence > 0.7 
                      ? 'bg-green-100 text-green-800' 
                      : searchResult.confidence > 0.4 
                        ? 'bg-yellow-100 text-yellow-800' 
                        : 'bg-red-100 text-red-800'
                  }`}>
                    {(searchResult.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
                <Link href={`/profile/${searchResult.username}`} className="px-4 py-2 bg-blue-600 text-white rounded-md">
                  View Profile
                </Link>
              </div>
            )}
            
            <div className="p-4 bg-gray-100 rounded-md">
              <h4 className="font-medium mb-2">AI Explanation</h4>
              <p>{searchResult.explanation}</p>
            </div>
            
            {specificUser && (
              <div className="mt-4 p-4 border border-gray-200 rounded-md">
                <h4 className="font-medium mb-2">User Details</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Display Name</p>
                    <p className="font-medium">{specificUser.display_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Followers</p>
                    <p className="font-medium">{specificUser.follower_count.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Following</p>
                    <p className="font-medium">{specificUser.following_count.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Likes</p>
                    <p className="font-medium">{specificUser.likes_count.toLocaleString()}</p>
                  </div>
                </div>
                {specificUser.bio && (
                  <div className="mt-4">
                    <p className="text-sm text-gray-500">Bio</p>
                    <p className="font-medium">{specificUser.bio}</p>
                  </div>
                )}
              </div>
            )}
            
            {searchResult.username === "No specific user found" && (
              <div className="mt-4">
                <p className="mb-4">Try refining your search or use the standard search for more options.</p>
                <button
                  onClick={() => setQuery('')}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md"
                >
                  Clear Search
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
} 
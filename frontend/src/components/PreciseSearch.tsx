import React, { useState } from 'react';
import Image from 'next/image';
import { PreciseSearchResponse, preciseSearch, WebEnhancedSearchResponse, webEnhancedSearch } from '../app/api/tiktok';

const MOCK_RESULTS: PreciseSearchResponse = {
  query: "a tech influencer from south africa",
  required_criteria: [
    "Must be explicitly based in South Africa", 
    "Must create tech-focused content regularly", 
    "Must have influencer status or following in tech niche",
    "Should mention technology products or reviews", 
    "Should have South African nationality or location in bio"
  ],
  matches: [
    {
      username: "techgurusa",
      display_name: "SA Tech Guy",
      bio: "South African tech reviewer | Based in Cape Town | Latest gadgets & tech news | Working with Samsung and Apple",
      follower_count: 75000,
      profile_pic: "https://randomuser.me/api/portraits/men/32.jpg",
      why_matches: "This account clearly mentions being from South Africa, creates tech-focused content regularly as a tech reviewer, has a significant following as a tech influencer, mentions working with tech brands, and explicitly states South African location in bio.",
      relevance_score: 0.95,
      videos: [
        {caption: "Unboxing the latest Galaxy S23 Ultra! 📱 #SouthAfrica #TechReview", thumbnail: "https://picsum.photos/200/300?random=1"},
        {caption: "Cape Town Tech Meetup highlights - amazing tech community in SA! #TechScene", thumbnail: "https://picsum.photos/200/300?random=2"},
        {caption: "Top 5 budget phones available in South Africa right now! 🇿🇦 #TechTips", thumbnail: "https://picsum.photos/200/300?random=3"}
      ]
    },
    {
      username: "satech_reviews",
      display_name: "Tech Reviews South Africa",
      bio: "🇿🇦 South African Tech Content | Reviews & Unboxings | Pretoria Based | Contact for collabs: satechreviews@mail.com",
      follower_count: 42300,
      profile_pic: "https://randomuser.me/api/portraits/women/44.jpg",
      why_matches: "This account is explicitly based in South Africa (Pretoria), focuses exclusively on tech content and reviews, has a significant following as a tech influencer, and uses the South African flag in bio.",
      relevance_score: 0.87,
      videos: [
        {caption: "Is this the BEST laptop for South Africans? Full review! 💻", thumbnail: "https://picsum.photos/200/300?random=4"},
        {caption: "Tech prices in SA vs global markets - why we pay more 💰 #SATech", thumbnail: "https://picsum.photos/200/300?random=5"},
        {caption: "My studio setup tour - all the gear I use for my tech reviews! 🎥", thumbnail: "https://picsum.photos/200/300?random=6"}
      ]
    }
  ],
  search_strategy: "Original query, Keyword: South African tech reviewer"
};

const PreciseSearch = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<PreciseSearchResponse | WebEnhancedSearchResponse | null>(null);
  const [error, setError] = useState('');
  const [useMockData, setUseMockData] = useState(false);
  const [useWebEnhanced, setUseWebEnhanced] = useState(true); // Default to use web-enhanced search

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');

    // If mock mode is enabled, return mock data instead of making API call
    if (useMockData) {
      // Simulate network delay
      setTimeout(() => {
        setResults({
          ...MOCK_RESULTS,
          query: query // Update the query to match user input
        });
        setLoading(false);
      }, 1500);
      return;
    }
    
    try {
      // ALWAYS use web-enhanced search for better results (Tavily-powered)
      // We force useWebEnhanced to true to ensure we're using Tavily
      console.log('Using Tavily-powered web-enhanced search...');
      const searchResults = await webEnhancedSearch(query, 5);
      
      setResults(searchResults);
      console.log('Search results:', searchResults); // Debug logging
    } catch (err) {
      setError('Failed to perform search. Please try again.');
      console.error('Search error:', err);
      
      // If web-enhanced search fails, fall back to regular precise search
      try {
        console.log('Web-enhanced search failed, falling back to regular search...');
        const fallbackResults = await preciseSearch(query, 5);
        setResults(fallbackResults);
        console.log('Fallback results:', fallbackResults);
      } catch (fallbackErr) {
        console.error('Fallback search error:', fallbackErr);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Precise TikTok Search</h1>
      <p className="mb-4 text-sm">
        This search uses ultra-strict verification to find only highly relevant accounts that match ALL criteria.
        It avoids generic keyword matches and only returns accounts that specifically meet each requirement.
      </p>
      
      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex items-center mb-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="E.g., 'a tech influencer from South Africa' or 'a cricketer who promotes cricket products'"
            className="flex-grow p-2 border rounded-l focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-500 text-white p-2 rounded-r hover:bg-blue-600 disabled:bg-blue-300"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
        
        <div className="flex items-center text-sm space-x-6">
          <label className="flex items-center text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={useMockData}
              onChange={() => setUseMockData(!useMockData)}
              className="mr-2 h-4 w-4"
            />
            Use mock data (for testing when API is rate limited)
          </label>
          
          <label className="flex items-center text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={useWebEnhanced}
              onChange={() => setUseWebEnhanced(!useWebEnhanced)}
              className="mr-2 h-4 w-4"
            />
            Use web-enhanced search (better for location-specific queries)
          </label>
        </div>
      </form>

      {error && <div className="bg-red-100 text-red-700 p-3 rounded mb-4">{error}</div>}

      {results && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-2">Search Results</h2>
          
          <div className="mb-4 p-4 bg-gray-100 rounded">
            <h3 className="font-semibold">Query Requirements</h3>
            <p className="mb-2">&ldquo;{results.query}&rdquo;</p>
            <h4 className="font-medium mt-2 mb-1">Required Criteria:</h4>
            <ul className="list-disc pl-5">
              {results.required_criteria.map((criterion, i) => (
                <li key={i} className="text-sm">{criterion}</li>
              ))}
            </ul>
            <p className="text-sm mt-2 italic">Search Strategy: {results.search_strategy}</p>
          </div>

          {(!results.matches || results.matches.length === 0) ? (
            <div className="p-4 bg-yellow-100 text-yellow-800 rounded">
              No accounts found that match ALL required criteria. Try broadening your search or using less specific criteria.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results.matches.map((user, index) => (
                <div key={index} className="border rounded p-4 flex flex-col">
                  <div className="flex items-start mb-4">
                    {user.profile_pic ? (
                      <div className="relative w-16 h-16 rounded-full overflow-hidden mr-4">
                        <Image 
                          src={user.profile_pic} 
                          alt={`${user.username}'s profile`} 
                          fill
                          className="object-cover"
                          unoptimized
                        />
                      </div>
                    ) : (
                      <div className="w-16 h-16 bg-gray-200 rounded-full mr-4 flex items-center justify-center">
                        <span className="text-gray-500">No pic</span>
                      </div>
                    )}
                    <div>
                      <h3 className="font-bold text-lg">@{user.username}</h3>
                      <p className="text-sm">{user.display_name}</p>
                      <p className="text-xs text-gray-600">{user.follower_count.toLocaleString()} followers</p>
                    </div>
                    <div className="ml-auto">
                      <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold">
                        {(user.relevance_score * 100).toFixed(0)}% match
                      </span>
                    </div>
                  </div>
                  
                  <div className="text-sm mb-3">
                    <p className="font-semibold mb-1">Bio:</p>
                    <p className="bg-gray-50 p-2 rounded">{user.bio || "(No bio)"}</p>
                  </div>
                  
                  <div className="text-sm mb-3 flex-grow">
                    <p className="font-semibold mb-1">Why this account matches:</p>
                    <p className="bg-green-50 p-2 rounded text-xs">{user.why_matches}</p>
                  </div>
                  
                  {user.videos && user.videos.length > 0 && (
                    <div className="mt-3">
                      <p className="font-semibold text-sm mb-1">Recent Videos:</p>
                      <div className="grid grid-cols-3 gap-2">
                        {user.videos.map((video, i) => (
                          <div key={i} className="text-xs">
                            {video.thumbnail && (
                              <div className="relative w-full h-20 rounded overflow-hidden">
                                <Image 
                                  src={video.thumbnail} 
                                  alt={`Video thumbnail ${i+1}`}
                                  fill
                                  className="object-cover"
                                  unoptimized
                                />
                              </div>
                            )}
                            <p className="truncate mt-1">{video.caption || "(No caption)"}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <a 
                    href={`https://tiktok.com/@${user.username}`} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="mt-3 text-center text-sm bg-gray-800 text-white py-1 px-3 rounded hover:bg-gray-700"
                  >
                    View on TikTok
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PreciseSearch;

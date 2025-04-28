"""
TikTok Analyzer Backend
-----------------------
A Flask API for searching and analyzing TikTok content using Tavily API, 
ScrapTik API, and OpenAI GPT for enhanced relevance scoring.
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
import requests
import re
import random
import json
import time
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
import os
import openai
import asyncio

# Import custom helpers
from security_privacy_helpers import is_security_privacy_focused, security_privacy_relevance_score

# Import the official Tavily Python client
try:
    from tavily import TavilyClient
    TAVILY_CLIENT_AVAILABLE = True
except ImportError:
    TAVILY_CLIENT_AVAILABLE = False
    print("⚠️ Tavily Python client not available. Consider installing with: pip install tavily-python")

# Initialize FastAPI
app = FastAPI(title="TikTok Analyzer API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv()
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# ScrapTik API setup
BASE_URL = "https://scraptik.p.rapidapi.com"
headers = {
    "X-RapidAPI-Key": RAPID_API_KEY,
    "X-RapidAPI-Host": "scraptik.p.rapidapi.com"
}

# Alternative API endpoints from ScrapTik docs
ENDPOINTS = {
    "user_info": f"{BASE_URL}/user-info",  # Primary endpoint for user data
    "web_user": f"{BASE_URL}/web/get-user",  # Web endpoint for user data
    "search_users": f"{BASE_URL}/search-users",  # Search users endpoint
    "username_to_id": f"{BASE_URL}/username-to-id",  # Convert username to ID
    "user_posts": f"{BASE_URL}/user-posts"  # Get user videos
}

# Alternative API provider
BASE_URL_ALTERNATIVE = "https://tiktok-video-no-watermark2.p.rapidapi.com"
headers_alternative = {
    "X-RapidAPI-Key": RAPID_API_KEY,
    "X-RapidAPI-Host": "tiktok-video-no-watermark2.p.rapidapi.com"
}

# Configure OpenAI client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

#-----------------------------------------------------------------------------
# Pydantic Models
#-----------------------------------------------------------------------------

class WebEnhancedSearchRequest(BaseModel):
    """Request model for web-enhanced TikTok search"""
    query: str
    max_results: int = 5
    min_relevance_score: float = 0.5

class TikTokUsername(BaseModel):
    """Model for TikTok username extracted from web search"""
    username: str
    source: str
    context: Optional[str] = None
    search_relevance: Optional[float] = None

class WebEnhancedUserMatch(BaseModel):
    """Model for matched TikTok user with relevance scoring"""
    username: str
    display_name: str
    bio: str
    follower_count: int
    profile_pic: str
    why_matches: str
    relevance_score: float
    discovery_method: str
    videos: Optional[List[Dict]] = []

class WebEnhancedSearchResponse(BaseModel):
    """Response model for web-enhanced search"""
    query: str
    required_criteria: List[str] = []
    matches: List[WebEnhancedUserMatch] = []
    search_strategy: str = ""
    usernames_found: int = 0
    profiles_analyzed: int = 0

#-----------------------------------------------------------------------------
# Tavily Search Integration
#-----------------------------------------------------------------------------

def perform_tavily_search(query: str, max_results: int = 10) -> Optional[Dict]:
    """
    Perform a search for TikTok profiles using Tavily API
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        Dict containing Tavily search results or None if search failed
    """
    try:
        print(f"==== PERFORMING TAVILY SEARCH ====\nQuery: {query}")
        
        if not TAVILY_API_KEY:
            print("ERROR: Tavily API key not configured")
            return None
            
        # Construct domain-specific search queries based on the query type
        if "security" in query.lower() or "privacy" in query.lower():
            # Security/privacy focused query
            sub_topics = []
            if "security" in query.lower():
                sub_topics.append("cybersecurity")
            if "privacy" in query.lower():
                sub_topics.append("data privacy")
                
            if sub_topics:
                specific_topics = " and ".join(sub_topics)
                enhanced_query = f"best TikTok {specific_topics} experts OR popular {specific_topics} influencers on TikTok"
            else:
                enhanced_query = f"top TikTok influencers specializing in {query}"
                
        elif "from" in query.lower() or "in" in query.lower():
            # Location-specific query
            location_parts = re.split(r'\sfrom\s|\sin\s', query.lower())
            if len(location_parts) > 1:
                topic = location_parts[0].strip()
                location = location_parts[1].strip()
                enhanced_query = f"top {topic} TikTok influencers from {location} 2025 OR most popular {location} TikTokers who create {topic} content"
            else:
                enhanced_query = f"best TikTok creators focused on {query}"
        else:
            # General topic query
            topic_terms = query.lower().replace("influencer", "").replace("creator", "").strip()
            enhanced_query = f"most popular TikTok accounts focused on {topic_terms} OR top {topic_terms} experts on TikTok 2025"
        
        print(f"Enhanced search query: {enhanced_query}")
        
        # 1. Use the official Tavily Python client if available
        if TAVILY_CLIENT_AVAILABLE:
            try:
                client = TavilyClient(api_key=TAVILY_API_KEY)
                
                # Use the official client to search
                data = client.search(
                    query=enhanced_query,
                    search_depth="advanced",
                    include_domains=[
                        "tiktok.com", "tokfluence.com", "heepsy.com", "influencermarketinghub.com", 
                        "hiveinfluence.io", "starngage.com", "favikon.com", "socialtracker.io", 
                        "socialblade.com", "omniinfluencer.com", "tokboard.com", "affable.ai"
                    ],
                    include_answer=True,
                    include_images=True,
                    max_results=max_results
                )
                
                result_count = len(data.get('results', []))
                print(f"✅ Tavily API client success - found {result_count} results")
                
                # Log first result for debugging
                if result_count > 0:
                    first_result = data['results'][0]
                    print(f"First result: {first_result.get('title')} - {first_result.get('url')}")
                
                return data
                
            except Exception as client_error:
                print(f"⚠️ Tavily client error: {str(client_error)}. Falling back to direct API call.")
                # Fall through to direct API call
        
        # 2. Fallback: Use direct API call
        search_url = "https://api.tavily.com/search"
        headers = {
            "Authorization": f"Bearer {TAVILY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": enhanced_query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_domains": [
                "tiktok.com", "tokfluence.com", "heepsy.com", "influencermarketinghub.com", 
                "hiveinfluence.io", "starngage.com", "favikon.com", "socialtracker.io", 
                "socialblade.com", "omniinfluencer.com", "tokboard.com", "affable.ai"
            ],
            "include_answer": True,
            "include_images": True
        }
        
        print(f"Tavily API request: {search_url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Execute search with timeout
        response = requests.post(search_url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            result_count = len(data.get('results', []))
            print(f"✅ Tavily API success - found {result_count} results")
            
            # Log first result for debugging
            if result_count > 0:
                first_result = data['results'][0]
                print(f"First result: {first_result.get('title')} - {first_result.get('url')}")
            
            return data
        else:
            print(f"❌ Tavily API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error performing Tavily search: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

#-----------------------------------------------------------------------------
# Username Extraction
#-----------------------------------------------------------------------------

def extract_tiktok_usernames(url: str, title: str, content: str) -> List[str]:
    """
    Extract TikTok usernames from search result data
    
    Args:
        url: The URL from search results
        title: The title from search results
        content: The content/snippet from search results
        
    Returns:
        List of extracted TikTok usernames
    """
    # Initialize list to store valid usernames
    usernames = []
    
    # Combine text for searching
    combined_text = f"{url} {title} {content}"
    
    # Extract from URL directly - most reliable source
    if "tiktok.com/@" in url:
        username = url.split("tiktok.com/@")[1].split("/")[0].split("?")[0]
        if username and username not in usernames and is_valid_tiktok_username(username):
            usernames.append(username)
    
    # General patterns to match TikTok usernames across various formats
    patterns = [
        # Standard username patterns
        r'@([\w\.]{2,24})\b',                       # @username notation with word boundary
        r'tiktok\.com/@([\w\.]{2,24})\b',          # TikTok URL format
        
        # Profile listing patterns (common in ranking sites)
        r'(?:^|\s)(\w+)\s+·\s+@([\w\.]{2,24})\b',      # "Name · @username" format
        r'(?:\.|\n|\s)(\w+)\s*@([\w\.]{2,24})\b',        # "Name@username" or "Name @username"
        r'(\w+)\s*\(\s*@([\w\.]{2,24})\s*\)',         # "Name (@username)" format
        
        # List formats (common in influencer listings)
        r'\d+\.\s*([\w\s]+)\s*[·•]\s*@([\w\.]{2,24})', # "1. Name · @username"
        r'\d+\.\s*@([\w\.]{2,24})\b',                  # "1. @username"
        
        # Additional contextual patterns from influencer directories
        r'(?:username|handle|account)\s*[:=]\s*@?([\w\.]{2,24})\b',  # "username: username"
        r'\b(\w+)\s+(?:has|with)\s+\d+(?:K|M)?\s+(?:followers|fans)\b.*?@([\w\.]{2,24})\b', # "Name has 1M followers @username"
        
        # Additional patterns for Tavily's structured results
        r'"(?:username|handle)"\s*:\s*"@?([\w\.]{2,24})"', # JSON-like "username": "username"
        r'\[([\w\.]{2,24})\]\(https://[\w\.]*tiktok\.com'  # Markdown link format [username](https://tiktok.com...)
    ]
    
    # Process all patterns
    for pattern in patterns:
        matches = re.findall(pattern, combined_text)
        for match in matches:
            if isinstance(match, tuple):
                # For patterns with capture groups, try the second group first (usually the username)
                # as the first group might be the display name
                username = match[1] if len(match) > 1 and match[1] else match[0]
            else:
                username = match
                
            # Clean up the username
            username = username.strip('@').strip()
            
            # Validate TikTok username
            if is_valid_tiktok_username(username) and username not in usernames:
                usernames.append(username)
    
    # Return only usernames that pass the validation filter
    filtered_usernames = filter_valid_usernames(usernames)
    return filtered_usernames

def is_valid_tiktok_username(username: str) -> bool:
    """
    Validate if a username follows TikTok's username constraints
    and is not a common word or text fragment
    """
    # Length check (TikTok allows 2-24 characters)
    if not username or len(username) < 2 or len(username) > 24:
        return False
        
    # Character check (letters, numbers, underscores, periods only)
    if not re.match(r'^[\w\.]+$', username):
        return False
        
    # Must start with a letter or number
    if not re.match(r'^[a-zA-Z0-9]', username):
        return False
    
    # Filter out common words and fragments that are often false positives
    common_words = [
        'tiktok', 'for', 'top', 'best', 'from', 'with', 'has', 'influencer', 
        'creator', 'africa', 'south', 'asia', 'europe', 'america', 'north', 'usa',
        'marketing', 'business', 'tech', 'fashion', 'beauty', 'fitness', 'food',
        'travel', 'srsltid', 'html', 'www', 'http', 'https', 'com', 'net', 'org',
        'influencers', 'marketers', 'followers', 'popular', 'discover', 'account',
        'accounts', 'users', 'user', 'handle', 'profile', 'website', 'site', 'page',
        'pages', 'search', 'find', 'results', 'trending', 'viral', 'famous',
        'category', 'categories', 'report', 'analysis', 'data', 'stats', 'statistics',
        'social', 'media', 'platform', 'app', 'rketing'
    ]
    
    if username.lower() in common_words:
        return False
    
    # Valid username
    return True

def filter_valid_usernames(usernames: List[str]) -> List[str]:
    """
    Filter a list of possible usernames to only include probably valid ones
    """
    if not usernames:
        return []
        
    # First pass: filter out invalid usernames
    filtered = [u for u in usernames if is_valid_tiktok_username(u)]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_filtered = [u for u in filtered if not (u.lower() in seen or seen.add(u.lower()))]
    
    return unique_filtered

async def search_directly_on_tiktok(query: str, max_results: int = 5) -> List[TikTokUsername]:
    """
    Search for TikTok profiles directly on TikTok using ScrapTik API's search-users endpoint
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        
    Returns:
        List of TikTok usernames with relevance scores
    """
    try:
        print(f"\n🎙️ DIRECT TIKTOK SEARCH: {query}")
        usernames = []
        
        # Use search-users endpoint from ScrapTik
        url = ENDPOINTS["search_users"]
        params = {
            "keyword": query.strip(),
            "count": str(max_results * 2),  # Request more to filter
            "cursor": "0"
        }
        
        print(f"Request: GET {url} with params {params}")
        response = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data and "user_list" in data and data["user_list"]:
                users = data["user_list"]
                print(f"✅ SUCCESS: Found {len(users)} users via direct TikTok search")
                
                for i, user in enumerate(users):
                    if "user_info" in user:
                        user_info = user["user_info"]
                        username = user_info.get("unique_id", "")
                        if username:
                            # Calculate a relevance score based on follower count and verification
                            follower_count = user_info.get("follower_count", 0)
                            is_verified = user_info.get("custom_verify", "") != ""
                            relevance = min(1.0, 0.5 + (0.3 if is_verified else 0) + min(0.2, follower_count / 1000000))
                            
                            # Create context text from user bio and stats
                            bio = user_info.get("signature", "")
                            followers = user_info.get("follower_count", 0)
                            following = user_info.get("following_count", 0)
                            likes = user_info.get("total_favorited", 0)
                            context = f"Bio: {bio}\nFollowers: {followers}, Following: {following}, Likes: {likes}"
                            
                            usernames.append(TikTokUsername(
                                username=username,
                                source="TikTok Direct Search",
                                context=context,
                                search_relevance=relevance
                            ))
                            
                            print(f"  {i+1}. @{username} (Relevance: {relevance:.2f})")
                
                return usernames[:max_results]
            else:
                print(f"⚠️ No users found in direct search response")
        else:
            print(f"❌ DIRECT SEARCH FAILED: HTTP {response.status_code}")
        
        return []
        
    except Exception as e:
        print(f"❌ ERROR in direct TikTok search: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []

async def search_for_tiktok_profiles(query: str, max_results: int = 10) -> List[TikTokUsername]:
    """
    Find TikTok profiles related to the query using multiple search strategies:
    1. Direct TikTok search using ScrapTik API
    2. Web search using Tavily API
    
    Args:
        query: Search query
        max_results: Maximum number of profiles to return
        
    Returns:
        List of TikTok usernames with context
    """
    try:
        print(f"\n==== SEARCHING FOR TIKTOK PROFILES ====\nQuery: {query}")
        
        all_usernames = []
        username_set = set()  # Avoid duplicates
        
        # STRATEGY 1: Try direct TikTok search
        direct_results = await search_directly_on_tiktok(query, max_results=max_results)
        if direct_results:
            print(f"✅ Found {len(direct_results)} usernames through direct TikTok search")
            for username_obj in direct_results:
                if username_obj.username not in username_set:
                    username_set.add(username_obj.username)
                    all_usernames.append(username_obj)
        
        # STRATEGY 2: Execute Tavily web search if we need more results
        if len(all_usernames) < max_results:
            more_needed = max_results - len(all_usernames)
            print(f"🔍 STRATEGY 2: Tavily web search for {more_needed} more profiles")
            tavily_results = perform_tavily_search(query, max_results=15)
            
            if not tavily_results or 'results' not in tavily_results or not tavily_results['results']:
                print(f"❌ No Tavily results found for query: {query}")
            else:
                result_count = len(tavily_results['results'])
                print(f"✅ Got {result_count} results from Tavily")
                
                # Process search results
                for item in tavily_results['results']:
                    title = item.get('title', '')
                    url = item.get('url', '')
                    content = item.get('content', '')
                    snippet = item.get('snippet', '')
                    
                    # Combine all content for better extraction
                    full_content = f"{title}\n{snippet}\n{content}"
                    
                    # Extract usernames
                    usernames = extract_tiktok_usernames(url, title, full_content)
                    
                    # Add each username to results
                    for username in usernames:
                        if username and username not in username_set:
                            username_set.add(username)
                            all_usernames.append(TikTokUsername(
                                username=username,
                                source=url,
                                context=snippet or content[:200]
                            ))
                    
                    # Check if we have enough
                    if len(all_usernames) >= max_results:
                        break
        
        # Score usernames for relevance if they don't already have scores
        usernames_to_score = [u for u in all_usernames if u.search_relevance is None]
        if usernames_to_score:
            print(f"Scoring relevance for {len(usernames_to_score)} usernames")
            scored_usernames = await score_usernames_relevance(usernames_to_score, query)
            
            # Update scores in original list
            for i, username in enumerate(all_usernames):
                if username.search_relevance is None:
                    username.search_relevance = scored_usernames[0].search_relevance
                    scored_usernames.pop(0)
        
        # Sort by relevance and return
        all_usernames.sort(key=lambda x: x.search_relevance or 0, reverse=True)
        final_results = all_usernames[:max_results]
        
        print(f"📊 FINAL RESULTS: {len(final_results)} TikTok profiles found")
        for i, username in enumerate(final_results):
            print(f"  {i+1}. @{username.username} (Source: {username.source}, Relevance: {username.search_relevance or 0:.2f})")
        
        return final_results
        
    except Exception as e:
        print(f"Error in search_for_tiktok_profiles: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []

#-----------------------------------------------------------------------------
# TikTok API Integration
#-----------------------------------------------------------------------------

async def get_user_by_username(username: str) -> Optional[Dict]:
    """
    Fetch TikTok user details by username using multiple endpoints in sequence
    
    Args:
        username: TikTok username
        
    Returns:
        User data from ScrapTik API or minimal placeholder data if not found
    """
    try:
        print(f"\n🔍 FETCHING USER DATA FOR: @{username}")
        print(f"API Key Status: {'✓ Set' if RAPID_API_KEY else '✗ Missing'}")
        
        # Try multiple approaches with a sequence of endpoints
        max_retries = 3  # Per endpoint
        backoff_time = 2
        
        # Track if we need to search for the user
        user_needs_search = True
        user_data = None
        
        # APPROACH 1: Try direct user-info endpoint with username
        if user_needs_search:
            print(f"🔎 APPROACH 1: Direct user-info lookup for @{username}")
            retry_count = 0
            
            while retry_count < max_retries and user_needs_search:
                try:
                    url = ENDPOINTS["user_info"]
                    params = {"unique_id": username}
                    print(f"Request: GET {url} with params {params}")
                    
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                    print(f"Response Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data and "user" in data:
                            print(f"✅ SUCCESS: Direct user-info found @{username}")
                            user_data = data["user"]
                            user_needs_search = False
                            print(f"Display Name: {user_data.get('nickname', 'Unknown')}")
                            print(f"Follower Count: {user_data.get('follower_count', 'Unknown')}")
                            return user_data
                    
                    # If rate limited, backoff and retry
                    if response.status_code == 429:
                        retry_count += 1
                        wait_time = backoff_time * (2 ** retry_count)  # Exponential backoff
                        print(f"⏱️ Rate limited. Retrying...")
                        await asyncio.sleep(wait_time)
                    else:
                        break
                        
                except requests.exceptions.ReadTimeout:
                    # Timeouts are common with this API - don't flood logs
                    retry_count += 1
                    if retry_count == max_retries:
                        print(f"⏱️ API timeouts for @{username}, moving to next approach")
                    await asyncio.sleep(backoff_time * retry_count)  # Simple backoff
                except Exception as e:
                    # Only log first error, not each retry
                    if retry_count == 0:
                        print(f"⚠️ Error in Approach 1: {type(e).__name__}")
                    retry_count += 1
                    if retry_count < max_retries:
                        await asyncio.sleep(backoff_time * retry_count)
                    else:
                        break
        
        # APPROACH 2: Try the web/get-user endpoint
        if user_needs_search:
            print(f"🔎 APPROACH 2: Web user lookup for @{username}")
            retry_count = 0
            timeout_occurred = False
            
            while retry_count < max_retries and user_needs_search:
                try:
                    url = ENDPOINTS["web_user"]
                    params = {"username": username}
                    
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data and "userInfo" in data:
                            print(f"✅ SUCCESS: Web user lookup found @{username}")
                            
                            # Convert web user format to standard format
                            user_info = data["userInfo"]
                            user_data = {
                                "nickname": user_info.get("user", {}).get("nickname", username),
                                "signature": user_info.get("user", {}).get("signature", "No bio available"),
                                "follower_count": user_info.get("stats", {}).get("followerCount", 0),
                                "avatar_larger": {"url_list": [user_info.get("user", {}).get("avatarLarger", "")]},
                                "uid": user_info.get("user", {}).get("id", "")
                            }
                            
                            user_needs_search = False
                            print(f"Display Name: {user_data.get('nickname', 'Unknown')}")
                            print(f"Follower Count: {user_data.get('follower_count', 'Unknown')}")
                            return user_data
                
                    # If rate limited, backoff and retry
                    if response.status_code == 429:
                        retry_count += 1
                        await asyncio.sleep(backoff_time * retry_count)
                    else:
                        # Try next approach
                        break
                        
                except requests.exceptions.ReadTimeout:
                    # Timeouts are common with this API - don't flood logs
                    timeout_occurred = True
                    retry_count += 1
                    if retry_count < max_retries:
                        await asyncio.sleep(backoff_time * retry_count)
                    else:
                        break
                except Exception as e:
                    # Only log first error, not repetitive ones
                    if retry_count == 0:
                        print(f"⚠️ Error: {type(e).__name__}")
                    retry_count += 1
                    if retry_count < max_retries:
                        await asyncio.sleep(backoff_time * retry_count)
                    else:
                        break
                    
            # Only log timeout once after all retries
            if timeout_occurred and retry_count >= max_retries:
                print(f"Error in Approach 2: Read timed out")
        
        # APPROACH 3: Try search-users endpoint to find the user
        if user_needs_search:
            print(f"🔎 APPROACH 3: Search users for @{username}")
            retry_count = 0
            
            while retry_count < max_retries and user_needs_search:
                try:
                    url = ENDPOINTS["search_users"]
                    # Search directly for the username as keyword
                    params = {"keyword": username, "count": "5", "cursor": "0"}
                    
                    print(f"Request: GET {url} with params {params}")
                    response = requests.get(url, headers=headers, params=params, timeout=15)
                    print(f"Response Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data and "user_list" in data:
                            users = data["user_list"]
                            
                            # Look for exact username match first
                            for user in users:
                                if "user_info" in user and user["user_info"].get("unique_id", "").lower() == username.lower():
                                    print(f"✅ SUCCESS: Found exact username match in search results")
                                    # Convert to standard format
                                    user_info = user["user_info"]
                                    user_data = {
                                        "nickname": user_info.get("nickname", username),
                                        "signature": user_info.get("signature", "No bio available"),
                                        "follower_count": user_info.get("follower_count", 0),
                                        "avatar_larger": {"url_list": [user_info.get("avatar_larger", "")]},
                                        "uid": user_info.get("uid", "")
                                    }
                                    user_needs_search = False
                                    print(f"Display Name: {user_data.get('nickname', 'Unknown')}")
                                    print(f"Follower Count: {user_data.get('follower_count', 'Unknown')}")
                                    return user_data
                            
                            # If no exact match but we have results, take the top one
                            if users and not user_data:
                                print(f"✅ SUCCESS: Using top search result for @{username}")
                                user = users[0]
                                if "user_info" in user:
                                    # Convert to standard format
                                    user_info = user["user_info"]
                                    user_data = {
                                        "nickname": user_info.get("nickname", username),
                                        "signature": user_info.get("signature", "No bio available"),
                                        "follower_count": user_info.get("follower_count", 0),
                                        "avatar_larger": {"url_list": [user_info.get("avatar_larger", "")]},
                                        "uid": user_info.get("uid", "")
                                    }
                                    user_needs_search = False
                                    print(f"Display Name: {user_data.get('nickname', 'Unknown')}")
                                    print(f"Follower Count: {user_data.get('follower_count', 'Unknown')}")
                                    print(f"Note: This is the closest match, not an exact username match")
                                    return user_data
                    
                    # If rate limited, backoff and retry
                    if response.status_code == 429:
                        retry_count += 1
                        wait_time = backoff_time * retry_count
                        print(f"⚠️ RATE LIMITED: Waiting {wait_time}s before retry {retry_count}/{max_retries}")
                        await asyncio.sleep(wait_time)
                    else:
                        # Try next approach
                        break
                        
                except Exception as e:
                    print(f"Error in Approach 3: {str(e)}")
                    retry_count += 1
                    if retry_count < max_retries:
                        await asyncio.sleep(backoff_time * retry_count)
                    else:
                        break
        
        # APPROACH 4: Alternative API provider's user info endpoint
        if user_needs_search:
            print(f"🔎 APPROACH 4: Alternative API provider for @{username}")
            retry_count = 0
            
            while retry_count < max_retries and user_needs_search:
                try:
                    url = f"{BASE_URL_ALTERNATIVE}/user/info"
                    params = {"unique_id": username}
                    
                    print(f"Request: GET {url} with params {params}")
                    response = requests.get(url, headers=headers_alternative, params=params, timeout=12)
                    print(f"Response Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data and "user" in data:
                            print(f"✅ SUCCESS: Alternative API found @{username}")
                            user_data = data["user"]
                            user_needs_search = False
                            print(f"Display Name: {user_data.get('nickname', 'Unknown')}")
                            print(f"Follower Count: {user_data.get('follower_count', 'Unknown')}")
                            return user_data
                    
                    # If rate limited, backoff and retry
                    if response.status_code == 429:
                        retry_count += 1
                        wait_time = backoff_time * retry_count
                        print(f"⚠️ RATE LIMITED: Waiting {wait_time}s before retry {retry_count}/{max_retries}")
                        await asyncio.sleep(wait_time)
                    else:
                        # Last approach failed
                        break
                        
                except Exception as e:
                    print(f"Error in Approach 4: {str(e)}")
                    retry_count += 1
                    if retry_count < max_retries:
                        await asyncio.sleep(backoff_time * retry_count)
                    else:
                        break
        
        # FALLBACK: Create minimal user object if all approaches failed
        if user_needs_search:
            print(f"🔄 CREATING MINIMAL USER OBJECT for @{username} after all approaches failed")
            return {
                "nickname": username,
                "signature": "Profile information not available",
                "follower_count": 0,
                "avatar_larger": {"url_list": [""]},
                "uid": ""
            }
    
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__} when fetching @{username}")
        # Last resort: Create a minimal user object even after fatal error
        return {
            "nickname": username,
            "signature": "Profile information not available",
            "follower_count": 0,
            "avatar_larger": {"url_list": [""]},
            "uid": ""
        }

async def get_user_videos(user_id: str, count: int = 3) -> List[Dict]:
    """
    Get recent videos for a user using multiple endpoints
    
    Args:
        user_id: TikTok user ID
        count: Number of videos to return
        
    Returns:
        List of video data
    """
    try:
        print(f"🎥 FETCHING VIDEOS for user_id: {user_id}")
        
        # Try multiple approaches to fetch videos
        max_retries = 2  # Per endpoint
        backoff_time = 2
        
        # APPROACH 1: Use standard user-posts endpoint
        print(f"🔎 APPROACH 1: Standard user-posts endpoint")
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                url = ENDPOINTS["user_posts"]
                params = {
                    "user_id": user_id,
                    "count": str(count),
                    "max_cursor": "0"
                }
                
                print(f"Request: GET {url} with params {params}")
                response = requests.get(url, headers=headers, params=params, timeout=12)
                print(f"Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "aweme_list" in data and data["aweme_list"]:
                        video_count = len(data["aweme_list"])
                        print(f"✅ SUCCESS: Retrieved {video_count} videos using standard endpoint")
                        return data["aweme_list"]
                    else:
                        print("⚠️ No videos found in standard endpoint response")
                
                # If rate limited, backoff and retry
                if response.status_code == 429:
                    retry_count += 1
                    wait_time = backoff_time * retry_count
                    print(f"⚠️ RATE LIMITED: Waiting {wait_time}s before retry")
                    await asyncio.sleep(wait_time)
                else:
                    # Try next approach if this one didn't work
                    break
                    
            except Exception as e:
                print(f"Error in Approach 1: {type(e).__name__}")
                retry_count += 1
                if retry_count < max_retries:
                    await asyncio.sleep(backoff_time * retry_count)
                else:
                    break
        
        # APPROACH 2: Use search keyword with the user ID to find videos
        print(f"🔎 APPROACH 2: Search posts endpoint with user ID")
        retry_count = 0
        
        try:
            # First try to get videos through search
            url = f"{BASE_URL}/search-posts"
            params = {
                "keyword": f"user:{user_id}",  # Using user ID as keyword
                "count": str(count),
                "offset": "0"
            }
            
            print(f"Request: GET {url} with params {params}")
            response = requests.get(url, headers=headers, params=params, timeout=15)
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data and "aweme_list" in data and data["aweme_list"]:
                    videos = data["aweme_list"]
                    print(f"✅ SUCCESS: Found {len(videos)} videos through search posts")
                    return videos
                
        except Exception as e:
            print(f"Error in Approach 2: {type(e).__name__}")
        
        # APPROACH 3: Try the alternative API provider
        print(f"🔎 APPROACH 3: Alternative API provider")
        
        try:
            alt_url = f"{BASE_URL_ALTERNATIVE}/user/posts"
            alt_params = {
                "user_id": user_id,
                "count": str(count),
                "cursor": "0"
            }
            
            print(f"Request: GET {alt_url} with params {alt_params}")
            alt_response = requests.get(alt_url, headers=headers_alternative, params=alt_params, timeout=12)
            print(f"Response Status: {alt_response.status_code}")
            
            if alt_response.status_code == 200:
                alt_data = alt_response.json()
                if "aweme_list" in alt_data and alt_data["aweme_list"]:
                    videos = alt_data["aweme_list"]
                    print(f"✅ SUCCESS: Retrieved {len(videos)} videos using alternative API")
                    return videos
                
        except Exception as e:
            print(f"Error in Approach 3: {type(e).__name__}")
        
        # If all approaches failed, return empty list
        print(f"❌ ALL APPROACHES FAILED: Unable to fetch videos for user_id {user_id}")
        return []
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__} when fetching videos for user_id {user_id}")
        return []

#-----------------------------------------------------------------------------
# Helper Functions
#-----------------------------------------------------------------------------

def get_profile_pic_url(user_data: Dict) -> str:
    """
    Extract profile picture URL from TikTok user data
    
    Args:
        user_data: User data from ScrapTik API
        
    Returns:
        URL string to user's profile picture or empty string if not found
    """
    try:
        # Check different avatar fields in order of preference
        if "avatar_larger" in user_data:
            # Handle both string and dictionary cases
            if isinstance(user_data["avatar_larger"], str):
                return user_data["avatar_larger"]
            elif isinstance(user_data["avatar_larger"], dict) and "url_list" in user_data["avatar_larger"]:
                urls = user_data["avatar_larger"]["url_list"]
                if urls and isinstance(urls, list) and len(urls) > 0:
                    return urls[0] if isinstance(urls[0], str) else ""
        
        # Try avatar_medium next
        if "avatar_medium" in user_data:
            if isinstance(user_data["avatar_medium"], str):
                return user_data["avatar_medium"]
            elif isinstance(user_data["avatar_medium"], dict) and "url_list" in user_data["avatar_medium"]:
                urls = user_data["avatar_medium"]["url_list"]
                if urls and isinstance(urls, list) and len(urls) > 0:
                    return urls[0] if isinstance(urls[0], str) else ""
        
        # Try avatar_thumb as fallback
        if "avatar_thumb" in user_data:
            if isinstance(user_data["avatar_thumb"], str):
                return user_data["avatar_thumb"]
            elif isinstance(user_data["avatar_thumb"], dict) and "url_list" in user_data["avatar_thumb"]:
                urls = user_data["avatar_thumb"]["url_list"]
                if urls and isinstance(urls, list) and len(urls) > 0:
                    return urls[0] if isinstance(urls[0], str) else ""
        
        # Try direct avatar field
        if "avatar" in user_data and isinstance(user_data["avatar"], str):
            return user_data["avatar"]
            
        # If all those fail, see if there's a raw avatar URL
        if "avatar_url" in user_data and isinstance(user_data["avatar_url"], str):
            return user_data["avatar_url"]
        
        # Return empty string if nothing found
        print(f"No profile picture URL found for user")
        return ""
        
    except Exception as e:
        print(f"Error extracting profile picture URL: {type(e).__name__}")
        return ""

def get_video_thumbnail(video_data: Dict) -> str:
    """
    Extract thumbnail URL from TikTok video data
    
    Args:
        video_data: Video data from ScrapTik API
        
    Returns:
        URL string to video thumbnail or empty string if not found
    """
    try:
        # Handle various thumbnail formats with better error handling
        # Check different thumbnail fields in order of preference
        if "cover" in video_data:
            # Handle both string and dictionary cases
            if isinstance(video_data["cover"], str):
                return video_data["cover"]
            elif isinstance(video_data["cover"], dict) and "url_list" in video_data["cover"]:
                urls = video_data["cover"]["url_list"]
                if urls and isinstance(urls, list) and len(urls) > 0:
                    return urls[0] if isinstance(urls[0], str) else ""
        
        # Try origin_cover next
        if "origin_cover" in video_data:
            if isinstance(video_data["origin_cover"], str):
                return video_data["origin_cover"]
            elif isinstance(video_data["origin_cover"], dict) and "url_list" in video_data["origin_cover"]:
                urls = video_data["origin_cover"]["url_list"]
                if urls and isinstance(urls, list) and len(urls) > 0:
                    return urls[0] if isinstance(urls[0], str) else ""
        
        # Try thumbnail as fallback
        if "thumbnail" in video_data:
            if isinstance(video_data["thumbnail"], str):
                return video_data["thumbnail"]
            elif isinstance(video_data["thumbnail"], dict) and "url_list" in video_data["thumbnail"]:
                urls = video_data["thumbnail"]["url_list"]
                if urls and isinstance(urls, list) and len(urls) > 0:
                    return urls[0] if isinstance(urls[0], str) else ""
                    
        # Try direct thumbnail field
        if "thumbnail_url" in video_data and isinstance(video_data["thumbnail_url"], str):
            return video_data["thumbnail_url"]
        
        # Return empty string if nothing found
        print(f"No thumbnail URL found for video")
        return ""
    except Exception as e:
        print(f"Error getting thumbnail URL: {type(e).__name__}")
        return ""

#-----------------------------------------------------------------------------
# OpenAI Integration
#-----------------------------------------------------------------------------

async def score_usernames_relevance(usernames: List[TikTokUsername], query: str) -> List[TikTokUsername]:
    """
    Score the relevance of usernames to the search query using GPT
    
    Args:
        usernames: List of TikTok usernames
        query: Original search query
        
    Returns:
        List of usernames with relevance scores
    """
    try:
        # If only a few usernames, give them high scores
        if len(usernames) <= 3:
            for username in usernames:
                username.search_relevance = 0.9
            return usernames
            
        # Skip scoring for efficiency if many usernames
        if len(usernames) > 20:
            # Just give them all medium scores
            for username in usernames:
                username.search_relevance = 0.7
            return usernames
        
        # Prepare scoring prompt
        # Format the query to be more specific for finding exact users
        formattedQuery = f"Find the exact TikTok username for: {query}. If you know the exact username, return it. If not, say 'No specific user found'"
        
        system_prompt = """You are an expert at determining the relevance of TikTok usernames to search queries.
        Rate each username based on how likely it is to be relevant to the query. Consider username patterns, 
        context, and source URL. Rate on a scale from 0 to 1, where 1 is highly relevant."""
        
        user_prompt = f"""Query: {formattedQuery}

        Please rate these TikTok usernames for relevance to the query:
        
        """
        
        # Add each username with context
        for i, username in enumerate(usernames[:15]):  # Limit to 15 to avoid token limits
            context = username.context or "No context available"
            source = username.source
            user_prompt += f"{i+1}. @{username.username} (Source: {source})\nContext: {context}\n\n"
            
        user_prompt += """Rate each username with a number between 0 and 1, where:
        - 1.0 = Highly relevant
        - 0.7 = Moderately relevant
        - 0.5 = Possibly relevant
        - 0.2 = Probably not relevant
        - 0.0 = Definitely not relevant
        
        Respond with a JSON object where keys are the numbers and values are the scores:
        {
          "1": 0.8,
          "2": 0.3,
          ...
        }
        """
        
        # Call GPT-4 for scoring
        completion = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        
        # Parse the response
        try:
            content = completion.choices[0].message.content
            scores = json.loads(content)
            for i, username in enumerate(usernames[:15]):
                score_key = str(i+1)
                if score_key in scores:
                    username.search_relevance = float(scores[score_key])
                else:
                    username.search_relevance = 0.5  # Default if not scored
        except Exception as e:
            print(f"Error parsing relevance scores: {type(e).__name__}")
            # Assign default scores
            for username in usernames:
                username.search_relevance = 0.5
        
        # For usernames beyond the first 15, give them lower scores
        for i, username in enumerate(usernames[15:]):
            username.search_relevance = 0.5
        
        return usernames
        
    except Exception as e:
        print(f"Error scoring usernames: {type(e).__name__}")
        # Fallback: give all usernames medium scores
        for username in usernames:
            username.search_relevance = 0.5
        return usernames

async def analyze_profile_relevance(user_info: Dict, query: str, criteria: List[str]) -> Dict:
    """
    Analyze a user profile for relevance to the search query
    
    Args:
        user_info: User information
        query: Original search query
        criteria: List of required criteria
        
    Returns:
        Dict with relevance score and explanation
    """
    try:
        # Prepare analysis prompt
        system_prompt = """You are an expert at analyzing TikTok profiles for relevance to search queries.
        Your job is to determine if a TikTok profile matches a specific query and required criteria.
        Provide a relevance score and detailed explanation."""
        
        user_prompt = f"""Query: {query}
        
        Required criteria:
        {chr(10).join(['- ' + criterion for criterion in criteria])}
        
        TikTok Profile:
        - Username: @{user_info.get('username', '')}
        - Display Name: {user_info.get('display_name', '')}
        - Bio: {user_info.get('bio', '')}
        - Follower Count: {user_info.get('follower_count', 0)}
        
        Analyze this profile and determine:
        1. How relevant is this profile to the query? (Score 0-1)
        2. Does it meet the required criteria? Why or why not?
        3. What evidence in the profile supports your conclusion?
        
        Respond with a JSON object:
        {
          "relevance_score": 0.9,
          "explanation": "Detailed explanation here..."
        }
        """
        
        # Call GPT for analysis
        completion = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        
        try:
            content = completion.choices[0].message.content
            result = json.loads(content)
            return {
                "relevance_score": float(result.get("relevance_score", 0.5)),
                "explanation": result.get("explanation", "No explanation provided")
            }
        except Exception as parse_error:
            print(f"Error parsing profile analysis: {type(parse_error).__name__}")
            # Manually extract data using regex if JSON parsing fails
            score_match = re.search(r"relevance_score\"?\s*:\s*([0-9.]+)", content)
            score = float(score_match.group(1)) if score_match else 0.5
            
            expl_match = re.search(r"explanation\"?\s*:\s*\"([^\"]+)", content)
            explanation = expl_match.group(1) if expl_match else "Analysis failed"
            
            return {
                "relevance_score": score,
                "explanation": explanation
            }
            
    except Exception as e:
        print(f"Error analyzing profile relevance: {type(e).__name__}")
        return {
            "relevance_score": 0.5,
            "explanation": "Error during analysis"
        }

#-----------------------------------------------------------------------------
# API Endpoints
#-----------------------------------------------------------------------------

@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Welcome to TikTok Analyzer API"}

@app.post("/web-enhanced-search")
async def web_enhanced_search(request: WebEnhancedSearchRequest):
    """
    Web-enhanced search for finding TikTok profiles using Tavily search
    
    Args:
        request: Search request parameters
        
    Returns:
        Search response with matched profiles
    """
    try:
        print(f"==== WEB-ENHANCED SEARCH REQUEST ====\nQuery: {request.query}")
        
        # Initialize response
        search_response = WebEnhancedSearchResponse(
            query=request.query,
            search_strategy="Tavily Search API + ScrapTik API + GPT-4 Analysis"
        )
        
        # Step 1: Extract search criteria using GPT-4
        system_prompt = """Analyze this search query for a TikTok user search and extract the specific criteria."""
        user_prompt = f"""Query: {request.query}
        
        Extract specific required criteria as a short list. These should be objective attributes a TikTok user must have to be considered a match. For example: 'must be from Mexico', 'must post about fashion', etc.
        
        Return a JSON object with these fields:
        - required_criteria: an array of strings, each describing one criterion
        - search_explanation: a detailed explanation of what we're looking for
        """
        
        completion = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        
        criteria_content = completion.choices[0].message.content
        try:
            criteria_analysis = json.loads(criteria_content)
            if criteria_analysis:
                search_response.required_criteria = criteria_analysis.get("required_criteria", [])
                search_response.search_strategy += f"\n\nSearching for: {criteria_analysis.get('search_explanation', '')}" 
        except:
            # Fallback if JSON parsing fails
            search_response.required_criteria = ["Relevant to: " + request.query]
        
        # Step 2: Use Tavily Search to find TikTok usernames
        print(f"\n🔍 STARTING TAVILY SEARCH: {request.query}")
        # Use the smart query optimization in perform_tavily_search
        tavily_results = perform_tavily_search(request.query, max_results=max(8, request.max_results * 2))
        search_response.usernames_found = len(tavily_results.get('results', [])) if tavily_results else 0
        print(f"🔍 Found {search_response.usernames_found} results via Tavily search")
        
        # If no usernames found, exit early
        if not tavily_results or 'results' not in tavily_results or not tavily_results['results']:
            print("❌ No usernames found via Tavily search, returning empty results")
            return search_response
        
        # Step 3: Fetch and analyze profiles
        user_matches = []
        analyzed_count = 0
        successful_count = 0
        
        # Process usernames with higher relevance scores first
        usernames = []
        for item in tavily_results['results']:
            title = item.get('title', '')
            url = item.get('url', '')
            content = item.get('content', '')
            
            # Combine all content for better extraction
            full_content = f"{title}\n{content}"
            
            # Extract usernames
            extracted = extract_tiktok_usernames(url, title, full_content)
            for username in extracted:
                usernames.append(TikTokUsername(
                    username=username,
                    source="Tavily Web Intelligence",
                    context=f"Found in: {title[:50]}"
                ))
        
        # Score usernames with GPT-4
        if usernames:
            usernames = await score_usernames_relevance(usernames, request.query)
            # Sort by relevance
            usernames.sort(key=lambda x: x.search_relevance or 0, reverse=True)
            # Print up to 5 usernames for debugging
            print(f"Found {len(usernames)} usernames from Tavily results:")
            for i, u in enumerate(usernames[:5]):
                print(f"  {i+1}. @{u.username} (Relevance: {u.search_relevance:.2f})")
        
        # Limit to prevent too many API calls
        max_analysis = min(15, request.max_results * 3)
        
        for username_obj in usernames:
            # Limit the number of API calls and stop if we have enough successful results
            if analyzed_count >= max_analysis or successful_count >= request.max_results:
                break
                
            username = username_obj.username
            print(f"Analyzing user: @{username}")
            
            # Get full user details
            user_data = await get_user_by_username(username)
            if not user_data:
                print(f"Failed to fetch data for @{username}")
                continue
                
            analyzed_count += 1
            
            # Extract relevant user information
            user_info = {
                "username": username,
                "display_name": user_data.get("nickname", ""),
                "bio": user_data.get("signature", ""),
                "follower_count": user_data.get("follower_count", 0),
                "profile_pic": get_profile_pic_url(user_data)
            }
            
            print(f"Processing: @{username} ({user_info['display_name']}) - {user_info['follower_count']} followers")
            
            # Skip users with no followers or empty bios unless search relevance is high
            if (int(user_info['follower_count']) < 100 or not user_info['bio'].strip()) and (username_obj.search_relevance or 0) < 0.8:
                print(f"Skipping @{username} - insufficient followers/bio")
                continue
                
            # Analyze relevance using GPT-4
            relevance_analysis = await analyze_profile_relevance(
                user_info, 
                request.query, 
                search_response.required_criteria
            )
            
            relevance_score = relevance_analysis.get("relevance_score", 0)
            explanation = relevance_analysis.get("explanation", "No explanation available")
            
            print(f"@{username} relevance score: {relevance_score:.2f}")
            
            # Only include profiles that meet the minimum relevance threshold
            if relevance_score >= request.min_relevance_score:
                # Get recent videos
                videos = []
                if "sec_uid" in user_data:
                    print(f"Fetching videos for @{username}")
                    recent_videos = await get_user_videos(user_data["sec_uid"], 3)
                    for video in recent_videos:
                        if len(videos) >= 3:
                            break
                        desc = video.get("desc", "")
                        thumbnail = get_video_thumbnail(video)
                        if desc or thumbnail:
                            videos.append({
                                "caption": desc,
                                "thumbnail": thumbnail
                            })
                    print(f"Found {len(videos)} videos for @{username}")
                
                # Add to matches - specify Tavily as the discovery method
                discovery_method = "Tavily Web Search"
                
                # Create user match object
                # Ensure profile_pic is a string, not a dict
                profile_pic = ""
                if "profile_pic" in user_info:
                    if isinstance(user_info["profile_pic"], str):
                        profile_pic = user_info["profile_pic"]
                    else:
                        # Log warning but continue with empty string
                        print(f"Warning: profile_pic is not a string for @{username}")
                
                user_match = WebEnhancedUserMatch(
                    username=username,
                    display_name=user_info["display_name"],
                    bio=user_info["bio"],
                    follower_count=user_info["follower_count"],
                    profile_pic=profile_pic,
                    why_matches=explanation,
                    relevance_score=relevance_score,
                    discovery_method=discovery_method,
                    videos=videos
                )
                
                user_matches.append(user_match)
                successful_count += 1  # Increment successful match counter
                print(f"✅ Added @{username} to matches ({successful_count}/{request.max_results})")
        
        # Sort matches by relevance score
        user_matches.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Add matches to response
        search_response.matches = user_matches[:request.max_results]
        search_response.profiles_analyzed = analyzed_count
        print(f"Final results: {len(search_response.matches)} matches from {search_response.profiles_analyzed} analyzed profiles")
        
        # If no matches found but we have usernames, create matches directly from usernames with enhanced profile data
        if not search_response.matches and usernames:
            print(f"\n💡 Creating comprehensive profile matches from {len(usernames)} usernames")
            # Take the top usernames by search relevance
            top_usernames = sorted(usernames, key=lambda x: x.search_relevance or 0, reverse=True)[:request.max_results]
            
            print("🔄 Starting enhanced profile data fetch for top usernames")
            for username_obj in top_usernames:
                # Use our improved get_user_by_username function which handles multiple APIs and fallbacks
                user_data = await get_user_by_username(username_obj.username)
                
                if user_data:
                    # If we have any user data (even minimal), create a match
                    # Make sure profile_pic is always a string
                    profile_pic_url = get_profile_pic_url(user_data)
                    
                    profile_match = WebEnhancedUserMatch(
                        username=username_obj.username,
                        display_name=user_data.get("nickname", username_obj.username),
                        bio=user_data.get("signature", ""),
                        follower_count=user_data.get("follower_count", 0),
                        profile_pic=profile_pic_url,
                        why_matches=f"Found via Tavily Search for '{request.query}'",
                        relevance_score=username_obj.search_relevance or 0.8,
                        discovery_method="Tavily Web Search" if user_data.get("follower_count", 0) > 0 else "Tavily Web Search (Limited Data)"
                    )
                    
                    # If user has an ID, try to get videos too
                    if user_data.get("uid"):
                        try:
                            videos = await get_user_videos(user_data["uid"], count=3)
                            if videos:
                                # Process videos
                                profile_match.videos = []
                                for video in videos[:3]:
                                    # Get thumbnail with better error handling
                                    thumbnail = get_video_thumbnail(video)
                                    profile_match.videos.append({
                                        "id": video.get("aweme_id", ""),
                                        "desc": video.get("desc", "No description"),
                                        "create_time": video.get("create_time", 0),
                                        "thumbnail": thumbnail
                                    })
                                print(f"🎥 Added {len(profile_match.videos)} videos for @{username_obj.username}")
                        except Exception as video_err:
                            print(f"Error fetching videos: {str(video_err)}")
                    
                    # Add relevance explanation using GPT-4
                    try:
                        if search_response.required_criteria:
                            # Create content for GPT-4 analysis
                            content_for_analysis = f"TikTok User: @{username_obj.username}\n"
                            content_for_analysis += f"Display Name: {profile_match.display_name}\n"
                            content_for_analysis += f"Bio: {profile_match.bio}\n"
                            content_for_analysis += f"Follower Count: {profile_match.follower_count}\n"
                            
                            # Add video content if available
                            if hasattr(profile_match, 'videos') and profile_match.videos:
                                content_for_analysis += "\nRecent Videos:\n"
                                for i, video in enumerate(profile_match.videos):
                                    content_for_analysis += f"Video {i+1}: {video.get('desc', '')}\n"
                            
                            # GPT-4 analysis
                            relevance_prompt = f"""You are analyzing the relevance of a TikTok profile for the search: '{request.query}'.
                            
                            Search Criteria: {', '.join(search_response.required_criteria)}
                            
                            Profile Information:
                            {content_for_analysis}
                            
                            Explain in 1-2 sentences why this profile is relevant to the search query. If it's not clearly relevant, explain why it might be a partial match.
                            """
                            
                            explanation = await get_gpt_completion(relevance_prompt, max_tokens=150)
                            if explanation and explanation.strip():
                                profile_match.why_matches = explanation.strip()
                                print(f"💬 Added relevance explanation for @{username_obj.username}")
                    except Exception as gpt_err:
                        print(f"Error getting relevance explanation: {str(gpt_err)}")
                    
                    search_response.matches.append(profile_match)
                    print(f"✅ Added enhanced profile match for @{username_obj.username}")
                else:
                    # This should rarely happen since get_user_by_username now returns minimal data in worst case
                    simple_match = WebEnhancedUserMatch(
                        username=username_obj.username,
                        display_name=username_obj.username,
                        bio="Profile information not available",
                        follower_count=0,
                        profile_pic="",
                        why_matches=f"Found via Tavily Search for '{request.query}'",
                        relevance_score=username_obj.search_relevance or 0.7,
                        discovery_method="Tavily Web Search (Direct Match)"
                    )
                    search_response.matches.append(simple_match)
                    print(f"➕ Added simple match for @{username_obj.username}")
            
            # Mark that we did profile analysis
            search_response.profiles_analyzed = len(search_response.matches)
            print(f"✅ Added {len(search_response.matches)} enhanced profile matches in total")
        
        return search_response
    
    except Exception as e:
        print(f"Error in web-enhanced search: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Web-enhanced search failed: {str(e)}")

#-----------------------------------------------------------------------------
# Basic REST Endpoints for backward compatibility
#-----------------------------------------------------------------------------

class UserInfo(BaseModel):
    """Basic user info model"""
    username: str

@app.get("/user/{username}")
async def get_user(username: str):
    """
    Get user info by username
    
    Args:
        username: TikTok username
        
    Returns:
        User data
    """
    user_data = await get_user_by_username(username)
    if not user_data:
        raise HTTPException(status_code=404, detail=f"User @{username} not found")
    return user_data

#-----------------------------------------------------------------------------
# Additional Frontend Compatibility Endpoints
#-----------------------------------------------------------------------------

class UserCriteria(BaseModel):
    """User search criteria model"""
    min_followers: Optional[int] = None
    max_followers: Optional[int] = None
    min_following: Optional[int] = None
    max_following: Optional[int] = None
    min_likes: Optional[int] = None
    max_likes: Optional[int] = None
    verified: Optional[bool] = None

class SearchUsersRequest(BaseModel):
    """Search users request model"""
    query: str
    criteria: Optional[UserCriteria] = None
    count: int = 20
    deep_analysis: bool = False

@app.post("/search-users")
async def search_users(request: SearchUsersRequest):
    """
    Search for TikTok users based on query and criteria
    
    Args:
        request: Search request with query and criteria
        
    Returns:
        List of matching TikTok users
    """
    try:
        print(f"Searching for TikTok users: '{request.query}'")
        
        # Use Tavily search first for better discovery
        print("🔍 USING TAVILY FIRST for better web discovery")
        # We'll let the perform_tavily_search function create an optimized query
        tavily_results = perform_tavily_search(request.query, request.count)
        
        # Extract usernames from Tavily results
        extracted_usernames = []
        
        if tavily_results and "results" in tavily_results:
            print(f"✅ Found {len(tavily_results['results'])} Tavily search results")
            
            # Analyze each search result to extract usernames
            for result in tavily_results["results"]:
                url = result.get("url", "")
                title = result.get("title", "")
                content = result.get("content", "")
                
                # Extract usernames from this result
                result_usernames = extract_tiktok_usernames(url, title, content)
                
                for username in result_usernames:
                    extracted_usernames.append(TikTokUsername(
                        username=username,
                        source="Tavily Web Intelligence",
                        context=f"{title}: {content[:100]}..."
                    ))
            
            # Debug output
            if extracted_usernames:
                print(f"✅ Extracted {len(extracted_usernames)} usernames from Tavily results:")
                for i, u in enumerate(extracted_usernames[:5]):
                    print(f"  {i+1}. @{u.username} (Source: {u.source})")
            else:
                print("⚠️ No usernames extracted from Tavily results, falling back to direct TikTok search")
                
        # Fall back to direct TikTok search for additional usernames
        tiktok_usernames = await search_directly_on_tiktok(request.query, request.count)
        
        # Combine usernames from both sources with deduplication
        all_usernames = []
        seen_usernames = set()
        
        # First add Tavily usernames (higher priority since they come from web intelligence)
        for username in extracted_usernames:
            if username.username.lower() not in seen_usernames and len(all_usernames) < request.count:
                all_usernames.append(username)
                seen_usernames.add(username.username.lower())
        
        # Then add TikTok search usernames
        for username in tiktok_usernames:
            if username.username.lower() not in seen_usernames and len(all_usernames) < request.count:
                all_usernames.append(username)
                seen_usernames.add(username.username.lower())
        
        print(f"🔍 TOTAL USERNAMES FOUND: {len(all_usernames)}")
        if not all_usernames:
            print(f"No usernames found for query: '{request.query}'")
            return []
            
        # Process and enrich each user
        users = []
        for username_obj in all_usernames[:request.count]:
            try:
                # Get user info using our robust multi-endpoint approach
                user_data = await get_user_by_username(username_obj.username)
                
                if not user_data:
                    continue
                    
                # Check if user meets criteria
                if request.criteria:
                    criteria = request.criteria
                    # Check follower count criteria
                    if criteria.min_followers and user_data.get("follower_count", 0) < criteria.min_followers:
                        continue
                    if criteria.max_followers and user_data.get("follower_count", 0) > criteria.max_followers:
                        continue
                        
                    # Check following count criteria
                    if criteria.min_following and user_data.get("following_count", 0) < criteria.min_following:
                        continue
                    if criteria.max_following and user_data.get("following_count", 0) > criteria.max_following:
                        continue
                        
                    # Check likes count criteria
                    if criteria.min_likes and user_data.get("likes_count", 0) < criteria.min_likes:
                        continue
                    if criteria.max_likes and user_data.get("likes_count", 0) > criteria.max_likes:
                        continue
                        
                    # Check verified status
                    if criteria.verified is not None and user_data.get("verified", False) != criteria.verified:
                        continue
                
                # Create user object
                user = {
                    "id": user_data.get("uid", "") or user_data.get("sec_uid", ""),
                    "username": username_obj.username,
                    "display_name": user_data.get("nickname", username_obj.username),
                    "bio": user_data.get("signature", ""),
                    "follower_count": user_data.get("follower_count", 0),
                    "following_count": user_data.get("following_count", 0),
                    "likes_count": user_data.get("likes_count", 0),
                    "verified": user_data.get("verified", False),
                    "profile_pic": get_profile_pic_url(user_data)
                }
                
                # Add relevance analysis if deep_analysis is requested
                if request.deep_analysis and openai_client:
                    try:
                        # Extract criteria from the query
                        system_prompt = """Extract search criteria from the query. 
                        Return a list of specific requirements that a TikTok account should meet to be relevant."""
                        
                        user_prompt = f"Query: {request.query}\n\nWhat criteria should a TikTok account meet to be relevant to this query?"
                        
                        completion = openai_client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.3
                        )
                        
                        criteria_text = completion.choices[0].message.content
                        criteria_list = [c.strip() for c in criteria_text.split('\n') if c.strip()]
                        
                        # Analyze profile relevance
                        relevance_analysis = await analyze_profile_relevance(
                            {
                                "username": user["username"],
                                "display_name": user["display_name"],
                                "bio": user["bio"],
                                "follower_count": user["follower_count"]
                            },
                            request.query,
                            criteria_list
                        )
                        
                        # Add analysis to user object
                        user["analysis_result"] = {
                            "score": relevance_analysis.get("relevance_score", 0.5),
                            "explanation": relevance_analysis.get("explanation", "No explanation available")
                        }
                    except Exception as analysis_err:
                        print(f"Error in relevance analysis: {str(analysis_err)}")
                        user["analysis_result"] = {
                            "score": 0.5,
                            "explanation": "Analysis failed due to an error"
                        }
                
                # Add user to results
                users.append(user)
                print(f"✅ Added user @{username_obj.username} to results")
                
            except Exception as user_err:
                print(f"Error processing user @{username_obj.username}: {str(user_err)}")
                continue
        
        # Check if query mentions a specific location
        location_keywords = ["from", "in", "located in", "based in"]
        location_search = False
        query_lower = request.query.lower()
        
        for keyword in location_keywords:
            if keyword in query_lower:
                location_search = True
                print(f"Location-based search detected with keyword: {keyword}")
                break
                
        # Sort users with smarter location relevance
        if location_search:
            # Extract possible location from query
            location_parts = query_lower.split(" from ")  # Most common pattern "X from Y"
            target_location = ""
            
            if len(location_parts) > 1:
                target_location = location_parts[1].strip().split()[0]  # First word after "from"
                print(f"Target location detected: {target_location}")
                
            # Custom sort function that prioritizes username+bio location match, then relevance/followers
            def location_relevance_sort(user):
                username = user.get("username", "").lower()
                display_name = user.get("display_name", "").lower()
                bio = user.get("bio", "").lower()
                
                # Calculate a location match score
                location_score = 0
                if target_location:  # If we have a specific location target
                    if target_location in username or target_location in display_name:
                        location_score += 10  # Highest priority for username/display_name match
                    if target_location in bio:
                        location_score += 5   # Good priority for bio match
                
                # Get follower score (0-1 scale)
                follower_count = user.get("follower_count", 0)
                follower_score = min(follower_count / 1000000, 1)  # Cap at 1M followers for scoring
                
                # Combine scores - location is primary, followers secondary
                return (location_score, follower_score)
                
            # Sort by location relevance first, then by followers    
            users.sort(key=location_relevance_sort, reverse=True)
            print(f"Sorted results by location relevance for '{target_location}'")
        elif request.deep_analysis:
            # If deep analysis but not location-specific, sort by analysis score
            users.sort(key=lambda u: u.get("analysis_result", {}).get("score", 0), reverse=True)
        else:
            # Default sort by followers
            users.sort(key=lambda u: u.get("follower_count", 0), reverse=True)
        
        # Filter results if criteria specified
        if request.criteria:
            # Determine if request is about security/privacy
            if request.query and ('privacy' in request.query.lower() or 'security' in request.query.lower() or 'cybersecurity' in request.query.lower()):
                print("🔐 Security/privacy query detected - applying special filtering")
                # Apply strict filtering for privacy/security influencers
                keyword = request.query.lower()
                
                # First, compute the relevance score for all users
                for user in users:
                    # Add a relevance score to each user
                    user['security_relevance'] = security_privacy_relevance_score(user)
                
                # Filter by minimum score threshold (removes totally irrelevant results)
                minimum_threshold = 0.2  # Minimum relevance score to be included
                filtered_users = [u for u in users if u.get('security_relevance', 0) >= minimum_threshold]
                
                # If we have enough quality results, use only those that pass security check
                quality_users = [u for u in filtered_users if is_security_privacy_focused(u)]
                
                # Use quality results if we have enough, otherwise fall back to filtered
                if len(quality_users) >= 3:
                    users = quality_users
                    print(f"✅ Found {len(quality_users)} quality security/privacy influencers")
                elif len(filtered_users) >= 3:
                    users = filtered_users
                    print(f"⚠️ Using {len(filtered_users)} filtered results - couldn't find enough top-quality security influencers")
                # If all else fails, keep original results but still sort by relevance
                
                # Apply final sorting, prioritizing relevance score but also considering followers
                users.sort(key=lambda u: (-u.get('security_relevance', 0), -int(u.get('follower_count', 0))))
            elif location_search:  # Handle location-based queries (already sorted above)
                pass  # Already handled by location_relevance_sort above
            else:
                # Sort by follower count as default
                users.sort(key=lambda u: -int(u.get('follower_count', 0)))
            
        else:
            # Default sort by follower count 
            users.sort(key=lambda u: -int(u.get('follower_count', 0)))
        
        return users
            
    except Exception as e:
        print(f"Error in search_users: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

#-----------------------------------------------------------------------------
# Application Entry Point
#-----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import base64
import json
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import io
from PIL import Image
import openai

# Load environment variables
load_dotenv()

app = FastAPI(title="TikTok Analyzer")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure OpenAI client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ScrapTik API base URL
BASE_URL = "https://scraptik.p.rapidapi.com"

# Common headers for ScrapTik API
headers = {
    "X-RapidAPI-Key": RAPID_API_KEY,
    "X-RapidAPI-Host": "scraptik.p.rapidapi.com"
}

# Models
class UserCriteria(BaseModel):
    min_followers: Optional[int] = 0
    max_followers: Optional[int] = None
    min_following: Optional[int] = 0
    max_following: Optional[int] = None
    min_likes: Optional[int] = 0
    max_likes: Optional[int] = None
    verified: Optional[bool] = None

class SearchRequest(BaseModel):
    query: str
    criteria: UserCriteria
    count: Optional[int] = 20
    deep_analysis: Optional[bool] = False

class AnalysisResult(BaseModel):
    relevant: bool
    score: float
    explanation: str
    image_analysis: Optional[str] = None
    thumbnail_analysis: Optional[str] = None

class TikTokUser(BaseModel):
    id: str
    username: str
    display_name: str
    bio: str
    follower_count: int
    following_count: int
    likes_count: int
    verified: bool
    profile_pic: str
    analysis_result: Optional[AnalysisResult] = None

class PostSearchRequest(BaseModel):
    keyword: str
    count: Optional[int] = 20
    offset: Optional[int] = 0
    use_filters: Optional[int] = 0
    publish_time: Optional[int] = 0
    sort_type: Optional[int] = 0

class ContentAnalysisRequest(BaseModel):
    user_id: str
    query: str

# Helper Functions
def get_image_as_base64(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
        return None
    except Exception as e:
        print(f"Error fetching image: {e}")
        return None

def analyze_profile_picture(base64_image, query):
    """Analyze the profile picture using OpenAI Vision API"""
    try:
        # Check if OpenAI API key is configured
        if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE":
            return "OpenAI API key not configured. Cannot analyze profile picture."
        
        # Now we're actually using Vision API
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"This is a TikTok profile picture. Based on the query '{query}', is this person likely relevant? Provide a brief analysis focusing on visual elements that might indicate relevance to the query."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error using Vision API: {str(e)}")
            return f"Could not analyze image: {str(e)}"
            
    except Exception as e:
        print(f"Error analyzing profile picture: {str(e)}")
        return "Could not analyze profile picture due to an error."

def analyze_thumbnail(base64_image, query):
    """Analyze a video thumbnail using OpenAI Vision API"""
    try:
        # Check if OpenAI API key is configured
        if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE":
            return "OpenAI API key not configured. Cannot analyze thumbnail."
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"This is a TikTok video thumbnail. Based on the query '{query}', does this content appear to be relevant? Look for visual elements related to the query."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error using Vision API for thumbnail: {str(e)}")
            return f"Could not analyze thumbnail: {str(e)}"
            
    except Exception as e:
        print(f"Error analyzing thumbnail: {str(e)}")
        return "Could not analyze thumbnail due to an error."

def analyze_user_content(user, query):
    """Analyze if a user's content is relevant to the query using OpenAI"""
    try:
        # Prepare user data for analysis
        user_data = {
            "username": user.get("uniqueId", ""),
            "display_name": user.get("nickname", ""),
            "bio": user.get("signature", ""),
            "stats": {
                "follower_count": user.get("followerCount", 0),
                "following_count": user.get("followingCount", 0),
                "likes": user.get("heartCount", 0),
            },
            "verified": user.get("verified", False),
        }
        
        # Check if OpenAI API key is configured
        if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_OPENAI_API_KEY_HERE":
            return AnalysisResult(
                relevant=True,
                score=0.5,
                explanation="OpenAI API key not configured. Basic analysis: Potentially relevant based on keyword match.",
                image_analysis="Image analysis not available",
                thumbnail_analysis="Thumbnail analysis not available"
            )
        
        # Profile picture analysis if available
        profile_pic_analysis = ""
        if user.get("avatarMedium"):
            try:
                profile_pic_base64 = get_image_as_base64(user.get("avatarMedium"))
                if profile_pic_base64:
                    profile_pic_analysis = analyze_profile_picture(profile_pic_base64, query)
            except Exception as e:
                print(f"Error analyzing profile picture: {str(e)}")
                profile_pic_analysis = "Error analyzing profile picture"
        
        # Try to get a thumbnail from a recent video if available
        thumbnail_analysis = ""
        try:
            if "aweme_list" in user and isinstance(user["aweme_list"], list) and len(user["aweme_list"]) > 0:
                video = user["aweme_list"][0]
                if "video" in video and "cover" in video["video"]:
                    cover_url = None
                    if isinstance(video["video"]["cover"], str):
                        cover_url = video["video"]["cover"]
                    elif isinstance(video["video"]["cover"], dict) and "url_list" in video["video"]["cover"]:
                        if video["video"]["cover"]["url_list"] and len(video["video"]["cover"]["url_list"]) > 0:
                            cover_url = video["video"]["cover"]["url_list"][0]
                    
                    if cover_url:
                        thumbnail_base64 = get_image_as_base64(cover_url)
                        if thumbnail_base64:
                            thumbnail_analysis = analyze_thumbnail(thumbnail_base64, query)
        except Exception as e:
            print(f"Error analyzing thumbnail: {str(e)}")
            thumbnail_analysis = "Error analyzing thumbnail"

        # Basic keyword matching as fallback
        keywords = query.lower().split()
        username = user_data["username"].lower()
        display_name = user_data["display_name"].lower()
        bio = user_data["bio"].lower()
        
        matches = sum(1 for keyword in keywords if 
                      keyword in username or 
                      keyword in display_name or 
                      keyword in bio)
        
        relevance = min(matches / max(len(keywords), 1), 1.0)
        basic_result = AnalysisResult(
            relevant=relevance > 0.2,
            score=relevance,
            explanation=f"Basic keyword matching: {matches} keyword(s) found in profile.",
            image_analysis=profile_pic_analysis,
            thumbnail_analysis=thumbnail_analysis
        )

        # Try content relevance analysis with GPT if quota allows
        try:
            # Content relevance analysis prompt
            prompt = f"""
            Analyze this TikTok user's profile in relation to the search query: "{query}"
            
            User data:
            {json.dumps(user_data, indent=2)}
            
            Profile picture analysis: {profile_pic_analysis}
            
            Thumbnail analysis: {thumbnail_analysis}
            
            Is this user relevant to the search query? Consider:
            1. Does the username or display name suggest relevance?
            2. Does the bio contain relevant keywords or topics?
            3. Based on the profile picture analysis, does the visual content seem relevant?
            4. Based on the thumbnail analysis (if available), does their content seem relevant?
            
            Provide a relevance score from 0.0 to 1.0 and explanation.
            
            Output format:
            {{
              "relevant": true/false,
              "score": 0.0-1.0,
              "explanation": "Your explanation here"
            }}
            """
            
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You analyze TikTok profiles for relevance to search queries. Respond in JSON format."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = json.loads(response.choices[0].message.content)
            return AnalysisResult(
                relevant=result.get("relevant", False),
                score=result.get("score", 0.0),
                explanation=result.get("explanation", "No explanation provided"),
                image_analysis=profile_pic_analysis,
                thumbnail_analysis=thumbnail_analysis
            )
        except Exception as api_error:
            print(f"OpenAI API error: {str(api_error)}")
            # Return the basic result if OpenAI fails
            return basic_result
            
    except Exception as e:
        print(f"Error analyzing user content: {str(e)}")
        # Provide a basic fallback analysis
        keywords = query.lower().split()
        username = user.get("uniqueId", "").lower()
        display_name = user.get("nickname", "").lower()
        bio = user.get("signature", "").lower()
        
        # Simple keyword matching for fallback
        matches = sum(1 for keyword in keywords if 
                      keyword in username or 
                      keyword in display_name or 
                      keyword in bio)
        
        relevance = min(matches / max(len(keywords), 1), 1.0)
        return AnalysisResult(
            relevant=relevance > 0.2,
            score=relevance,
            explanation=f"AI analysis failed: {str(e)}. Basic keyword match: {matches} keyword(s) found in profile.",
            image_analysis="Image analysis failed",
            thumbnail_analysis="Thumbnail analysis failed"
        )

def does_user_match_criteria(user_data, criteria):
    """Check if a user matches the given filtering criteria"""
    if not user_data:
        return False
    
    # Check for follower count in multiple possible fields
    follower_count = 0
    for field in ["followerCount", "follower_count", "fans"]:
        if field in user_data:
            follower_count = user_data.get(field, 0)
            break
    
    # Check for following count in multiple possible fields
    following_count = 0
    for field in ["followingCount", "following_count", "following"]:
        if field in user_data:
            following_count = user_data.get(field, 0)
            break
    
    # Check for likes count in multiple possible fields
    likes_count = 0
    # First check direct fields
    for field in ["heartCount", "heart_count", "likes", "digg_count", "hearts", "total_favorited", "heart", "favorited_count", "total_hearts"]:
        if field in user_data:
            likes_count = user_data.get(field, 0)
            break
    
    # If not found, check stats object
    if likes_count == 0 and "stats" in user_data and isinstance(user_data["stats"], dict):
        stats = user_data["stats"]
        for field in ["heartCount", "heart_count", "likes", "digg_count", "hearts", "total_favorited", "heart", "favorited_count", "total_hearts"]:
            if field in stats:
                likes_count = stats[field]
                break
    
    # If still not found, check counts object
    if likes_count == 0 and "counts" in user_data and isinstance(user_data["counts"], dict):
        counts = user_data["counts"]
        for field in ["likes", "hearts", "heart", "digg", "total_favorited", "favorited_count", "total_hearts"]:
            if field in counts:
                likes_count = counts[field]
                break
    
    verified = user_data.get("verified", user_data.get("is_verified", False))
    
    # Check criteria
    if criteria.min_followers and follower_count < criteria.min_followers:
        return False
    if criteria.max_followers and follower_count > criteria.max_followers:
        return False
    if criteria.min_following and following_count < criteria.min_following:
        return False
    if criteria.max_following and following_count > criteria.max_following:
        return False
    if criteria.min_likes and likes_count < criteria.min_likes:
        return False
    if criteria.max_likes and likes_count > criteria.max_likes:
        return False
    if criteria.verified is not None and verified != criteria.verified:
        return False
    
    return True

# API Endpoints
@app.get("/")
def read_root():
    return {"message": "Welcome to TikTok Analyzer API"}

@app.get("/test")
def test_endpoint():
    """Simple endpoint to test if the API is working"""
    return {"status": "ok", "message": "API is working properly"}

@app.post("/search-users", response_model=List[TikTokUser])
async def search_users(request: SearchRequest, background_tasks: BackgroundTasks):
    """Search for TikTok users based on query and filter criteria"""
    try:
        print(f"\n\n==== SEARCH REQUEST ====")
        print(f"Query: {request.query}")
        print(f"Criteria: {request.criteria}")
        print(f"Count: {request.count}")
        print(f"Deep Analysis: {request.deep_analysis}")
        
        url = f"{BASE_URL}/search-users"
        params = {
            "keyword": request.query,
            "count": request.count,
            "cursor": "0"
        }
        
        print(f"\n==== MAKING API REQUEST ====")
        print(f"URL: {url}")
        print(f"Params: {params}")
        print(f"Headers: X-RapidAPI-Key: {'*' * 5 + RAPID_API_KEY[-5:] if RAPID_API_KEY else 'Not set'}")
        
        response = requests.get(url, headers=headers, params=params)
        
        print(f"\n==== API RESPONSE ====")
        print(f"Status Code: {response.status_code}")
        print(f"Response Text Preview: {response.text[:200]}...")
        
        if response.status_code != 200:
            error_detail = f"Error from ScrapTik API: {response.text}"
            print(f"API Error: {error_detail}")
            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )
        
        data = response.json()
        
        print(f"\n==== PARSED RESPONSE ====")
        print(f"Response Type: {type(data)}")
        print(f"API Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dictionary'}")
        
        users_data = data.get("user_list", [])
        print(f"User List Length: {len(users_data)}")
        
        if not users_data and isinstance(data, dict):
            print(f"WARNING: No user_list found. Available keys: {list(data.keys())}")
        
        # Try alternative keys if user_list isn't found
        if not users_data and isinstance(data, dict):
            for key in data.keys():
                if isinstance(data[key], list) and len(data[key]) > 0:
                    print(f"Found potential users list in key: {key} with {len(data[key])} items")
                    if "user" in key.lower():
                        print(f"Using {key} as user list")
                        users_data = data[key]
        
        # Filter users based on criteria and prepare response
        filtered_users = []
        pending_analyses = []  # Store users that need deep analysis

        for i, user_item in enumerate(users_data):
            print(f"\n==== USER ITEM {i} ====")
            
            # Handle different response formats
            user = None
            if isinstance(user_item, dict):
                if "user_info" in user_item:
                    user = user_item.get("user_info", {})
                    print(f"Found user_info in user_item")
                else:
                    user = user_item  # Maybe the user data is directly in the item
                    print(f"Using user_item directly as user")
            
            if not user:
                print(f"User item {i} has no user data. Keys: {list(user_item.keys()) if isinstance(user_item, dict) else 'Not a dictionary'}")
                continue
                
            print(f"User keys: {list(user.keys())}")
            
            # Check if required fields exist to avoid empty usernames
            username_field = None
            for field in ["uniqueId", "unique_id", "username", "name"]:
                if field in user:
                    username_field = field
                    print(f"Found username in field: {field} = {user.get(field)}")
                    break
                    
            if not username_field:
                print(f"User {i} missing username field. Available keys: {list(user.keys())}")
                continue
                
            if does_user_match_criteria(user, request.criteria):
                print(f"User matches criteria: {user.get(username_field)}")
                
                # Determine appropriate field names
                follower_field = next((f for f in ["followerCount", "follower_count", "fans"] if f in user), None)
                following_field = next((f for f in ["followingCount", "following_count", "following"] if f in user), None)
                likes_field = next((f for f in ["heartCount", "heart_count", "likes", "digg_count", "hearts", "total_favorited", "heart", "favorited_count", "total_hearts"] if f in user), None)
                display_name_field = next((f for f in ["nickname", "display_name", "name"] if f in user), None)
                bio_field = next((f for f in ["signature", "bio", "description"] if f in user), None)
                verify_field = next((f for f in ["verified", "is_verified"] if f in user), None)
                avatar_field = next((f for f in ["avatarMedium", "avatar_medium", "avatar", "avatar_url"] if f in user), None)
                
                # Add debug logging specifically for likes
                print(f"Looking for likes field. Available fields: {list(user.keys())}")
                print(f"Found likes_field: {likes_field}")
                if likes_field:
                    print(f"Likes value: {user.get(likes_field)}")
                
                # Try to find likes in a stats object if present
                likes_count = 0
                if likes_field:
                    likes_count = user.get(likes_field, 0)
                elif "stats" in user and isinstance(user["stats"], dict):
                    stats = user["stats"]
                    print(f"Found stats object with keys: {list(stats.keys())}")
                    for potential_field in ["heartCount", "heart_count", "likes", "digg_count", "hearts", "total_favorited", "heart", "favorited_count", "total_hearts", "diggCount"]:
                        if potential_field in stats:
                            likes_count = stats[potential_field]
                            print(f"Found likes in stats.{potential_field}: {likes_count}")
                            break
                # Check if there's a direct counts field
                elif "counts" in user and isinstance(user["counts"], dict):
                    counts = user["counts"]
                    print(f"Found counts object with keys: {list(counts.keys())}")
                    for potential_field in ["likes", "hearts", "heart", "digg", "total_favorited", "favorited_count", "total_hearts"]:
                        if potential_field in counts:
                            likes_count = counts[potential_field]
                            print(f"Found likes in counts.{potential_field}: {likes_count}")
                            break
                
                # Add one more check for direct stats fields at root level
                if likes_count == 0:
                    for potential_field in ["heartCount", "heart_count", "diggCount", "digg_count", "hearts", "total_favorited"]:
                        if potential_field in user:
                            likes_count = user.get(potential_field, 0)
                            print(f"Found likes directly in user.{potential_field}: {likes_count}")
                            break
                
                # Get profile picture as base64
                profile_pic_base64 = None
                if avatar_field and user.get(avatar_field):
                    print(f"Getting profile picture from {avatar_field}: {user.get(avatar_field)}")
                    profile_pic_base64 = get_image_as_base64(user.get(avatar_field))
                
                # Get video count if available
                video_count = 0
                if "video_count" in user:
                    video_count = user.get("video_count", 0)
                elif "aweme_count" in user:
                    video_count = user.get("aweme_count", 0)
                
                # Basic user information
                tiktok_user = TikTokUser(
                    id=user.get("uid", user.get("id", "")),
                    username=user.get(username_field, ""),
                    display_name=user.get(display_name_field, "Unknown") if display_name_field else "Unknown",
                    bio=user.get(bio_field, "") if bio_field else "",
                    follower_count=user.get(follower_field, 0) if follower_field else 0,
                    following_count=user.get(following_field, 0) if following_field else 0,
                    likes_count=likes_count,
                    verified=user.get(verify_field, False) if verify_field else False,
                    profile_pic=profile_pic_base64 or ""
                )
                
                print(f"Created TikTokUser object with username: {tiktok_user.username}")
                
                # Basic analysis for all users
                keywords = request.query.lower().split()
                username = tiktok_user.username.lower()
                display_name = tiktok_user.display_name.lower()
                bio = tiktok_user.bio.lower()
                
                matches = sum(1 for keyword in keywords if 
                             keyword in username or 
                             keyword in display_name or 
                             keyword in bio)
                
                relevance = min(matches / max(len(keywords), 1), 1.0)
                tiktok_user.analysis_result = AnalysisResult(
                    relevant=relevance > 0.2,
                    score=relevance,
                    explanation=f"Based on keyword matching: {matches} keyword(s) found in profile.",
                    image_analysis="Image analysis pending",
                    thumbnail_analysis="Thumbnail analysis pending"
                )
                
                # Add to filtered users
                filtered_users.append(tiktok_user)
                
                # If deep analysis is requested and we have OpenAI API key, queue this user for analysis
                if request.deep_analysis and OPENAI_API_KEY and OPENAI_API_KEY != "YOUR_OPENAI_API_KEY_HERE":
                    pending_analyses.append((user, i, request.query))
        
        print(f"\n==== SEARCH RESULTS ====")
        print(f"Found {len(filtered_users)} users matching criteria")
        
        if not filtered_users:
            print(f"WARNING: No users matched criteria or no valid users found")
            
        # If we have users to analyze deeply, schedule them as background tasks
        for user, index, query in pending_analyses:
            if index < len(filtered_users):
                background_tasks.add_task(analyze_user_and_update, user, query, index, filtered_users)
        
        return filtered_users
    except HTTPException:
        raise
    except Exception as e:
        error_message = f"Internal server error: {str(e)}"
        print(f"ERROR in search_users: {error_message}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_message)

def analyze_user_and_update(user, query, index, users_list):
    """Analyze a user and update the results"""
    analysis = analyze_user_content(user, query)
    if index < len(users_list):
        users_list[index].analysis_result = analysis

@app.get("/user-details/{username}")
async def get_user_details(username: str):
    """Get detailed information about a specific TikTok user"""
    try:
        url = f"{BASE_URL}/web/get-user"
        params = {"username": username}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error from ScrapTik API: {response.text}"
            )
        
        return response.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/user-info")
async def get_user_info(user_id: str):
    """Get detailed information about a specific TikTok user by ID"""
    try:
        url = f"{BASE_URL}/get-user-info"
        params = {"user_id": user_id}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error from ScrapTik API: {response.text}"
            )
        
        return response.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/user-posts/{user_id}")
async def get_user_posts(user_id: str, count: int = 5):
    """Get recent posts from a specific TikTok user"""
    try:
        print(f"\n==== FETCHING USER POSTS ====")
        print(f"User ID: {user_id}")
        print(f"Count: {count}")
        
        url = f"{BASE_URL}/user-posts"
        params = {
            "user_id": user_id,
            "count": count,
            "max_cursor": "0"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            error_detail = f"Error from ScrapTik API: {response.text}"
            print(f"API Error: {error_detail}")
            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )
            
        return response.json()
    except Exception as e:
        error_message = f"Error fetching user posts: {str(e)}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)

@app.get("/trending-creators")
async def get_trending_creators(region: str = "US"):
    """Get trending creators from TikTok"""
    try:
        print(f"\n==== FETCHING TRENDING CREATORS ====")
        print(f"Region: {region}")
        
        url = f"{BASE_URL}/trending-creators"
        params = {"region": region}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            error_detail = f"Error from ScrapTik API: {response.text}"
            print(f"API Error: {error_detail}")
            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )
        
        data = response.json()
        
        # Process the response to ensure likes count is available
        if "user_list" in data and isinstance(data["user_list"], list):
            for user_item in data["user_list"]:
                # Process each user to extract likes count from different sources
                user = user_item.get("user_info", user_item)
                
                # Find likes in different possible locations
                if not any(field in user for field in ["heartCount", "heart_count", "diggCount", "digg_count"]):
                    # Look for likes in stats
                    if "stats" in user and isinstance(user["stats"], dict):
                        stats = user["stats"]
                        for src_field, dest_field in [
                            ("heartCount", "heartCount"),
                            ("heart_count", "heart_count"),
                            ("diggCount", "diggCount"), 
                            ("digg_count", "digg_count")
                        ]:
                            if src_field in stats:
                                user[dest_field] = stats[src_field]
                    
                    # Look in counts
                    elif "counts" in user and isinstance(user["counts"], dict):
                        counts = user["counts"]
                        for src_field, dest_field in [
                            ("hearts", "heartCount"),
                            ("heart", "heartCount"),
                            ("digg", "diggCount"), 
                            ("likes", "heartCount")
                        ]:
                            if src_field in counts:
                                user[dest_field] = counts[src_field]
        
        return data
    except Exception as e:
        error_message = f"Error fetching trending creators: {str(e)}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)

@app.get("/download-video")
async def download_video(video_url: str):
    """Download a TikTok video without watermark"""
    try:
        print(f"\n==== DOWNLOADING VIDEO ====")
        print(f"Received video URL: {video_url}")
        
        # Handle invalid URL format
        if not isinstance(video_url, str) or video_url == '[object Object]':
            raise HTTPException(
                status_code=400, 
                detail="Invalid video URL format. Received: " + str(video_url)
            )
            
        # If URL is already a CDN URL, just return it directly
        if "tiktokcdn" in video_url:
            print("Direct CDN URL detected, returning it directly")
            return {"url": video_url, "source": "direct_cdn"}
            
        # Clean the URL if it has query parameters or extra data
        if "?" in video_url:
            video_url = video_url.split("?")[0]
            
        if not (video_url.startswith("http://") or video_url.startswith("https://")):
            if "tiktok.com" in video_url:
                video_url = "https://" + video_url
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid URL format: {video_url}"
                )
        
        # Handle TikTok shortlinks
        if "vm.tiktok.com" in video_url or "vt.tiktok.com" in video_url:
            print("Converting TikTok shortlink to full URL")
            try:
                # Follow the redirect to get the full URL
                redirect_session = requests.Session()
                redirect_response = redirect_session.head(video_url, allow_redirects=True, timeout=5)
                if redirect_response.url and "tiktok.com" in redirect_response.url:
                    video_url = redirect_response.url
                    print(f"Converted to: {video_url}")
            except requests.exceptions.Timeout:
                print("Timeout when following shortlink redirect")
            except Exception as e:
                print(f"Error following shortlink: {str(e)}")
        
        # Try direct extraction first (faster and more reliable)
        try:
            print("Attempting direct extraction...")
            # Get TikTok page content
            tiktok_response = requests.get(video_url, timeout=10)
            if tiktok_response.status_code == 200:
                # Look for video URL in page source
                video_content = tiktok_response.text
                # Try to extract the video URL with a basic regex pattern
                import re
                video_url_match = re.search(r'{"playAddr":"([^"]+)"', video_content) or \
                                re.search(r'playAddr":"([^"]+)"', video_content) or \
                                re.search(r'"playAddr":{"uri":"([^"]+)"', video_content) or \
                                re.search(r'"playAddr":"([^"]+)"', video_content) or \
                                re.search(r'<video[^>]*src=["\']([^"\']+)["\']', video_content)
                
                if video_url_match:
                    direct_url = video_url_match.group(1).replace('\\u002F', '/').replace('\\/', '/')
                    print(f"Direct extraction successful: {direct_url[:50]}...")
                    return {"url": direct_url, "source": "direct_extraction"}
        except requests.exceptions.Timeout:
            print("Direct extraction timed out")
        except Exception as e:
            print(f"Direct extraction failed: {str(e)}")
        
        # Try using the scraptik API with timeout
        print("Trying ScrapTik API...")
        
        # Use the API key from the request to properly authenticate
        api_key = RAPID_API_KEY
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="API key is not configured"
            )
        
        url = f"{BASE_URL}/video-without-watermark"
        params = {"url": video_url}
        api_headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "scraptik.p.rapidapi.com"
        }
        
        try:
            response = requests.get(url, headers=api_headers, params=params, timeout=15)
            
            if response.status_code != 200:
                error_detail = f"Error from ScrapTik API: {response.text[:200]}"
                print(f"API Error: {error_detail}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_detail
                )
                
            result = response.json()
            print(f"ScrapTik response keys: {list(result.keys())}")
            
            # Check different possible response structures
            if "play_url" in result:
                return {"url": result["play_url"], "source": "scraptik"}
            elif "url" in result:
                return {"url": result["url"], "source": "scraptik"}
            elif "data" in result and isinstance(result["data"], dict):
                data = result["data"]
                if "play_url" in data:
                    return {"url": data["play_url"], "source": "scraptik_data"}
                elif "url" in data:
                    return {"url": data["url"], "source": "scraptik_data"}
            
            # No valid URL found in response
            raise HTTPException(
                status_code=404,
                detail="No video URL found in the API response"
            )
        except requests.exceptions.Timeout:
            raise HTTPException(
                status_code=504,
                detail="ScrapTik API request timed out"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error with ScrapTik API: {str(e)}"
            )
                
    except HTTPException:
        raise
    except Exception as e:
        error_message = f"Error downloading video: {str(e)}"
        print(error_message)
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_message)

@app.post("/search-posts")
async def search_posts(request: PostSearchRequest):
    """Search for TikTok posts based on keyword and filters"""
    try:
        print(f"\n\n==== POST SEARCH REQUEST ====")
        print(f"Keyword: {request.keyword}")
        print(f"Count: {request.count}")
        print(f"Offset: {request.offset}")
        print(f"Use Filters: {request.use_filters}")
        print(f"Publish Time: {request.publish_time}")
        print(f"Sort Type: {request.sort_type}")
        
        url = f"{BASE_URL}/search-posts"
        params = {
            "keyword": request.keyword,
            "count": request.count,
            "offset": request.offset,
            "use_filters": request.use_filters,
            "publish_time": request.publish_time,
            "sort_type": request.sort_type
        }
        
        print(f"\n==== MAKING API REQUEST ====")
        print(f"URL: {url}")
        print(f"Params: {params}")
        print(f"Headers: X-RapidAPI-Key: {'*' * 5 + RAPID_API_KEY[-5:] if RAPID_API_KEY else 'Not set'}")
        
        response = requests.get(url, headers=headers, params=params)
        
        print(f"\n==== API RESPONSE ====")
        print(f"Status Code: {response.status_code}")
        print(f"Response Text Preview: {response.text[:200]}...")
        
        if response.status_code != 200:
            error_detail = f"Error from ScrapTik API: {response.text}"
            print(f"API Error: {error_detail}")
            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )
        
        data = response.json()
        
        # Process the response if needed
        print(f"\n==== PARSED RESPONSE ====")
        print(f"Response Type: {type(data)}")
        print(f"API Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dictionary'}")
        
        # Create a result container for posts
        processed_posts = []
        
        # Check for posts list in the response
        if "aweme_list" in data and isinstance(data["aweme_list"], list) and len(data["aweme_list"]) > 0:
            posts = data["aweme_list"]
            print(f"Found {len(posts)} posts in aweme_list")
            processed_posts = posts
            
        # If aweme_list is empty, check for search_item_list
        elif "search_item_list" in data and isinstance(data["search_item_list"], list) and len(data["search_item_list"]) > 0:
            search_items = data["search_item_list"]
            print(f"Found {len(search_items)} posts in search_item_list")
            
            # Extract aweme_info from each search item
            for item in search_items:
                if "aweme_info" in item and isinstance(item["aweme_info"], dict):
                    processed_posts.append(item["aweme_info"])
        
        print(f"Processed {len(processed_posts)} total posts")
        
        # Enrich post data if needed
        for post in processed_posts:
            # Add profile pics for authors if available
            if "author" in post and "avatar_thumb" in post["author"]:
                avatar_url = post["author"]["avatar_thumb"].get("url_list", [])
                if avatar_url and len(avatar_url) > 0:
                    post["author"]["avatar_base64"] = get_image_as_base64(avatar_url[0])
        
        # Return our processed data
        result = {
            "aweme_list": processed_posts,
            "has_more": data.get("has_more", 0),
            "cursor": data.get("cursor", 0)
        }
        return result
    except HTTPException:
        raise
    except Exception as e:
        error_message = f"Error searching posts: {str(e)}"
        print(f"ERROR in search_posts: {error_message}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_message)

# Add a new endpoint for deep content analysis
@app.post("/analyze-content")
async def analyze_content(request: ContentAnalysisRequest):
    """Perform deeper content analysis on a specific user"""
    try:
        print(f"\n\n==== CONTENT ANALYSIS REQUEST ====")
        print(f"User ID: {request.user_id}")
        print(f"Query: {request.query}")
        
        # First try getting user details by ID
        try:
            url = f"{BASE_URL}/get-user-info"
            params = {"user_id": request.user_id}
            
            user_response = requests.get(url, headers=headers, params=params)
            if user_response.status_code == 200:
                user_data = user_response.json()
            else:
                # Fallback to user-posts to get basic info
                print(f"Failed to get user details, falling back to user posts data")
                user_data = {
                    "uid": request.user_id,
                    "id": request.user_id
                }
        except Exception as e:
            print(f"Error getting user info: {str(e)}")
            user_data = {
                "uid": request.user_id,
                "id": request.user_id
            }
            
        # Then get user posts to analyze thumbnails and get more user data
        posts_url = f"{BASE_URL}/user-posts"
        posts_params = {
            "user_id": request.user_id,
            "count": 3,  # Get a few posts for thumbnail analysis
            "max_cursor": "0"
        }
        
        posts_response = requests.get(posts_url, headers=headers, params=posts_params)
        if posts_response.status_code == 200:
            posts_data = posts_response.json()
            
            # Extract author info from posts if it exists
            if "aweme_list" in posts_data and isinstance(posts_data["aweme_list"], list) and len(posts_data["aweme_list"]) > 0:
                # Add post data to user for thumbnail analysis
                user_data["aweme_list"] = posts_data["aweme_list"]
                
                # Get author data if not available from user-info
                if "author" in posts_data["aweme_list"][0]:
                    author = posts_data["aweme_list"][0]["author"]
                    for key, value in author.items():
                        if key not in user_data:
                            user_data[key] = value
        
        # Perform deep analysis
        try:
            analysis_result = analyze_user_content(user_data, request.query)
            
            return {
                "user_id": request.user_id,
                "query": request.query,
                "analysis": analysis_result,
                "status": "success"
            }
        except Exception as analysis_error:
            # If analysis fails, return error details
            error_msg = str(analysis_error)
            if "insufficient_quota" in error_msg or "rate limit" in error_msg.lower():
                return {
                    "user_id": request.user_id,
                    "query": request.query,
                    "analysis": AnalysisResult(
                        relevant=True,
                        score=0.5,
                        explanation="OpenAI API quota exceeded. Using basic keyword matching instead.",
                        image_analysis="OpenAI API quota exceeded",
                        thumbnail_analysis="OpenAI API quota exceeded"
                    ),
                    "status": "limited",
                    "error": "OpenAI API quota exceeded. Please check your OpenAI API billing."
                }
            else:
                return {
                    "user_id": request.user_id,
                    "query": request.query,
                    "analysis": AnalysisResult(
                        relevant=True,
                        score=0.5,
                        explanation="Error during analysis. Using basic keyword matching instead.",
                        image_analysis="Analysis error",
                        thumbnail_analysis="Analysis error"
                    ),
                    "status": "error",
                    "error": error_msg
                }
        
    except HTTPException:
        raise
    except Exception as e:
        error_message = f"Error analyzing content: {str(e)}"
        print(f"ERROR in analyze_content: {error_message}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        print(traceback.format_exc())
        
        # Return a user-friendly error response
        return {
            "user_id": request.user_id,
            "query": request.query,
            "analysis": AnalysisResult(
                relevant=True,
                score=0.5,
                explanation="Error occurred during analysis. Using basic matching instead.",
                image_analysis="Analysis error",
                thumbnail_analysis="Analysis error"
            ),
            "status": "error",
            "error": error_message
        }

# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
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
    allow_origins=["https://tiktok-analyzer-2.vercel.app", "*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure OpenAI client
openai.api_key = OPENAI_API_KEY

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

class AnalysisResult(BaseModel):
    relevant: bool
    score: float
    explanation: str

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
        
        # Profile picture analysis if available
        profile_pic_analysis = ""
        if user.get("avatarMedium"):
            profile_pic_base64 = get_image_as_base64(user.get("avatarMedium"))
            if profile_pic_base64:
                profile_pic_analysis = analyze_profile_picture(profile_pic_base64, query)
        
        # Content relevance analysis prompt
        prompt = f"""
        Analyze this TikTok user's profile in relation to the search query: "{query}"
        
        User data:
        {json.dumps(user_data, indent=2)}
        
        Profile picture analysis: {profile_pic_analysis}
        
        Is this user relevant to the search query? Consider:
        1. Does the username or display name suggest relevance?
        2. Does the bio contain relevant keywords or topics?
        3. Based on the profile picture analysis, does the visual content seem relevant?
        
        Provide a relevance score from 0.0 to 1.0 and explanation.
        
        Output format:
        {{
          "relevant": true/false,
          "score": 0.0-1.0,
          "explanation": "Your explanation here"
        }}
        """
        
        response = openai.chat.completions.create(
            model="gpt-4",
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
            explanation=result.get("explanation", "No explanation provided")
        )
    except Exception as e:
        print(f"Error analyzing user content: {e}")
        return AnalysisResult(
            relevant=False,
            score=0.0,
            explanation=f"Analysis error: {str(e)}"
        )

def analyze_profile_picture(base64_image, query):
    """Analyze the profile picture using OpenAI Vision API"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Does this image appear to be related to '{query}'? Provide a brief analysis."},
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
        print(f"Error analyzing profile picture: {e}")
        return "Could not analyze profile picture."

def does_user_match_criteria(user_data, criteria):
    """Check if a user matches the given filtering criteria"""
    if not user_data:
        return False
    
    follower_count = user_data.get("followerCount", 0)
    following_count = user_data.get("followingCount", 0)
    likes_count = user_data.get("heartCount", 0)
    verified = user_data.get("verified", False)
    
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

@app.post("/search-users", response_model=List[TikTokUser])
async def search_users(request: SearchRequest, background_tasks: BackgroundTasks):
    """Search for TikTok users based on query and filter criteria"""
    try:
        url = f"{BASE_URL}/search-users"
        params = {
            "keyword": request.query,
            "count": request.count,
            "cursor": "0"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error from ScrapTik API: {response.text}"
            )
        
        data = response.json()
        users_data = data.get("user_list", [])
        
        # Filter users based on criteria and prepare response
        filtered_users = []
        for user_item in users_data:
            user = user_item.get("user_info", {})
            
            if does_user_match_criteria(user, request.criteria):
                # Get profile picture as base64
                profile_pic_base64 = None
                if user.get("avatarMedium"):
                    profile_pic_base64 = get_image_as_base64(user.get("avatarMedium"))
                
                # Basic user information
                tiktok_user = TikTokUser(
                    id=user.get("uid", ""),
                    username=user.get("uniqueId", ""),
                    display_name=user.get("nickname", ""),
                    bio=user.get("signature", ""),
                    follower_count=user.get("followerCount", 0),
                    following_count=user.get("followingCount", 0),
                    likes_count=user.get("heartCount", 0),
                    verified=user.get("verified", False),
                    profile_pic=profile_pic_base64 or ""
                )
                
                # Analyze user in the background
                # For immediate response, we'll return without analysis first
                filtered_users.append(tiktok_user)
                
                # Add analysis task to background
                background_tasks.add_task(
                    analyze_user_and_update,
                    user,
                    request.query,
                    len(filtered_users) - 1,
                    filtered_users
                )
        
        return filtered_users
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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

@app.get("/user-posts/{user_id}")
async def get_user_posts(user_id: str, count: int = 10):
    """Get posts from a specific TikTok user"""
    try:
        url = f"{BASE_URL}/user-posts"
        params = {
            "user_id": user_id,
            "count": count,
            "max_cursor": "0"
        }
        
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

# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
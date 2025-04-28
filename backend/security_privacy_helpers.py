"""
Helper functions for identifying and scoring security/privacy focused TikTok influencers
"""

from typing import Dict, Any, List

def is_security_privacy_focused(user: Dict[str, Any]) -> bool:
    """
    Determine if a user is genuinely focused on security or privacy topics
    based on bio, username, display name, and video content.
    """
    # Security/privacy keywords and phrases (expanded list)
    security_terms = [
        "security", "privacy", "cybersecurity", "hacker", "hacking", "infosec", 
        "cyber", "encryption", "vpn", "data protection", "opsec", "osint",
        "penetration test", "pentest", "secure", "protection", "firewall", 
        "malware", "phishing", "breach", "exploit", "vulnerability", "ciso", 
        "security expert", "security professional", "privacy advocate", "digital privacy", 
        "identity theft", "online safety", "digital security", "threat", "cybercrime",
        "cyberthreats", "encryption", "secure messaging", "2fa", "mfa", "authentication",
        "security awareness", "security tips", "privacy tips", "data breach", "information security",
        "personal data", "surveillance", "cyber attack", "digital footprint", "anonymity"
    ]
    
    # Security/privacy professionals and roles
    professional_terms = [
        "security researcher", "privacy researcher", "cybersecurity expert", "ethical hacker",
        "security analyst", "privacy advocate", "infosec", "security engineer", "ciso", 
        "security professional", "cybersecurity professional", "penetration tester", 
        "privacy lawyer", "cybersecurity consultant", "security specialist", "digital forensics",
        "security consultant", "security advisor", "privacy consultant", "security auditor",
        "red team", "blue team", "security architect", "information security", "it security"
    ]
    
    # Get user attributes
    username = user.get("username", "") or user.get("unique_id", "")
    display_name = user.get("display_name", "") or user.get("nickname", "")
    bio = user.get("bio", "") or user.get("signature", "")
    videos = user.get("videos", [])
    follower_count = int(user.get("follower_count", 0)) 
    
    # MINIMUM FOLLOWER COUNT CHECK: Real influencers have followers
    # For generic username matches, require more followers
    if "privacy" in username.lower() or "security" in username.lower():
        # Generic name requires significant followers to be considered legitimate
        if follower_count < 5000:
            return False
    elif follower_count < 1000:
        # Even non-generic names should have some followers
        return False
        
    # Check display name for security/privacy focus (strong indicator)
    if display_name:
        display_name_lower = display_name.lower()
        for term in ["security", "cyber", "hacker", "privacy", "infosec", "encryption", "malware", "digital safety"]:
            if term in display_name_lower:
                # Display name is a strong indicator when combined with followers
                if follower_count > 10000:
                    return True
    
    # Check bio thoroughly - this is the most important indicator
    if bio:
        bio_lower = bio.lower()
        
        # Check for professional security/privacy roles
        for term in professional_terms:
            if term in bio_lower:
                return True
                
        # Check for multiple security terms (more reliable than just one)
        security_term_count = sum(1 for term in security_terms if term in bio_lower)
        if security_term_count >= 2:  # If bio contains at least 2 security terms
            return True
            
        # Check for specific credentials like CISSP, CEH, etc.
        credentials = ["cissp", "ceh", "security+", "sec+", "cisa", "oscp", "ccsp"]
        for credential in credentials:
            if credential in bio_lower:
                return True
    
    # Check recent video content if available
    if videos and len(videos) >= 3:  # At least 3 videos available
        security_video_count = 0
        for video in videos[:8]:  # Check first 8 videos
            title = video.get("title", "")
            if title:
                video_lower = title.lower()
                # Count videos with security/privacy topics
                for term in security_terms:
                    if term in video_lower:
                        security_video_count += 1
                        break
        
        # If at least 50% of recent videos are about security/privacy
        if security_video_count >= min(4, len(videos) / 2):
            return True
    
    # If it's just a username match with no other indicators and low followers,
    # it's likely not a real security/privacy influencer
    return False

def security_privacy_relevance_score(user: Dict[str, Any]) -> float:
    """
    Calculate a detailed relevance score for security/privacy focused influencers
    """
    score = 0.0
    
    # Extract user attributes safely
    username = user.get("username", "") or user.get("unique_id", "")
    display_name = user.get("display_name", "") or user.get("nickname", "")
    bio = user.get("bio", "") or user.get("signature", "")
    videos = user.get("videos", [])
    follower_count = int(user.get("follower_count", 0))
    
    # Security/privacy keywords (shorter list for scoring)
    security_terms = [
        "security", "privacy", "cybersecurity", "hacker", "infosec", "cyber", 
        "encryption", "vpn", "data protection", "malware", "phishing", 
        "exploit", "vulnerability", "threat", "secure", "authentication", 
        "information security", "digital privacy", "identity protection"
    ]
    
    # FOLLOWER SCORE - Strong influencers have more followers
    # This is crucial for distinguishing real influencers from name-only matches
    follower_score = 0.0
    if follower_count > 500000:
        follower_score = 0.5  # Major influencer
    elif follower_count > 100000:
        follower_score = 0.4  # Significant influencer
    elif follower_count > 50000:
        follower_score = 0.3  # Medium influencer
    elif follower_count > 10000:
        follower_score = 0.2  # Growing influencer
    elif follower_count > 5000:
        follower_score = 0.1  # Small influencer
    elif follower_count > 1000:
        follower_score = 0.05  # Micro influencer
    
    # Add follower score to overall score
    score += follower_score
    
    # CONTENT RELEVANCE SCORE
    # Check display name for security focus (strong indicator)
    if display_name:
        for term in security_terms:
            if term in display_name.lower():
                score += 0.2
                break
    
    # Check bio (weighted heavily)
    if bio:
        bio_lower = bio.lower()
        bio_terms_found = 0
        
        for term in security_terms:
            if term in bio_lower:
                bio_terms_found += 1
        
        # Calculate score based on number of terms found
        if bio_terms_found > 0:
            score += min(0.4, bio_terms_found * 0.1)  # Up to 0.4 for bio
    
    # Check video content
    if videos:
        security_videos = 0
        for i, video in enumerate(videos[:5]):  # First 5 videos
            title = video.get("title", "")
            if not title:
                continue
                
            video_lower = title.lower()
            for term in security_terms:
                if term in video_lower:
                    # More recent videos have higher weight
                    security_videos += 1 - (i * 0.1)  # 1.0, 0.9, 0.8, etc.
                    break
        
        score += min(0.3, security_videos * 0.1)  # Up to 0.3 for videos
    
    # USERNAME MATCH - Add points for username match, but less than content/followers
    # This prevents accounts with just "privacy" in username from ranking high
    if username:
        username_lower = username.lower()
        if "cyber" in username_lower or "infosec" in username_lower or "malware" in username_lower:
            # More technical/specific username terms get higher scores
            score += 0.15
        elif "security" in username_lower or "privacy" in username_lower:
            # Generic terms get lower scores
            score += 0.1
    
    # Hard Penalties:
    
    # Penalty for accounts that only have the search term in username but no other indicators
    if "privacy" in username.lower() or "security" in username.lower():
        if not bio and follower_count < 5000:
            score -= 0.5  # Significant penalty for empty bio + just name match
    
    # Cap score between 0 and 1.0
    return max(0, min(score, 1.0))

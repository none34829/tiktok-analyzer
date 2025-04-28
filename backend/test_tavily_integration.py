import requests
import json
import time

def test_full_integration():
    """Test the complete Tavily + ScrapTik + GPT-4 integration pipeline"""
    url = "http://127.0.0.1:8000/web-enhanced-search"
    
    # Test different queries to verify full integration
    queries = [
        {
            "name": "Fashion Influencer",
            "query": "fashion influencer from New York",
            "max_results": 3,
            "min_relevance_score": 0.5
        },
        {
            "name": "Tech Reviewer",
            "query": "tech gadget reviewer with over 1M followers",
            "max_results": 3,
            "min_relevance_score": 0.5
        },
        {
            "name": "Specific Profile",
            "query": "charlidamelio",  # Known large TikTok account
            "max_results": 1,
            "min_relevance_score": 0.1
        }
    ]
    
    results_summary = []
    
    for test_case in queries:
        print(f"\n{'='*80}")
        print(f"🧪 TEST CASE: {test_case['name']}")
        print(f"🔍 Query: {test_case['query']}")
        print(f"{'='*80}\n")
        
        try:
            # Make the request
            start_time = time.time()
            response = requests.post(url, json=test_case)
            duration = time.time() - start_time
            
            # Check response
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS: Search completed in {duration:.2f} seconds\n")
                
                # Summarize high-level results
                print(f"🔎 Search Strategy: {data.get('search_strategy')}")
                print(f"🏷️ Required Criteria: {', '.join(data.get('required_criteria', []))}")
                print(f"👤 Usernames Found: {data.get('usernames_found')}")
                print(f"🔄 Profiles Analyzed: {data.get('profiles_analyzed')}")
                
                # Check integration components
                tavily_success = "Tavily" in data.get('search_strategy', '')
                scraptik_success = any(match.get('follower_count', 0) > 0 for match in data.get('matches', []))
                gpt_success = any(match.get('why_matches', '') != '' for match in data.get('matches', []))
                
                # Print integration status
                print(f"\n🔌 INTEGRATION STATUS:")
                print(f"  Tavily Search: {'✅ SUCCESS' if tavily_success else '❌ FAILURE'}")
                print(f"  ScrapTik API: {'✅ SUCCESS' if scraptik_success else '❌ FAILURE'}")
                print(f"  GPT Analysis: {'✅ SUCCESS' if gpt_success else '❌ FAILURE'}")
                
                # Print information about matches
                matches = data.get('matches', [])
                print(f"\n📊 Found {len(matches)} matches:")
                
                for i, match in enumerate(matches):
                    print(f"\nMatch #{i+1}: @{match.get('username')}")
                    
                    # Verify profile data
                    has_display_name = match.get('display_name', '') != match.get('username')
                    has_bio = match.get('bio', '') != "Profile information not available"
                    has_followers = match.get('follower_count', 0) > 0
                    has_profile_pic = match.get('profile_pic', '') != ''
                    
                    # Calculate profile completeness
                    completeness = sum([has_display_name, has_bio, has_followers, has_profile_pic]) / 4 * 100
                    
                    print(f"  👤 Display Name: {match.get('display_name')}")
                    print(f"  📝 Bio: {match.get('bio')[:80]}..." if len(match.get('bio', '')) > 80 else f"  📝 Bio: {match.get('bio')}")
                    print(f"  👥 Followers: {match.get('follower_count'):,}")
                    print(f"  🖼️ Has Profile Pic: {'Yes' if has_profile_pic else 'No'}")
                    print(f"  📊 Profile Data Completeness: {completeness:.0f}%")
                    print(f"  📊 Relevance Score: {match.get('relevance_score'):.2f}")
                    print(f"  💬 Why Relevant: {match.get('why_matches')[:80]}..." if len(match.get('why_matches', '')) > 80 else f"  💬 Why Relevant: {match.get('why_matches')}")
                    
                    # Check if videos are included
                    videos = match.get('videos', [])
                    if videos:
                        print(f"  🎥 Videos: {len(videos)} included")
                        for j, video in enumerate(videos[:2]):
                            print(f"    - Video {j+1}: {video.get('desc', '')[:50]}..." if len(video.get('desc', '')) > 50 else f"    - Video {j+1}: {video.get('desc', '')}")
                
                # Add to results summary
                results_summary.append({
                    "test_case": test_case['name'],
                    "query": test_case['query'],
                    "usernames_found": data.get('usernames_found', 0),
                    "matches": len(data.get('matches', [])),
                    "tavily_success": tavily_success,
                    "scraptik_success": scraptik_success,
                    "gpt_success": gpt_success,
                    "duration": duration
                })
                
            else:
                print(f"\n❌ ERROR: HTTP {response.status_code}")
                print(response.text)
                results_summary.append({
                    "test_case": test_case['name'],
                    "error": f"HTTP {response.status_code}"
                })
        except Exception as e:
            print(f"\n❌ EXCEPTION: {str(e)}")
            results_summary.append({
                "test_case": test_case['name'],
                "error": str(e)
            })
    
    # Print overall summary
    print(f"\n{'='*80}")
    print(f"📊 OVERALL INTEGRATION TEST SUMMARY")
    print(f"{'='*80}")
    
    for result in results_summary:
        status = "✅ SUCCESS" if result.get('error') is None else f"❌ FAILURE: {result.get('error')}"
        
        if result.get('error') is None:
            integration_score = sum([result['tavily_success'], result['scraptik_success'], result['gpt_success']]) / 3 * 100
            print(f"🧪 {result['test_case']}: {status} - {result['matches']} matches in {result['duration']:.1f}s - Integration: {integration_score:.0f}%")
        else:
            print(f"🧪 {result['test_case']}: {status}")

if __name__ == "__main__":
    test_full_integration()

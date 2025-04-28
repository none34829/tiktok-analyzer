import requests
import json

# Test the web-enhanced search endpoint with Tavily integration
def test_web_enhanced_search():
    url = "http://127.0.0.1:8000/web-enhanced-search"
    
    # Sample query
    payload = {
        "query": "fashion influencer from Sri Lanka",
        "max_results": 3,
        "min_relevance_score": 0.5
    }
    
    # Make the request
    print(f"Sending request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            print("\n--- Tavily Search Successful ---")
            print(f"Query: {data.get('query')}")
            print(f"Search Strategy: {data.get('search_strategy')}")
            print(f"Required Criteria: {data.get('required_criteria')}")
            print(f"Usernames Found: {data.get('usernames_found')}")
            print(f"Profiles Analyzed: {data.get('profiles_analyzed')}")
            print("\nMatches:")
            
            # Print information about each match
            for i, match in enumerate(data.get('matches', [])):
                print(f"\nMatch #{i+1}:")
                print(f"Username: @{match.get('username')}")
                print(f"Display Name: {match.get('display_name')}")
                print(f"Relevance Score: {match.get('relevance_score')}")
                print(f"Discovery Method: {match.get('discovery_method')}")
                print(f"Why Matches: {match.get('why_matches')[:100]}...")  # Truncate for readability
            
            # Check if Tavily was actually used
            if "Tavily" in data.get('search_strategy', ''):
                print("\n✅ Tavily API was successfully used in the search process")
            else:
                print("\n❌ Tavily API might not have been used - check the search_strategy")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Exception occurred: {str(e)}")

if __name__ == "__main__":
    test_web_enhanced_search()

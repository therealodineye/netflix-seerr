import requests
import urllib.parse
from config import SEERR_URL, SEERR_API_KEY, SEERR_EMAIL, SEERR_PASSWORD

HEADERS = {
    "X-Api-Key": SEERR_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

_CACHED_COOKIE = None

def get_auth_cookie():
    """
    Authenticates with Overseerr using local auth (email/password) to get a session cookie.
    This bypasses the API Key's admin auto-approval behavior.
    """
    global _CACHED_COOKIE
    if _CACHED_COOKIE is not None:
        return _CACHED_COOKIE

    url = f"{SEERR_URL.rstrip('/')}/api/v1/auth/local"
    payload = {
        "email": SEERR_EMAIL,
        "password": SEERR_PASSWORD
    }
    
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    
    # Extract the connect.sid cookie from the response headers
    if "set-cookie" in response.headers:
        # requests automatically handles cookies in response.cookies, but we can manually extract
        cookie_header = response.headers["set-cookie"]
        _CACHED_COOKIE = cookie_header.split(';')[0]
    elif "connect.sid" in response.cookies:
        _CACHED_COOKIE = f"connect.sid={response.cookies['connect.sid']}"
    else:
        raise ValueError("Failed to retrieve session cookie from Overseerr authentication.")
        
    return _CACHED_COOKIE

def search_media(query, media_type="movie"):
    """
    Search for a movie or TV show by title.
    Returns a dictionary with the tmdbId and a skip flag if already requested/available,
    or None if no matching media is found.
    """
    query_encoded = urllib.parse.quote(query)
    url = f"{SEERR_URL.rstrip('/')}/api/v1/search?query={query_encoded}"
    
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    data = response.json()
    results = data.get("results", [])
    
    for result in results:
        # Check if the result matches the requested media type
        if result.get("mediaType") == media_type:
            tmdb_id = result.get("id")
            skip = False
            
            # Check the mediaInfo object to see if we should skip requesting it
            media_info = result.get("mediaInfo")
            if media_info:
                status = media_info.get("status")
                # 2: PENDING, 3: PROCESSING, 4: PARTIALLY_AVAILABLE, 5: AVAILABLE
                if status in [2, 3, 4, 5]:
                    skip = True
                    return {"tmdbId": tmdb_id, "skip": skip}
                    
            # If not skipped by basic status, check for declined requests
            # Search endpoint doesn't return requests list, so we query the media directly
            media_url = f"{SEERR_URL.rstrip('/')}/api/v1/{media_type}/{tmdb_id}"
            media_response = requests.get(media_url, headers=HEADERS)
            if media_response.status_code == 200:
                detailed_media_info = media_response.json().get("mediaInfo", {})
                if detailed_media_info:
                    requests_list = detailed_media_info.get("requests", [])
                    for req in requests_list:
                        # 3: DECLINED
                        if req.get("status") == 3:
                            skip = True
                            break
                            
            return {"tmdbId": tmdb_id, "skip": skip}
            
    return None

def get_latest_season(tmdb_id):
    """
    Fetch TV show details to find the highest valid season number.
    Excludes season 0 / specials.
    """
    url = f"{SEERR_URL.rstrip('/')}/api/v1/tv/{tmdb_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    data = response.json()
    seasons = data.get("seasons", [])
    
    latest_season = 0
    for season in seasons:
        season_number = season.get("seasonNumber", 0)
        # We only want valid seasons (exclude 0/specials) and keep track of the max
        if season_number > 0 and season_number > latest_season:
            latest_season = season_number
            
    return latest_season

def request_media(tmdb_id, media_type):
    """
    Request a movie or TV show using the Overseerr API.
    For TV shows, it dynamically fetches and requests only the latest season.
    Uses the authenticated user's session cookie to avoid admin auto-approval.
    """
    url = f"{SEERR_URL.rstrip('/')}/api/v1/request"
    
    # Get the session cookie using local auth
    cookie = get_auth_cookie()
    
    # Use ONLY the cookie (and basic content headers) to act exactly as the user
    # Do NOT send the X-Api-Key header, as Overseerr prioritizes the API key over the cookie
    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Cookie": cookie
    }
    
    payload = {
        "mediaId": tmdb_id,
        "mediaType": media_type
    }
    
    if media_type == "tv":
        latest_season = get_latest_season(tmdb_id)
        if latest_season > 0:
            payload["seasons"] = [latest_season]
            
    response = requests.post(url, headers=request_headers, json=payload)
    response.raise_for_status()
    
    return response.json()

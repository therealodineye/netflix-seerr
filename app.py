import os
import sys
import requests
import urllib.parse
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Ensure we can load helper modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import scraper
import seerr

# Load active environment configuration
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path, override=True)

app = Flask(__name__)

# Make sure templates folder exists or Flask knows where it is
app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

def get_env_vars():
    """
    Reads active configuration values directly from the .env file if it exists,
    or falls back to active environment variables.
    """
    if os.path.exists(env_path):
        from dotenv import dotenv_values
        config = dotenv_values(env_path)
        return {
            "SEERR_URL": config.get("SEERR_URL") or "",
            "SEERR_API_KEY": config.get("SEERR_API_KEY") or "",
            "SEERR_EMAIL": config.get("SEERR_EMAIL") or "",
            "SEERR_PASSWORD": config.get("SEERR_PASSWORD") or ""
        }
    return {
        "SEERR_URL": os.getenv("SEERR_URL") or "",
        "SEERR_API_KEY": os.getenv("SEERR_API_KEY") or "",
        "SEERR_EMAIL": os.getenv("SEERR_EMAIL") or "",
        "SEERR_PASSWORD": os.getenv("SEERR_PASSWORD") or ""
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/favicon.ico")
def favicon():
    return app.send_static_file("favicon.ico")

@app.route("/api/countries", methods=["GET"])
def get_countries():
    return jsonify({
        "countries": scraper.COUNTRIES,
        "globalLists": scraper.GLOBAL_LISTS
    })

@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify(get_env_vars())

@app.route("/api/config", methods=["POST"])
def save_config():
    data = request.json or {}
    url = data.get("SEERR_URL", "").strip()
    api_key = data.get("SEERR_API_KEY", "").strip()
    email = data.get("SEERR_EMAIL", "").strip()
    password = data.get("SEERR_PASSWORD", "").strip()

    try:
        # Save to local .env
        with open(env_path, "w") as f:
            f.write(f"SEERR_URL={url}\n")
            f.write(f"SEERR_API_KEY={api_key}\n")
            f.write(f"SEERR_EMAIL={email}\n")
            f.write(f"SEERR_PASSWORD={password}\n")

        # Reload environment variables in Python context immediately
        load_dotenv(env_path, override=True)
        # Clear the Overseerr auth session cookie
        seerr.clear_cached_cookie()
        
        return jsonify({"success": True, "message": "Configuration successfully saved and reloaded."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/fetch", methods=["POST"])
def fetch_netflix_list():
    data = request.json or {}
    selection = data.get("selection", "Norway").strip()
    fetch_movies = data.get("movies", True)
    fetch_shows = data.get("shows", True)

    # Soft check: If config is missing, return friendly notice
    config = get_env_vars()
    if not config["SEERR_URL"] or not config["SEERR_API_KEY"]:
        return jsonify({
            "error": "Overseerr is not configured. Please open Settings via the Gear Icon to configure SEERR_URL and SEERR_API_KEY."
        }), 400

    try:
        movies_scraped, shows_scraped = scraper.scrape_top_10(selection)
    except Exception as e:
        return jsonify({"error": f"Failed to scrape Netflix lists: {str(e)}"}), 500

    movies_results = []
    shows_results = []

    # Process movies
    if fetch_movies:
        for idx, title in enumerate(movies_scraped, 1):
            item = {
                "rank": idx,
                "title": title,
                "tmdbId": None,
                "posterUrl": None,
                "status": "Ready",
                "isRequestable": True
            }
            # Search in Seerr
            seerr_res = seerr.search_media(title, "movie")
            if seerr_res:
                item["tmdbId"] = seerr_res.get("tmdbId")
                raw_url = seerr_res.get("posterUrl")
                if raw_url:
                    item["posterUrl"] = f"/api/proxy-image?url={urllib.parse.quote(raw_url)}"
                item["status"] = seerr_res.get("status")
                item["isRequestable"] = not seerr_res.get("skip")
            movies_results.append(item)

    # Process TV shows
    if fetch_shows:
        for idx, title in enumerate(shows_scraped, 1):
            item = {
                "rank": idx,
                "title": title,
                "tmdbId": None,
                "posterUrl": None,
                "status": "Ready",
                "isRequestable": True
            }
            # Search in Seerr
            seerr_res = seerr.search_media(title, "tv")
            if seerr_res:
                item["tmdbId"] = seerr_res.get("tmdbId")
                raw_url = seerr_res.get("posterUrl")
                if raw_url:
                    item["posterUrl"] = f"/api/proxy-image?url={urllib.parse.quote(raw_url)}"
                item["status"] = seerr_res.get("status")
                item["isRequestable"] = not seerr_res.get("skip")
            shows_results.append(item)

    return jsonify({
        "selection": selection,
        "movies": movies_results,
        "shows": shows_results
    })

@app.route("/api/sync", methods=["POST"])
def sync_selected():
    data = request.json or {}
    items = data.get("requests", [])

    # Check configuration
    config = get_env_vars()
    if not config["SEERR_URL"] or not config["SEERR_EMAIL"] or not config["SEERR_PASSWORD"]:
        return jsonify({
            "error": "Local auth credentials missing. Please open Settings via the Gear Icon to configure SEERR_EMAIL and SEERR_PASSWORD."
        }), 400

    results = []
    success_count = 0
    fail_count = 0

    for item in items:
        tmdb_id = item.get("tmdbId")
        media_type = item.get("type") # "movie" or "tv"
        title = item.get("title", f"TMDB ID {tmdb_id}")

        if not tmdb_id:
            results.append({"title": title, "success": False, "error": "Missing TMDB ID"})
            fail_count += 1
            continue

        try:
            seerr.request_media(tmdb_id, media_type)
            results.append({"title": title, "success": True})
            success_count += 1
        except Exception as e:
            results.append({"title": title, "success": False, "error": str(e)})
            fail_count += 1

    return jsonify({
        "success": True,
        "successCount": success_count,
        "failCount": fail_count,
        "details": results
    })

@app.route("/api/proxy-image", methods=["GET"])
def proxy_image():
    target_url = request.args.get("url")
    if not target_url:
        return "Missing url parameter", 400

    config = get_env_vars()
    headers = {
        "X-Api-Key": config["SEERR_API_KEY"]
    }

    try:
        # 1. Attempt to stream the image from Seerr's proxy using backend auth
        img_res = requests.get(target_url, headers=headers, timeout=5, stream=True)
        img_res.raise_for_status()

        from flask import Response
        return Response(
            img_res.raw.read(),
            mimetype=img_res.headers.get("Content-Type", "image/jpeg")
        )
    except Exception as e:
        print(f"[IMAGE PROXY WARNING] Failed to fetch from Seerr ({e}). Falling back to TMDB CDN directly...")
        
        # 2. Self-healing fallback: extract the TMDB portion and fetch from TMDB directly
        import re
        tmdb_match = re.search(r'(https://image\.tmdb\.org/t/p/.*)$', target_url)
        if tmdb_match:
            tmdb_url = tmdb_match.group(1)
        else:
            # Fallback if URL doesn't match standard prefix
            tmdb_url = target_url
            
        try:
            fallback_res = requests.get(tmdb_url, timeout=5, stream=True)
            fallback_res.raise_for_status()
            
            from flask import Response
            return Response(
                fallback_res.raw.read(),
                mimetype=fallback_res.headers.get("Content-Type", "image/jpeg")
            )
        except Exception as fallback_err:
            print(f"[IMAGE PROXY ERROR] Fallback also failed: {fallback_err}")
            return "Failed to load image", 500


if __name__ == "__main__":
    # Start on local dev server
    app.run(host="127.0.0.1", port=5000, debug=True)

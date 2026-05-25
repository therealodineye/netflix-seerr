import requests
import re
from bs4 import BeautifulSoup

COUNTRIES = [
    "Argentina", "Australia", "Austria", "Bahamas", "Bahrain", "Bangladesh", "Belgium", "Bolivia", 
    "Brazil", "Bulgaria", "Canada", "Chile", "Colombia", "Costa Rica", "Croatia", "Cyprus", 
    "Czech Republic", "Denmark", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", 
    "Estonia", "Finland", "France", "Germany", "Greece", "Guadeloupe", "Guatemala", "Honduras", 
    "Hong Kong", "Hungary", "Iceland", "India", "Indonesia", "Ireland", "Israel", "Italy", 
    "Jamaica", "Japan", "Jordan", "Kenya", "Kuwait", "Latvia", "Lebanon", "Lithuania", 
    "Luxembourg", "Malaysia", "Maldives", "Malta", "Martinique", "Mauritius", "Mexico", 
    "Morocco", "New Caledonia", "New Zealand", "Nicaragua", "Nigeria", "Norway", "Oman", 
    "Pakistan", "Panama", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", 
    "Réunion", "Romania", "Saudi Arabia", "Serbia", "Singapore", "Slovakia", "Slovenia", 
    "South Africa", "South Korea", "Spain", "Sri Lanka", "Sweden", "Switzerland", "Taiwan", 
    "Thailand", "Trinidad and Tobago", "Türkiye", "Ukraine", "United Arab Emirates", 
    "United Kingdom", "United States", "Uruguay", "Venezuela", "Vietnam"
]

GLOBAL_LISTS = [
    "Global (Films English)",
    "Global (Films Non-English)",
    "Global (TV English)",
    "Global (TV Non-English)",
    "Global (Most Popular)"
]

GLOBAL_LISTS_MAP = {
    "Global (Films English)": {
        "movie": "https://www.netflix.com/tudum/top10",
        "tv": None
    },
    "Global (Films Non-English)": {
        "movie": "https://www.netflix.com/tudum/top10/films-non-english",
        "tv": None
    },
    "Global (TV English)": {
        "movie": None,
        "tv": "https://www.netflix.com/tudum/top10/tv"
    },
    "Global (TV Non-English)": {
        "movie": None,
        "tv": "https://www.netflix.com/tudum/top10/tv-non-english"
    },
    "Global (Most Popular)": {
        "movie": "https://www.netflix.com/tudum/top10/most-popular",
        "tv": "https://www.netflix.com/tudum/top10/most-popular/tv"
    }
}

def slugify_country(country_name):
    # Standard countries slugification
    name = country_name.strip().lower()
    # Replace special accented characters specifically listed in available countries
    name = name.replace("ü", "u")
    name = name.replace("é", "e")
    # Remove any character that is not lowercase letter, digit, space, or hyphen
    name = re.sub(r'[^a-z0-9\s-]', '', name)
    # Replace whitespace/hyphens with a single hyphen
    name = re.sub(r'[\s-]+', '-', name)
    return name

def get_titles(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    titles = []
    # Find all table data cells with the class "title"
    for td in soup.find_all('td', class_='title'):
        # Extract the title from the <button> element inside
        btn = td.find('button')
        if btn:
            titles.append(btn.text.strip())
            
        # We only want the top 10
        if len(titles) == 10:
            break
            
    return titles

def scrape_top_10(selection="Norway"):
    """
    Scrapes the top 10 movies and/or TV shows for the given country or global list.
    Returns a tuple of (movies, tv_shows).
    """
    if selection in GLOBAL_LISTS_MAP:
        urls = GLOBAL_LISTS_MAP[selection]
        movies = get_titles(urls["movie"]) if urls["movie"] else []
        tv_shows = get_titles(urls["tv"]) if urls["tv"] else []
    else:
        slug = slugify_country(selection)
        movies_url = f"https://www.netflix.com/tudum/top10/{slug}"
        tv_url = f"https://www.netflix.com/tudum/top10/{slug}/tv"
        
        movies = get_titles(movies_url)
        tv_shows = get_titles(tv_url)
        
    return movies, tv_shows

if __name__ == "__main__":
    import sys
    country = sys.argv[1] if len(sys.argv) > 1 else "Norway"
    print(f"Scraping Top 10 for: {country}")
    movies, tv_shows = scrape_top_10(country)
    
    print(f"--- Top 10 Movies ({len(movies)}) ---")
    for i, title in enumerate(movies, 1):
        print(f"{i}. {title}")
        
    print(f"\n--- Top 10 TV Shows ({len(tv_shows)}) ---")
    for i, title in enumerate(tv_shows, 1):
        print(f"{i}. {title}")

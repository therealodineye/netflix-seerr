import requests
from bs4 import BeautifulSoup

def get_titles(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
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

def scrape_top_10():
    """
    Scrapes the top 10 movies and TV shows from Netflix Tudum (Norway).
    Returns a tuple of (movies, tv_shows).
    """
    movies_url = "https://www.netflix.com/tudum/top10/norway"
    tv_url = "https://www.netflix.com/tudum/top10/norway/tv"
    
    movies = get_titles(movies_url)
    tv_shows = get_titles(tv_url)
    
    return movies, tv_shows

if __name__ == "__main__":
    movies, tv_shows = scrape_top_10()
    print("--- Top 10 Movies in Norway ---")
    for i, title in enumerate(movies, 1):
        print(f"{i}. {title}")
        
    print("\n--- Top 10 TV Shows in Norway ---")
    for i, title in enumerate(tv_shows, 1):
        print(f"{i}. {title}")

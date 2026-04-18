
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urlencode

tv_search_list = [
    "ahsoka s02e01",
    "fallout s03e01",
    "for all mankind s05e03",
    "foundation s04e01",
    "fubar s03e01",
    "house of the dragon s03e01",
    "mandalorian s04e01",
    "monarch legacy of monsters s02e07",
    "obi-wan kenobi s02e01",
    "orville s04e01",
    "prehistoric planet s04e01",
    "silo s03e01",
    "star wars visions s04e01",
    "strange new worlds s04e01",
    "shogun s02e01",
    "the last of us s03e01",
    "skeleton crew s02e01",
    "mobland s02e01",
    "ironheart s02e01",
    "wednesday s03e01",
    "ncis s24e01",
    "ncis sydney s04e01",
    "ncis origins s03e01",
    "ncis tony and ziva s02e01",
    "dmv s01e17",
    "percy jackson and the olympians s03e01",
    "starfleet academy s02e01",
    "wonderman s02e01",
    "dark winds s05e01",
    "star wars maul shadow lord s01e04",
    "star city s01e01",
    "spider-noir s01e01",
    "forged in fire s06",
]

movie_search_list = [
    "jumanji open world",
    "the mandalorian and grogu",
    "godzilla minus zero",
    "the dog stars",
    "avengers doomsday",
    "toy story 5",
    "top gun 3",
    "balls up",
    "normal",
    "the mummy",
    "heart of the beast",
]

total_tv = []
total_mov = []

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def normalize_title(title):
    title = title.lower()
    title = re.sub(r'[^a-z0-9\s]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def query_matches_title(query, title):
    normalized_query = normalize_title(query)
    normalized_title = normalize_title(title)
    query_tokens = normalized_query.split()
    title_tokens = set(normalized_title.split())
    return all(token in title_tokens for token in query_tokens)

def report_result_count(param1, driver, type):
    base_url = "http://10.0.4.58:3333/webui/torrents"
    query = urlencode({"query": param1, "content_type": type, "limit": "100"})
    url = f"{base_url}?{query}"
    print(f"Searching for: {param1}")
    try:
        driver.get(url)
        try:
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            WebDriverWait(driver, 30).until(
                lambda d: (
                    len(d.find_elements(By.CSS_SELECTOR, "span.title")) > 0
                    or len(d.find_elements(By.CSS_SELECTOR, "tr")) > 1
                    or "no torrents found" in d.page_source.lower()
                    or "no results" in d.page_source.lower()
                )
            )
        except TimeoutException:
            print("Warning: Timeout waiting for dynamic results; continuing with current page HTML")

        rendered_html = driver.page_source
        soup = BeautifulSoup(rendered_html, 'html.parser')
        rows = soup.find_all('tr')
        matched_titles = []
        title_nodes = soup.select("span.title")
        for idx, node in enumerate(title_nodes, start=1):
            raw_text = node.get_text(" ", strip=True)
            if not raw_text:
                print(f"Debug: span.title #{idx} is empty")
                continue
            if query_matches_title(param1, raw_text):
                matched_titles.append(raw_text)
        matched_titles = list(dict.fromkeys(matched_titles))
        torrent_count = len(rows) if rows else len(title_nodes)
        print(f"Title token matches for '{param1}': {len(matched_titles)}")
        if matched_titles:
            print(f"Found {len(matched_titles)} matching torrents\n\n")
        elif torrent_count > 0:
            print(f"Found {torrent_count} torrents, but no exact title matches\n\n")
        else:
            print("No torrents found\n\n")
        return len(matched_titles)
    except Exception as e:
        print(f"Error: {e}")
        return 0
        
def search_for_movs(driver):
    for search_term in movie_search_list:
        mov = report_result_count(search_term, driver, "movie")
        total_mov.append(mov)
        # Rate limit: wait between requests
        time.sleep(15)

def search_for_tv(driver):
    for search_term in tv_search_list:
        eps = report_result_count(search_term, driver, "tvshow")
        total_tv.append(eps)
        # Rate limit: wait between requests
        time.sleep(15)

if __name__ == "__main__":

    

    driver = init_driver()

    try:

        search_for_movs(driver)
        search_for_tv(driver)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Always close the driver
        driver.quit()
        
    print(f"Number of New Episodes: {sum(total_tv)}")
    print(f"Number of New Movies: {sum(total_mov)}")
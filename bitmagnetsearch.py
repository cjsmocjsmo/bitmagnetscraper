
import platform
import re
import time
from urllib.parse import urlencode
from bs4 import BeautifulSoup
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import TimeoutException
except ImportError:
    webdriver = None
    Options = None
    WebDriverWait = None
    By = None
    TimeoutException = None
import requests

tv_search_list = [
    "ahsoka s02e01",
    "dark winds s05e01",
    "dmv s01e21",
    "fallout s03e01",
    "for all mankind s05e09",
    "foundation s04e01",
    "fubar s03e01",
    "house of the dragon s03e01",
    "ironheart s02e01",
    "mandalorian s04e01",
    "mobland s02e01",
    "monarch legacy of monsters s02e11",
    "ncis origins s03e01",
    "ncis s24e01",
    "ncis sydney s04e01",
    "ncis tony and ziva s02e01",
    "obi-wan kenobi s02e01",
    "orville s04e01",
    "percy jackson and the olympians s03e01",
    "prehistoric planet s04e01",
    "shogun s02e01",
    "silo s03e01",
    "skeleton crew s02e01",
    "spider-noir s01e05",
    "star city s01e01",
    "star wars maul shadow lord s01e11",
    "star wars visions s04e01",
    "starfleet academy s02e01",
    "strange new worlds s04e01",
    "the last of us s03e01",
    "wednesday s03e01",
    "wonderman s02e01",
]

movie_search_list = [
    "avengers doomsday",
    "godzilla minus zero",
    "heart of the beast",
    "jumanji open world",
    "minions and monsters",
    "normal (2026)",
    "spider-man: brand new day",
    "star wars: the mandalorian and grogu",
    "supergirl (2026)",
    "the dog stars",
    "top gun 3 (2026)",
    "toy story 5 (2026)",
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
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            WebDriverWait(driver, 10).until(
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
        title_nodes = soup.select("span.title")
        matched_titles = []
        
        for idx, node in enumerate(title_nodes, start=1):
            raw_text = node.get_text(" ", strip=True)
            if not raw_text:
                print(f"Debug: span.title #{idx} is empty")
                continue
            if query_matches_title(param1, raw_text):
                matched_titles.append(raw_text)
        
        matched_titles = list(dict.fromkeys(matched_titles))
        print(f"Title token matches for '{param1}': {len(matched_titles)}")
        
        torrent_count = len(rows) if rows else len(title_nodes)
        
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

# ARMv7l scraping using requests and BeautifulSoup
def report_result_count_requests(param1, type):
    base_url = "http://10.0.4.58:3333/webui/torrents"
    query = urlencode({"query": param1, "content_type": type, "limit": "100"})
    url = f"{base_url}?{query}"
    print(f"[requests] Searching for: {param1}")
    try:
        resp = requests.get(url, timeout=15)
        print(resp.text)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        rows = soup.find_all('tr')
        print(rows)
        title_nodes = soup.select("span.title")
        matched_titles = []
        for idx, node in enumerate(title_nodes, start=1):
            raw_text = node.get_text(" ", strip=True)
            if not raw_text:
                print(f"Debug: span.title #{idx} is empty")
                continue
            print(param1)
            print(raw_text)
            if query_matches_title(param1, raw_text):
                matched_titles.append(raw_text)
        print(matched_titles)
        matched_titles = list(dict.fromkeys(matched_titles))
        print(f"Title token matches for '{param1}': {len(matched_titles)}")
        torrent_count = len(rows) if rows else len(title_nodes)
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
        

def search_for_movs_selenium(driver):
    for search_term in movie_search_list:
        mov = report_result_count(search_term, driver, "movie")
        total_mov.append(mov)
        time.sleep(15)

def search_for_tv_selenium(driver):
    for search_term in tv_search_list:
        eps = report_result_count(search_term, driver, "tvshow")
        total_tv.append(eps)
        time.sleep(15)

def search_for_movs_requests():
    for search_term in movie_search_list:
        mov = report_result_count_requests(search_term, "movie")
        total_mov.append(mov)
        time.sleep(5)

def search_for_tv_requests():
    for search_term in tv_search_list:
        eps = report_result_count_requests(search_term, "tvshow")
        total_tv.append(eps)
        time.sleep(5)

if __name__ == "__main__":
    arch = platform.machine().lower()
    sysplat = platform.system().lower()
    plat = platform.platform().lower()
    print(f"Detected architecture: {arch}, system: {sysplat}, platform: {plat}")
    if arch == "armv7l":
        print("Running in ARMv7l mode: using requests + BeautifulSoup")
        search_for_movs_requests()
        search_for_tv_requests()
    else:
        print("Running in standard mode: using Selenium")
        driver = init_driver()
        try:
            search_for_movs_selenium(driver)
            search_for_tv_selenium(driver)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            driver.quit()
    print(f"Number of New Episodes: {sum(total_tv)}")
    print(f"Number of New Movies: {sum(total_mov)}")
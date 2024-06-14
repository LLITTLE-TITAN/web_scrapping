import requests
import time
import random
from bs4 import BeautifulSoup
import json

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.4"
]

delay = 5

urls = []

def generate_urls():
    first_url = "https://www.zillow.com/kissimmee-fl/?searchQueryState=%7B%22isMapVisible%22%3Afalse%2C%22mapBounds%22%3A%7B%22west%22%3A-81.89622672558593%2C%22east%22%3A-81.00221427441406%2C%22south%22%3A27.733072175952117%2C%22north%22%3A28.72280783787644%7D%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A18847%2C%22regionType%22%3A6%7D%5D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22fc%22%3A%7B%22value%22%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%7D"
    for i in range(2, 22):
        url = f"https://www.zillow.com/kissimmee-fl/{i}_p/?searchQueryState=%7B%22pagination%22%3A%7B%22currentPage%22%3A{i}%7D%2C%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22west%22%3A-82.25259574414062%2C%22east%22%3A-80.64584525585937%2C%22south%22%3A27.733072175952113%2C%22north%22%3A28.722807837876445%7D%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A18847%2C%22regionType%22%3A6%7D%5D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22land%22%3A%7B%22value%22%3Afalse%7D%2C%22fc%22%3A%7B%22value%22%3Afalse%7D%7D%2C%22isListVisible%22%3Atrue%7D"
        urls.append(url)
    urls.append(first_url)
generate_urls()
#end getting all urls
def extract_detail_urls(obj, path=''):
    detail_urls = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'detailUrl':
                detail_urls.append(value)
            else:
                detail_urls.extend(extract_detail_urls(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            detail_urls.extend(extract_detail_urls(item, f"{path}[{i}]"))
    return detail_urls

def get_onepage_urls(url):
    response = None
    while response is None or response.status_code == 403:
        user_agent = random.choice(user_agents)
        headers = {"User-Agent": user_agent}
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
            print(f"Request blocked. Waiting for {delay} seconds before retrying.")
            time.sleep(delay)
    soup = BeautifulSoup(response.content, "html.parser")
    links = []
    for link in soup.find_all('a'):
        links.append(link.get('href'))
    current_urls = [item for item in links if item and item.startswith('https://www.zillow.com/homedetails')]
    next_element = soup.find("script", {"id": "__NEXT_DATA__"})
    next_url_data = json.loads(next_element.string)
    next_urls = extract_detail_urls(next_url_data)
    total_urls = current_urls + next_urls
    url_list = list(dict.fromkeys(total_urls))
    return url_list


home_urls = []

for item in urls:
    home_urls += get_onepage_urls(item)
    

with open("home_url_data.py", "w", encoding="utf-8") as file:
    # Write the HTML content to the file
    file.write(str(home_urls))

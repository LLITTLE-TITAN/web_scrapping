import requests
import time
import random
from bs4 import BeautifulSoup
import json
import os
import re
example_url = "https://www.zillow.com/homedetails/2838-Sweetspire-Cir-Kissimmee-FL-34746/82072676_zpid/"

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.4"
]

delay = 5

def extract_detail_urls(obj, path=''):
    detail_urls = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            # print(key)
            if key == "gdpClientCache":
                detail_urls.append(value)
            else:
                detail_urls.extend(extract_detail_urls(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            detail_urls.extend(extract_detail_urls(item, f"{path}[{i}]"))
    return detail_urls
def fix_string(input_str):
    fixed_str = re.sub(r'(\w+):\s*(\{.*?\})', r'"\1":\2', input_str)
    fixed_str = re.sub(r'(\w+):\s*(\[.*?\])', r'"\1":\2', fixed_str)
    return fixed_str
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
    
    MLS = soup.title.string
    mls_start = MLS.find("MLS #")
    mls_number = MLS[mls_start + 5:MLS.find(" |", mls_start)]
    
    component = soup.find_all('div', {'data-testid': 'bed-bath-sqft-fact-container'})
    beds = component[0].find_all('span')[0].text
    baths = component[1].find_all('span')[0].text
    sqft = component[2].find_all('span')[0].text
    
    component2 = soup.find_all('div', {'data-cy': 'chip-first-column-content'})
    price = component2[0].find('span', {"data-testid": "price"}).text.strip('$').replace(',', '')
    address = component2[0].find('h1').text.strip()
    
    component3 = soup.find('meta', {'name': 'description'}).get('content')
    built_in_index = component3.index("built in ")
    built_year = int(component3[built_in_index + len("built in "):built_in_index + len("built in ") + 4])
    data = [beds, baths, sqft, price, address, built_year]
    description = soup.find('article').find_all('div')[0].find('div').text
    
    component4 = soup.find_all('div', {'data-testid': 'category-group'})[1]
    lot_size = component4.find_all('div', {'data-testid': 'fact-category'})[2].find("li").text.split(": ")[1].strip()
    property_list = component4.find_all('div', {'data-testid': 'fact-category'})
    property = []
    for item in property_list:
        title = item.find('h6').text
        data_url = item.find_all('li')
        data = []
        for item in data_url:
            data.append(item.find('span').text)
        property.append({title : data})
        
    component5 = soup.find_all('div', {'data-testid': 'category-group'})[0]
    feature_list = component5.find_all('div', {'data-testid': 'fact-category'})
    facts_features = []
    for item in feature_list:
        title = item.find('h6').text
        data_url = item.find_all('li')
        data = []
        for item in data_url:
            data.append(item.find('span').text)
        facts_features.append({title : data})
        
    component6 = soup.find('ul', {'class': 'footer-breadcrumbs'})
    location_elements = component6.find_all('li')
    breadcrumb_navigation = []
    for element in location_elements:
        if element.find('a'):
            breadcrumb_navigation.append(element.find('a').text)
        else:
            breadcrumb_navigation.append(element.find('strong').text)
            
    component7 = soup.find("script", {"id": "__NEXT_DATA__"})
    agent_data = component7.string.replace("\\", "")
    phone_number_pattern = r'\b\d{3}-\d{3}-\d{4}\b'
    phone_numbers = list(dict.fromkeys(re.findall(phone_number_pattern, agent_data)))
    listing_agents_start = agent_data.find('"listingAgents":[')
    listing_agents_end = agent_data.find(']', listing_agents_start) + 1
    listing_offices_start = agent_data.find('"listingOffices":[')
    listing_offices_end = agent_data.find(']', listing_offices_start) + 1
    listing_agents = agent_data[listing_agents_start:listing_agents_end]
    listing_offices = agent_data[listing_offices_start:listing_offices_end]
    agent_name_pattern = r'"memberFullName":"([^"]+)"'
    agent_name = re.search(agent_name_pattern, listing_agents).group(1)
    broker_name_pattern = r'"officeName":"([^"]+)"'
    broker_name = re.search(broker_name_pattern, listing_offices).group(1)
    provied_information = {agent_name : phone_numbers[0] , broker_name : phone_numbers[1] }
    result = {
        "MLS" : mls_number,
        "Listing Price" : price,
        "Address" : address,
        "Bedrooms" : beds,
        "Bathrooms" : baths,
        "Sqft" : sqft,
        "Year Built" : built_year,
        "Lot Size" : lot_size,
        "Description" : description,
        "Provide Information" : provied_information,
        "All Facts & Features" : facts_features,
        "All Property information" : property,
        "Breadcrumb" : breadcrumb_navigation,
    }

    component8 = soup.find("script", {"id": "__NEXT_DATA__"})
    img_data = component8.string.replace("\\", "")
    pattern = r'https://photos.zillowstatic.com/fp/\w+-cc_ft_768.jpg'
    image_urls = re.findall(pattern, img_data)
    for url in image_urls:
        save_directory = f"upload/{address}"
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
        filename = url.split("/")[-1]
        save_path = os.path.join(save_directory, filename)
        response = requests.get(url)
        with open(save_path, "wb") as file:
            file.write(response.content)

    
    return result

data = get_onepage_urls(example_url)

# with open("data.json", "w", encoding="utf-8") as file:
#     # Write the HTML content to the file
#     file.write(str(get_onepage_urls(example_url)))
    

with open("data.json", "w") as f:
    json.dump(data, f, indent=4)
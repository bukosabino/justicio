import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import os

# AJ: The scraper is storing the data in a JSON locally. Integration with current project architecture needs to be made
session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
session.headers.update(headers)
def create_url(date):
    base_url = "https://sede.asturias.es/bopa-sumario?p_p_id=pa_sede_bopa_web_portlet_SedeBopaSummaryWeb&p_p_lifecycle=0&p_r_p_summaryDate="
    return f"{base_url}{date.strftime('%d/%m/%Y')}"
def follow_disposition_link(initial_url):
    # AJ: Follows the second link where the html with the full content is
    try:
        response = session.get(initial_url, verify=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            link = soup.find('a', title="Texto de la disposición")
            if link and link.has_attr('href'):
                return link['href']
    except Exception as e:
        print(f"Error when trying to access the second link: {e}")
    return None

def BOPA_scrape_html(url):
    # AJ: scrapes the html and store data with metadata tags in a JSON file
    data = {'url_html': url}
    try:
        date_match = re.search(r'p_r_p_dispositionDate=(\d{2}%2F\d{2}%2F\d{4})', url)
        if date_match:
            disposition_date = date_match.group(1).replace('%2F', '/')
            data['disposition_date'] = disposition_date

        reference_match = re.search(r'p_r_p_dispositionText=([0-9-]+)', url)
        if reference_match:
            reference_number = reference_match.group(1)
            data['reference_number'] = reference_number
            
        response = session.get(url, verify=False)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            h4 = soup.find('h4')
            if h4:
                data['section_name'] = h4.text.strip()
            h5 = soup.find('h5')
            if h5:
                data['department_name'] = h5.text.strip()
            data['content'] = []
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                data['content'].append(p.text.strip())
    except Exception as e:
        data['error'] = f"Error when making the request: {e}"
    return data

def main():
    start_date = datetime(2024, 3, 5)
    end_date = datetime.now()
    delta = timedelta(days=1)
    all_data = []
    while start_date <= end_date:
        initial_url = create_url(start_date)
        disposition_url = follow_disposition_link(initial_url)
        if disposition_url:
            scraped_data = BOPA_scrape_html(disposition_url)
            all_data.append(scraped_data)
        start_date += delta
    # AJ: The code below must be changed. only for test purposes. Stores the data in local.
    desktop_path = os.path.join(os.path.expanduser(
        "~"), "Desktop", "BOPAData_Scaper")
    os.makedirs(desktop_path, exist_ok=True)
    with open(os.path.join(desktop_path, 'output.json'), 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
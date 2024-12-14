import requests
import json
from bs4 import BeautifulSoup
import time
import logging

class AncestryObituaryScraper:
    def __init__(self, base_url, headers):
        """
        Initialize the scraper with base URL and headers
        
        :param base_url: Base URL for Ancestry.com obituary search
        :param headers: Headers to use for the request
        """
        self.base_url = base_url
        self.headers = headers
        self.session = requests.Session()
        #self.session.headers.update(headers)
        
        # Configure logging
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def scrape_page(self, page_num):
        """
        Scrape a single page of obituary results
        
        :param page_num: Page number to scrape
        :return: List of obituary dictionaries
        """
        # Construct URL with page number
        url = f"{self.base_url}pg={page_num}&e--Obituary=2023&e--Obituary_x=1-0-0"
        print(f"url is {url}")
        # params = {
        #     'pg': f'{page_num}',
        #     'e--Obituary': '2023',
        #     'e--Obituary_x': '1-0-0'
        # }
        
        # Retry mechanism
        print("IN function attempting to scrape")
        for attempt in range(3):
            try:
                # Send GET request
                response = self.session.get(url, headers=self.headers)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find table rows
                rows = soup.select('table.collection-results-table tbody tr')
                
                # Extract data
                page_results = []
                for row in rows:
                    try:
                        data = {}

                        # Loop through each <td> in the row and map the "data-label" to its content
                        for cell in row.find_all('td'):
                            label = cell.get('data-label')  # Extract the data-label attribute
                            if label:
                                # Extract content, handling <br> tags for "Relatives"
                                content = cell.get_text(separator=',', strip=True)
                                data[label] = content
                            # Parse relatives into a list
                            relatives = data.get('Relatives', '')
                            relatives_list = [relative.strip() for relative in relatives.split(',') if relative.strip()]
                        print(data.get("Name"))


                        page_results.append({
                            "Name": data.get("Name"),
                            "Birth Date": data.get("Birth Date"),
                            "Death Date": data.get("Death Date"),
                            "Publication Place": data.get("Publication Place"),
                            "Relatives": relatives_list,
                        })
                        #print(page_results)
                    except Exception as row_error:
                        self.logger.warning(f"Error parsing row: {row_error}")
                
                self.logger.info(f"Successfully scraped page {page_num}")
                with open("temporary_obit1.json", 'a', encoding='utf-8') as f:
                    json.dump(page_results, f, indent=2, ensure_ascii=False)
                return page_results
            
            except requests.RequestException as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"Failed to scrape page {page_num} after 3 attempts")
                    return []

    def scrape_all_pages(self, max_pages=1000):
        """
        Scrape multiple pages of obituary results
        
        :param max_pages: Maximum number of pages to scrape
        :return: List of all obituary dictionaries
        """
        all_results = []
        
        for page in range(2, max_pages + 1):
            page_results = self.scrape_page(page)
            
            # Stop if no results found
            if not page_results:
                break
            
            all_results.extend(page_results)
            
            # Optional: Add delay between page requests to avoid overwhelming the server
            time.sleep(1)
        
        return all_results

    def save_to_json(self, data, filename='ancestry_obituaries2.json'):
        """
        Save scraped data to a JSON file
        
        :param data: List of obituary dictionaries
        :param filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Data saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to JSON: {e}")

def main():
    # Headers from the provided document
    headers = {
        'authority': 'www.ancestry.com',
        'method': 'GET',
        'path': '/search/collections/7545/?pg=12&e--Obituary=2023&e--Obituary_x=1-0-0',
        'scheme': 'https',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'cookie': 'SOURCES=DID=3&DDD=12%2f12%2f2024+10%3a36%3a51; OPTOUTMULTI=c3:0%7Cc7:0%7Cc12:0%7Cc11:0%7Cc2:0%7Cc8:0%7Cc10:0%7Cc6:0%7Cc9:0%7Ci:8140; TI.SI=0; TI=0; ANCUUID=101c52b2-9d6e-4584-b6cf-2de725abc1d9; ANCSESSIONID=882c58c1-ff2e-42a0-8933-0b66e33ecb29; _gcl_au=1.1.1418618086.1734025016; at_check=true; an_split=54; an_s_split=74; VARS=LCISONAME=enUS&LCID=1033&COUNTRYCODE=US&NOTIFIEDOFCOOKIES=2dcd349f_27369; AMCVS_ED3301AC512D2A290A490D4C%40AdobeOrg=1; s_ecid=MCMID%7C84694747853769952310526338751830387192; AMCV_ED3301AC512D2A290A490D4C%40AdobeOrg=1585540135%7CMCIDTS%7C20070%7CMCMID%7C84694747853769952310526338751830387192%7CMCAAMLH-1734629826%7C9%7CMCAAMB-1734629826%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1734032229s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C4.4.0; qsBucket=6.7; surveyid=CSAT-1006; _ga=GA1.1.130765843.1734025032; _rlu=4c8c4d35-4d91-4ff5-97b0-4f5ee16854e1; _rlgm=GwXogq0|y|1E3sxHPP|VvWNwxxy9:y|; _rlsnk=4c8c_m4llqjh1; _rllt=1734025039383; _tt_enable_cookie=1; _ttp=FK7dO342qyn5WX8owcBoQY7lksj.tt.1; _pin_unauth=dWlkPVlUSmlabVZrT1dVdE5EQTFaQzAwWldFNExUaGhZbVl0WWpVeE1HSmpOR1JpTWpndw; _fbp=fb.1.1734025046262.451590497499484115; LAU=09e82641-0006-0000-0000-000000000000; VARSESSION=S=A5tvSgrugkCr1cRu5CQWkw&SLI=0&ITT=0&NoDoubleBillStateFound=1; _csrf=L4NEczGSzWHaNimo2iS1Udet; USERID=09e82641-0006-0000-0000-000000000000; BAIT=BT%3D%3Bcr%3D%3BCOL_ONSITE%3D%22%22%3Bhasgs%3D0%3BCSub%3D0%3Bct%3D%22%22%3BCTrial%3D0%3Brt%3Dd1-7%3BDnaDSAC%3D0%3BDnaDSP%3D0%3BDnaGF%3D0%3BDnaPilot%3D0%3Bduration%3D%3BESub%3D0%3BETrial%3D0%3Bhadgs%3D0%3BFreeDnaUp%3D0%3BGEN_ONSITE%3D%22%22%3Bbuygs%3D0%3Bht%3D0%3BId%3D09e82641-0006-0000-0000-000000000000%3BINF_ONSITE%3D%22%22%3Bdne%3D%22%22%3BLanguage%3DEnglish%3BLSubPrice%3D0%3BLSubDuration%3D%3BLSubCurrency%3D%3BLSub%3D%3BLoggedIn%3D1%3BNBP_ONSITE%3D%22%22%3BNewDna%3D0%3BOldDna%3D0%3Bownership%3Dnosubscriptions%3BRegType%3D0%3Btn%3D0%3B; ETRIAL=0; CTRIAL=0; CSUB=0; ORDERSUMMARYROUTESTATUS=true; OMNITURE=TYPE=Trialer; qs90=yes; _hjSessionUser_1584090=eyJpZCI6ImY3MTQ3YThmLWJiNWUtNWJkNy1iMjE2LTc5MGQ1MWVjZWI4YiIsImNyZWF0ZWQiOjE3MzQwMjYwMjE3OTksImV4aXN0aW5nIjpmYWxzZX0=; ATT=Mjd3sFbR4qAQrpNR9IU6zG*CvPAOBhMABZC6JY; RMEATT=Mjd3sFbR4qAQrpNR9IU6zG*CvPAOBhMABZC6JY; ANCATT=Mjd3sFbR4qAQrpNR9IU6zG*CvPAOBhMABZC6JY; _cfuvid=yJsk162aUWpT3XWrARcriMFCCpFocwuOjahv8rDgx.s-1734076658853-0.0.1.1-604800000; SecureATT=eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6IjEifQ.eyJzdWIiOiIwOWU4MjY0MS0wMDA2LTAwMDAtMDAwMC0wMDAwMDAwMDAwMDAiLCJleHAiOjE3MzQwODI2MjIsImlzcyI6InVkcy1pbXMiLCJzaWQiOiJlOGU4MDk2OC1mZDhlLTQ2YTYtOGM1My1lNDNiZmUyMjEzYzEiLCJhdWQiOiJBbmNlc3RyeSIsImlhdCI6MTczNDA4MDgyMiwiYWlhdCI6MTczNDAyNTQwMSwianRpIjoiMGVjMTI4YzAtMWU3Ny00YzAzLWI1MDQtODJlZTJhMzU4OGVhIiwiZmdzIjo4LCJncmMiOjM2MH0.KVJObA10eCCUSPB2UpszUSeG70Ku6moiQoW5e4DRzrGbFELhXcFgFwmCrDYI58Ftde-T4F5CNSi6CbvU5p8lVg; __cf_bm=FoNZSFew8iuBfE58OJnHRtRL1O.fNdb5WFDf_jjnS1k-1734080822-1.0.1.1-5xQKvuN0PX0CkMUjwQNf0Dzm4QKIqkPITZrq6dx50oLOdW2VJ_d7YF8N2zwdf9ZGWb.polpxT7WqzWlSMI7pyA; cf_clearance=w0RpxlhlCoDu7FzUbRbUrT1LTep9PbM8HoQOlhtENDk-1734080831-1.2.1.1-gIXwovnYxRy5OObkuo28BwqLTVi29rZL6hzuNX_TkJJMU6FG1kEyW5kWii4jOHIuYRgu4K1QH9CcJiAby1BhLKs3rHQZs.xfoZz7pyaFLxMDhOHSWZtPzBiAO.nJjw1TuxQJQBCvDltvLdOimbjbYEK7LRkInQy4BzpPIWzC2K1DtaTs50X5k_6TppytBRmOcFmSzHgzXJ4WVfmbFZSv656B09iKXl3ZqlmgEpRdltI.fHKjXhRMTt8kJjwXJttOHFQ89KZOaqy0Bta5WcCQaC0Hntzwf61UsH.UEZ5f9Ps.51YLYd5hctbPQE0qz7HARydZHwJhuC1OagKR8W4iYqjk4HMwfB5sPVSO1krVVnhMBYwERLxgE2a84PBEFBqfjva37YOX.Rep9nFWLjYZgaV5yY7E3hHiE81462nI_z8; mbox=PC#bf38cd4a57b9466ca17714730b5f12d0.35_0#1797321897|session#1be04514d69f4e9db04148c480f0e5da#1734082693; gtm_pageview_count=23; _ga_4QT8FMEX30=GS1.1.882c58c1-ff2e-42a0-8933-0b66e33ecb29.3.1.1734080844.40.0.0; _uetsid=bbeb28d0b8af11ef8605e561cb5be70a; _uetvid=bbeb7740b8af11ef8f83f9df2d5ad7d3; _ga_LMK6K2LSJH=GS1.1.882c58c1-ff2e-42a0-8933-0b66e33ecb29.3.1.1734080860.0.0.0',
        'dnt': '1',
        'priority': 'u=0, i',
        'referer': 'https://www.ancestry.com/account/create?returnUrl=https%3A%2F%2Fwww.ancestry.com%2Fsearch%2Fcollections%2F7545%2F%3Fe--Obituary%3D2023%26e--Obituary_x%3D1-0-0&e--Obituary_x=1-0-0',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36'
    }

    # Base URL for Ancestry.com obituary search
    base_url = 'https://www.ancestry.com/search/collections/7545/?'

    # Create scraper instance
    print("Starting scraper")
    scraper = AncestryObituaryScraper(base_url, headers)

    # Scrape and save data
    obituaries = scraper.scrape_all_pages()
    scraper.save_to_json(obituaries)

if __name__ == '__main__':
    main()
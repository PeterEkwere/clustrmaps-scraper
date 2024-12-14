import requests
import json
import time
from datetime import datetime

def scrape_obituaries(fh_id=16293, page_count=20):
    # Base URL for the API endpoint
    base_url = "https://www.socalfuneral.com/obituaries/obit_json"
    
    # Headers to mimic the browser request
    headers = {
        "authority": "www.socalfuneral.com",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "dnt": "1",
        "referer": "https://www.socalfuneral.com/obits",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A_Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
    
    # List to store all obituaries
    all_obituaries = []
    
    # Current page number
    current_page = 1
    
    while True:
        # Prepare the parameters for the request
        params = {
            "fh_id": fh_id,
            "page_count": page_count,
            "page_number": current_page,
            "search_field": "",
            "sort_by": "deathDate",
            "sort_direction": "desc",
            "_": int(datetime.now().timestamp() * 1000)
        }
        
        print(f"Fetching page {current_page}...")
        
        try:
            # Send GET request
            response = requests.get(base_url, headers=headers, params=params)
            #print(f"response is {response.text}, {response.json()}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            print(f"data is {data}")
            
            # Check if we have reached the last page
            if not data: #or 'data' not in data or len(data['data']) == 0:
                print("No more pages to fetch.")
                break
            
            # Process and filter each obituary
            page_obituaries = []
            for person in data:
                filtered_obit = {
                    "first_name": person.get('first_name', ''),
                    "middle_name": person.get('middle_name', ''),
                    "last_name": person.get('last_name', ''),
                    "birth_date": person.get('birth_date', ''),
                    "death_date": person.get('death_date', ''),
                    "obit_text": person.get('obit_text', '')
                }
                page_obituaries.append(filtered_obit)
            
            # Add page obituaries to all obituaries
            all_obituaries.extend(page_obituaries)
            
            print(f"Fetched {len(page_obituaries)} obituaries from page {current_page}")
            
            # Check total record count to determine if we should continue
            #total_records = data.get('record_count', 0)
            #print(f"Total records: {total_records}")
            
            # Increment page number
            current_page += 1
            
            # Optional: Add a small delay to avoid overwhelming the server
            time.sleep(1)
            
            # Break if we've fetched all records
            if current_page == 3:
                print("Fetched all available records.")
                break
        
        except requests.RequestException as e:
            print(f"Error fetching page {current_page}: {e}")
            break
    
    # Save the obituaries to a JSON file
    output_file = 'obituaries.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_obituaries, f, indent=4, ensure_ascii=False)
    
    print(f"\nTotal obituaries saved: {len(all_obituaries)}")
    print(f"Saved to {output_file}")
    
    return all_obituaries

# Run the scraper
if __name__ == "__main__":
    obituaries = scrape_obituaries()
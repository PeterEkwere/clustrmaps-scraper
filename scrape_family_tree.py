import requests
from urllib.parse import quote
import cloudscraper
from twocaptcha import TwoCaptcha
from urllib.parse import quote

def solve_captcha(url, sitekey):
    solver = TwoCaptcha('0fc18e610fd8c46403982e5f422aa130')
    try:
        result = solver.turnstile(sitekey=sitekey, url=url)
        return result['code']
    except Exception as e:
        print(f"Captcha solving error: {e}")
        return None

def search_family_tree(first_name, last_name, city_state_zip):
    # Use cloudscraper to handle Cloudflare protection
    scraper = cloudscraper.create_scraper()
    
    # Captcha parameters
    captcha_url = 'https://www.familytreenow.com/internalcaptcha/captchasubmit'
    sitekey = '0x4AAAAAAAnLepxurEtn5y1M'
    
    # Solve Turnstile captcha
    captcha_response = solve_captcha(captcha_url, sitekey)
    print(f"Captcha response is {captcha_response}")
    if not captcha_response:
        print("Captcha solving failed")
        return None
    
    # Prepare headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'cf-turnstile-response': captcha_response  # Add Turnstile response to headers
    }
    
    # Encode search parameters
    first_name_encoded = quote(first_name)
    last_name_encoded = quote(last_name)
    city_state_zip_encoded = quote(city_state_zip)
    
    # Construct search URL
    search_url = (f'https://www.familytreenow.com/search/genealogy/results'
                  f'?first={first_name_encoded}'
                  f'&last={last_name_encoded}'
                  f'&citystatezip={city_state_zip_encoded}')
    
    try:
        # Make the request using scraper
        response = scraper.get(search_url, headers=headers)
        
        if response.status_code == 200:
            print("Successfully accessed the URL!")
            return response.text
        else:
            print(f"Failed to access URL. Status code: {response.status_code}")
            print(f"Response content: {response.text}")
            return None
    
    except Exception as e:
        print(f"Request error: {e}")
        return None

# Usage
results = search_family_tree("James", "Abiusi", "Utica,NY")
if results:
    with open('search_result.html', 'w', encoding='utf-8') as f:
        f.write(results)
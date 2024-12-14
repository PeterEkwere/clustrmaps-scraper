import requests
import re
import json
import cloudscraper
from twocaptcha import TwoCaptcha
from urllib.parse import quote
from bs4 import BeautifulSoup
import difflib
import time
import random

def normalize_name(name):
    """
    Normalize name for comparison by removing extra whitespaces, 
    converting to lowercase, and handling middle initials.
    """
    # Remove extra whitespaces and convert to lowercase
    name = ' '.join(name.split()).lower()
    
    # Remove middle initial if present
    name_parts = name.split()
    if len(name_parts) > 2:
        # Keep first and last name, remove middle initial
        name = f"{name_parts[0]} {name_parts[-1]}"
    
    return name

def compare_names(name1, name2):
    """
    Advanced name comparison using difflib for similarity
    """
    # Normalize names first
    norm_name1 = normalize_name(name1)
    norm_name2 = normalize_name(name2)
    
    # Use SequenceMatcher to get a similarity ratio
    similarity = difflib.SequenceMatcher(None, norm_name1, norm_name2).ratio()
    
    # If names are very similar (above 0.8 threshold)
    return similarity > 0.8

def compare_birthdates(date1, date2):
    """
    Compare birthdates with some flexibility
    
    :param date1: First date in format MM/DD/YYYY or DD/MM/YYYY or YYYY
    :param date2: Second date for comparison
    :return: Boolean indicating if dates match
    """
    if not date1 or not date2:
        return False
    
    # Remove any leading zeros and split
    def clean_date(date_str):
        # Split by / and remove leading zeros
        parts = [part.lstrip('0') for part in date_str.split('/')]
        return parts
    
    try:
        # First try exact match
        if date1 == date2:
            return True
        
        # If dates have different formats
        clean1 = clean_date(date1)
        clean2 = clean_date(date2)
        
        # Check if years match
        if clean1[-1] == clean2[-1]:
            return True
        
        # Check partial matches (for cases with incomplete info)
        if len(clean1) > 1 and len(clean2) > 1:
            # Check if month and year match
            if clean1[-1] == clean2[-1] and clean1[0] == clean2[0]:
                return True
        
        return False
    
    except Exception:
        return False

def compare_relatives(relatives1, relatives2):
    """
    Compare lists of relatives
    :param relatives1: List of first set of relatives
    :param relatives2: List of second set of relatives
    :return: Boolean indicating if there's at least one matching relative
    """
    # Normalize relatives lists
    norm_relatives1 = set(normalize_name(rel) for rel in relatives1)
    norm_relatives2 = set(normalize_name(rel) for rel in relatives2)
    
    # Check for any overlap
    return len(norm_relatives1.intersection(norm_relatives2)) > 0

def solve_captcha(url, sitekey):
    """
    Solve Turnstile captcha using 2captcha
    
    :param url: URL where captcha is located
    :param sitekey: Captcha sitekey
    :return: Captcha solution or None
    """
    solver = TwoCaptcha('0fc18e610fd8c46403982e5f422aa130')
    try:
        result = solver.turnstile(sitekey=sitekey, url=url)
        return result['code']
    except Exception as e:
        print(f"Captcha solving error: {e}")
        return None

def extract_person_details(html_content):
    """
    Extract details of people from search results HTML
    
    :param html_content: HTML content of search results
    :return: List of person dictionaries
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all person rows
    person_rows = soup.find_all('div', class_='row')
    print(f"Found {len(person_rows)} person rows")
    
    persons = []
    for row in person_rows:
        try:
            # Extract name
            name_elem = row.find_all('strong')
            if not name_elem:
                continue
            
            # Get full name
            full_name = ' '.join(elem.get_text(strip=True) for elem in name_elem)
            print(f"Found name: {full_name}")
            
            # Extract detail link
            detail_link = row.find('a', class_='btn-success detail-link')
            if not detail_link:
                continue
            
            # Extract birthdate
            birth_elem = row.find('td', text=re.compile(r'Born:'))
            birthdate = birth_elem.find_next('td').get_text(strip=True) if birth_elem else ''
            
            # Extract relatives
            relatives_elem = row.find('td', text=re.compile(r'Related:'))
            relatives = relatives_elem.find_next('td').get_text(strip=True).split(',') if relatives_elem else []
            
            # Store details
            persons.append({
                'name': full_name,
                'detail_link': detail_link.get('href'),
                'birthdate': birthdate,
                'relatives': [r.strip() for r in relatives]
            })
        except Exception as e:
            print(f"Error extracting person details: {e}")
    
    return persons

def find_matching_person(deceased_info, search_results):
    """
    Find matching person based on advanced comparison
    
    :param deceased_info: Dictionary with deceased person's details
    :param search_results: HTML content of search results
    :return: Matching person's detail link or None
    """
    # Extract persons from search results
    persons = extract_person_details(search_results)
    print(f"Found {len(persons)} potential matches")
    
    # Prepare deceased info
    deceased_name = ' '.join(deceased_info.get('name_parts', []))
    deceased_birthdate = deceased_info.get('birthdate', '')
    deceased_relatives = deceased_info.get('relatives', [])
    
    # Compare each person
    for person in persons:
        # Name comparison
        name_match = compare_names(deceased_name, person['name'])
        
        # Birthdate comparison
        birthdate_match = compare_birthdates(deceased_birthdate, person['birthdate'])
        
        # Relatives comparison (optional)
        relatives_match = compare_relatives(deceased_relatives, person['relatives'])
        
        # If at least 2 out of 3 criteria match
        match_criteria = sum([name_match, birthdate_match, relatives_match])
        if match_criteria >= 2:
            print(f"Matched person: {person['name']}")
            return person['detail_link']
    
    return None

def search_family_tree(deceased_info, max_retries=3):
    """
    Search family tree with deceased person's info and retry mechanism
    
    :param deceased_info: Dictionary containing deceased person details
    :param max_retries: Maximum number of retry attempts
    :return: Detailed page HTML or None
    """
    # Use cloudscraper to handle Cloudflare protection
    scraper = cloudscraper.create_scraper()
    
    # Captcha parameters
    captcha_url = 'https://www.familytreenow.com/internalcaptcha/captchasubmit'
    sitekey = '0x4AAAAAAAnLepxurEtn5y1M'
    
    # Extract search parameters
    first_name = deceased_info['name_parts'][0]
    last_name = deceased_info['name_parts'][-1]
    city = "Utica, NY"
    
    # Encode search parameters
    first_name_encoded = quote(first_name)
    last_name_encoded = quote(last_name)
    city_state_zip_encoded = quote(city)
    
    # Construct search URL
    search_url = (f'https://www.familytreenow.com/search/genealogy/results'
                  f'?first={first_name_encoded}'
                  f'&last={last_name_encoded}'
                  f'&citystatezip={city_state_zip_encoded}')
    
    # Retry loop
    for attempt in range(max_retries):
        try:
            # Prepare headers with random user agent to reduce detection
            headers = {
                'User-Agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 110)}.0.{random.randint(1000, 9999)}.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Make the request
            response = scraper.get(search_url, headers=headers)
            
            # Check for bad responses that might need captcha
            if response.status_code in [403, 500, 502, 503, 429]:
                print(f"Attempt {attempt + 1}: Received status code {response.status_code}")
                
                # Solve captcha only for specific error codes
                captcha_response = solve_captcha(captcha_url, sitekey)
                if captcha_response:
                    # Update headers with captcha response
                    headers['cf-turnstile-response'] = captcha_response
                    
                    # Retry with captcha
                    response = scraper.get(search_url, headers=headers)
                else:
                    print("Captcha solving failed")
                    continue
            
            # Check if request was successful
            if response.status_code == 200:
                print("Successfully accessed the search results URL!")
                
                # Save search results
                with open(f'search_results_attempt_{attempt + 1}.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                # Find matching person's detail link
                matching_detail_link = find_matching_person(deceased_info, response.text)
                
                if matching_detail_link:
                    # Construct full URL
                    base_url = 'https://www.familytreenow.com'
                    full_url = base_url + matching_detail_link
                    
                    # Get user details page
                    details_response = scraper.get(full_url, headers=headers)
                    
                    if details_response.status_code == 200:
                        # Save user details
                        with open(f'users_details_attempt_{attempt + 1}.html', 'w', encoding='utf-8') as f:
                            f.write(details_response.text)
                        
                        return details_response.text
                    else:
                        print(f"Failed to access user details. Status code: {details_response.status_code}")
                else:
                    print("No matching person found.")
                
                return None
            
            # Add a small delay between retries to avoid rate limiting
            time.sleep(random.uniform(1, 3))
        
        except Exception as e:
            print(f"Request error on attempt {attempt + 1}: {e}")
            time.sleep(random.uniform(1, 3))
    
    print("Max retries reached. Unable to complete the search.")
    return None

# Example usage
def main():
    # Load deceased info from JSON file
    with open('cleaned_deceased_names.json', 'r') as f:
        deceased_data = json.load(f)
    
    # Search for each deceased person
    for person in deceased_data:
        print(f"Searching for: {person['deceased_name']}")
        search_family_tree(person)
        break  # Process only the first person in this example

if __name__ == "__main__":
    main()
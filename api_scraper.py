import requests
from bs4 import BeautifulSoup
import os
import json
import re
import random
import os
from typing import Dict, List, Any, Optional

def load_processed_data(output_file: str) -> Dict[str, Any]:
    """
    Load previously processed data or create an empty dictionary.
    
    Args:
        output_file (str): Path to the output JSON file
    
    Returns:
        Dict[str, Any]: Existing processed data or an empty dictionary
    """
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            return json.load(f)
    return {}

def save_processed_data(output_file: str, processed_data: Dict[str, Any]) -> None:
    """
    Save processed data to a JSON file.
    
    Args:
        output_file (str): Path to the output JSON file
        processed_data (Dict[str, Any]): Data to be saved
    """
    #os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(processed_data, f, indent=2)

def process_clustrmaps_result(result: Dict[str, Any], deceased_name: str) -> Dict[str, Any]:
    """
    Process the ClusterMaps search result into a structured format.
    
    Args:
        result (Dict[str, Any]): Raw ClusterMaps search result
        deceased_name (str): Name of the deceased person
    
    Returns:
        Dict[str, Any]: Processed person data
    """
    processed_data = {
        'deceased': deceased_name,
        'full_name': result.get('name', 'N/A'),
        'age': result.get('age', 'Age not available'),
        'location': f"{result.get('city', 'city not available')}-{result.get('address', 'address not available')}",
        'email': result.get('email', 'Next of kin email not provided'),
        'phone_number': result.get('phone_number', 'Phone number not available'),
        'associated_persons': result.get('persons', 'other kin relatives not available')
    }
    
    # Process associated persons
    if 'persons' in result:
        for person in result.get('persons', []):
            associated_person = {}
            
            # If person is just a string, add it as a name
            if isinstance(person, str):
                associated_person['name'] = person
            # If person is a dictionary, extract available details
            elif isinstance(person, dict):
                associated_person = person
            
            processed_data['associated_persons'].append(associated_person)
    
    return processed_data


def search_clustrmaps(first_name, middle_name=None, last_name=None):
    """
    Search Clustrmaps with flexible name matching
    
    Args:
        first_name (str): First name
        middle_name (str, optional): Middle name
        last_name (str, optional): Last name
    
    Returns:
        dict or None: Scraped person data
    """
    # Construct full name variations for matching
    full_name_variations = []
    if middle_name:
        full_name_variations.extend([
            f"{first_name} {middle_name} {last_name}",
            f"{first_name} {get_initial(middle_name)} {last_name}",
            f"{first_name} {last_name}"
        ])
    else:
        full_name_variations.extend([
            f"{first_name} {last_name}",
            #f"{first_name} {get_initial(last_name)} {last_name}",
            f"{first_name} {last_name[0]}",
            f"{last_name} {first_name}",
            # f"{last_name[0]} {first_name}",
            # f"{first_name} {last_name[1]}",
            # f"{first_name} {get_initial(first_name)} {last_name}"
        ])
    
    # URL for the API endpoint
    url = 'https://clustrmaps.com/search/live'
    
    # Headers based on the provided request headers
    headers = {
        'authority': 'clustrmaps.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://clustrmaps.com',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # Try each name variation
        for name_variant in full_name_variations:
            # Payload with the query
            payload = {'q': name_variant}
            
            # Send POST request
            response = session.post(url, headers=headers, data=payload)
            response.raise_for_status()
            
            # Parse JSON response
            results = response.json()
            
            # Use improved matching logic
            best_match = improved_matching_logic(
                results, 
                first_name, 
                last_name or '', 
                full_name_variations
            )
            
            # If a match is found, scrape the person's page
            if best_match:
                print(f"Matched result: {best_match}")
                
                # Scrape the person's detailed page
                person_data = scrape_person_page(session, best_match['link'], headers)
                
                return person_data
        
        # If no matching results found
        print(f"No match found for names: {full_name_variations}")
        return None
    
    except requests.RequestException as e:
        print(f"Request Error occurred: {e}")
        return None
    except Exception as e:
        print(f"Unexpected Error occurred: {e}")
        return None
    finally:
        session.close()
        
        
        
def improved_matching_logic(results, first_name, last_name, name_variants):
    """
    Improved matching logic for ClusterMaps search results.
    
    Args:
        results (dict): Search results dictionary
        first_name (str): First name to match
        last_name (str): Last name to match
        name_variants (list): List of possible name variations
    
    Returns:
        dict or None: Best matching result or None if no match found
    """
    def name_similarity_score(result_name, target_name_parts):
        """
        Calculate similarity score between result name and target name.
        
        Args:
            result_name (str): Name from search result
            target_name_parts (list): List of name parts to match
        
        Returns:
            float: Similarity score (higher is better)
        """
        if not result_name:
            return 0
        
        # Convert to lowercase for case-insensitive matching
        result_words = result_name.lower().split()
        target_words = [part.lower() for part in target_name_parts]
        
        # Calculate word overlap
        word_overlap = len(set(result_words) & set(target_words))
        
        # Bonus for full name match
        full_name_match = int(all(word in result_words for word in target_words))
        
        # Penalty for extra words
        extra_words_penalty = len(result_words) - len(target_words)
        
        return word_overlap + full_name_match * 2 - max(0, extra_words_penalty)

    def is_valid_person_result(result):
        """
        Check if the result is a valid person result.
        
        Args:
            result (dict): Individual search result
        
        Returns:
            bool: True if valid, False otherwise
        """
        # Ensure it's a person type result with a link
        return (
            result.get('t') == 'p' and 
            result.get('link', '').startswith('https://clustrmaps.com/person/')
        )

    # Combine name variants for broader matching
    name_search_variants = [
        [first_name, last_name],  # Standard order
        [last_name, first_name],  # Reversed order
        [name_variants[0]] if name_variants else []  # Additional name variant if available
    ]

    # Collect potential matches
    potential_matches = []

    # Iterate through search results
    for result in results.get('result', []):
        # Skip non-person results
        if not is_valid_person_result(result):
            continue

        # Check each name variant for matching
        for name_parts in name_search_variants:
            similarity_score = name_similarity_score(result.get('name', ''), name_parts)
            
            # Only consider results with a meaningful similarity score
            if similarity_score > 0:
                potential_matches.append({
                    'result': result,
                    'score': similarity_score
                })

    # If no potential matches found, return None
    if not potential_matches:
        return None

    # Sort matches by similarity score in descending order
    potential_matches.sort(key=lambda x: x['score'], reverse=True)

    # Return the top match's result
    return potential_matches[0]['result']



def scrape_person_page(session, link, headers):
    try:
        # Send GET request to person's page
        person_response = session.get(link, headers=headers, timeout=10)
        person_response.raise_for_status()
        
        # Parse person's page
        person_soup = BeautifulSoup(person_response.text, 'html.parser')
        #print(f"Person Soup is {person_soup}")
        
        # Initialize person data dictionary
        person_data = {
            'full_name': '',
            'age': '',
            'location': '',
            'email': '',
            'phone_number': '',
            'associated_persons': []
        }
        
        # Extract name and location
        name_elem = person_soup.find('h1', class_='person-name')
        addon_elem = person_soup.find('div', class_='person-addon')
        
        if name_elem:
            person_data['full_name'] = name_elem.get_text(strip=True)
        
        if addon_elem:
            addon_text = addon_elem.get_text(strip=True)
            person_data['location'] = addon_text.split(',')[-1].strip()
            
            # Try to extract age
            if 'age' in addon_text:
                person_data['age'] = addon_text.split('age')[1].split(',')[0].strip()
        
        # Extract phone number
        phone_elem = person_soup.find('span', itemprop='telephone')
        if phone_elem:
            person_data['phone_number'] = phone_elem.get_text(strip=True)
        
        # Extract email
        email_elem = person_soup.find('span', itemprop='email')
        if email_elem:
            person_data['email'] = email_elem.get_text(strip=True)
        
        # Extract associated persons
        associated_persons = person_soup.find_all('div', class_='card-body', itemprop='relatedTo')
        for assoc_person in associated_persons:
            assoc_data = {}
            
            # Name
            name_elem = assoc_person.find('span', itemprop='name')
            if name_elem:
                assoc_data['name'] = name_elem.get_text(strip=True)
            
            # Age
            age_elem = assoc_person.find('div', text=lambda t: t and 'Age' in t)
            if age_elem:
                assoc_data['age'] = age_elem.get_text(strip=True).replace('Age', '').strip()
            
            # Phone
            phone_elem = assoc_person.find('span', itemprop='telephone')
            if phone_elem:
                assoc_data['phone'] = phone_elem.get_text(strip=True)
            
            person_data['associated_persons'].append(assoc_data)
        
        # Save to JSON file
        output_dir = 'new_scraped_data'
        os.makedirs(output_dir, exist_ok=True)
        
        # Use first and last name from the full name for filename
        name_parts = person_data['full_name'].split()
        first_name = name_parts[0]
        last_name = name_parts[-1]
        
        output_file = os.path.join(output_dir, f'{first_name}_{last_name}_clustrmaps_data.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(person_data, f, indent=4)
        
        print(f"Data saved to {output_file}")
        
        return person_data
    
    except requests.RequestException as e:
        print(f"Error scraping {link}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

# Example usage
# Utility function to get initial
def get_initial(name):
    """
    Get the first letter of a name
    
    Args:
        name (str): Name to get initial from
    
    Returns:
        str: First letter, capitalized
    """
    return name[0].upper() if name else ''





def main():
    # Input and output file paths
    input_file = "ancestry_obituaries2.json"
    output_file = "processed_obituaries.json"
    
    # Load existing processed data
    processed_data = load_processed_data(output_file)
    
    # Load deceased persons data
    with open(input_file, "r") as file:
        deceased_list = json.load(file)
    
    # Track progress to allow resuming
    start_index = len(processed_data)
    
    # Process each deceased person
    for i, person in enumerate(deceased_list[start_index:], start=start_index):
        name_parts = person["Name"].split()
        relatives = person["Relatives"]
        
        # Determine first and last name for search
        if relatives:
            first_name = random.choice(relatives)
            last_name = name_parts[-1]
        else:
            first_name = name_parts[0]
            last_name = name_parts[-1]
        
        print(f"Accessing {first_name} - {last_name}")
        
        try:
            # Perform ClusterMaps search
            result = search_clustrmaps(first_name, last_name=last_name)
            
            # Skip if no match found
            if not result:
                print(f"No match found for names: ['{first_name} {last_name}', '{first_name} {last_name[0]} {last_name}']")
                continue
            
            # Process and save the result
            #processed_result = process_clustrmaps_result(result, person["Name"])
            processed_data[person["Name"]] = result
            
            # Save progress after each successful match
            save_processed_data(output_file, processed_data)
            
            # Print person data for logging
            print("Person Data:")
            for key, value in result.items():
                print(f"{key}: {value}")
        
        except Exception as e:
            print(f"Error processing {first_name} {last_name}: {e}")
            continue
    
    print("Processing complete.")

# Note: You'll need to implement the search_clustrmaps function separately
# This should be your existing function that performs the ClusterMaps search

if __name__ == "__main__":
    main()



# # # Example usage
# # first_name = "James"
# # last_name = "Abiusi"
# with open("ancestry_obituaries2.json", "r") as file:
#     deceased = json.load(file)
#     for person in deceased:
#         name_parts = person["Name"].split()
#         relatives = person["Relatives"]
#         if relatives:
#             random_relative = random.choice(relatives)
#         else:
#             random_relative = None
#         first_name = random_relative
#         last_name = name_parts[-1]
#         print(f"Accessing {first_name} - {last_name}")
#         if first_name == None:
#             result = search_clustrmaps(name_parts[0], last_name=last_name)
#         else:
#             result = search_clustrmaps(first_name, last_name=last_name)
        
#         if result:
#             print("Person Data:")
#             for key, value in result.items():
#                 print(f"{key}: {value}")
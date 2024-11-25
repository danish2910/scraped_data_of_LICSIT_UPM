import requests
import re
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # Import tqdm for a progress bar

# URL and headers for the POST request
url = "http://licsit.upm.edu.my/MainPage/detailOrganisation"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "http://licsit.upm.edu.my",
    "Connection": "keep-alive",
    "Referer": "http://licsit.upm.edu.my/",
    "Upgrade-Insecure-Requests": "1",
    "Priority": "u=0, i"
}

# Define the cookie for the session (replace with your actual PHPSESSID cookie)
cookies = {
    "PHPSESSID": "kctog94d9qrr2qqkssnhmosa0i"
}

# Regex patterns to extract City, Organisation Name, Remarks, and Blacklist
city_pattern = r'<th style="text-align:left">City<\/th>\n<td.*">(.*)<'
org_name_pattern = r'<th style="width:200px;text-align:left">Organisation Name<\/th>\n<td.*">(.*)<'
remarks_pattern = r'<th style="text-align:left;vertical-align:top">Remark<\/th>\n<td.*">(.*)<'
blacklist_pattern = r'<th style="text-align:left">Blacklist Reason<\/th>\n<td.*">(.*)<'

# Function to send POST request and extract data using regex
def fetch_organisation_data(organisation_dataid):
    payload = {
        "organisationDisplayLength": "10",
        "organisationDataid": str(organisation_dataid),  # Iterates over different IDs
        "iDisplayLength": "",
        "iDisplayStart": "",
        "sSearch": "",
        "dataid": "",
        "loginForm": "",
        "organisationSearch": "",
        "organisationDisplayStart": "0"
    }

    # Send the POST request
    try:
        response = requests.post(url, headers=headers, cookies=cookies, data=payload)

        # Check if the request was successful
        if response.status_code == 200:
            # Apply regex to find City, Organisation Name, Remarks, and Blacklist
            city_match = re.search(city_pattern, response.text)
            org_name_match = re.search(org_name_pattern, response.text)
            remarks_match = re.search(remarks_pattern, response.text)
            blacklist_match = re.search(blacklist_pattern, response.text)

            # Extract the city, organisation name, remarks, and blacklist if found
            city = city_match.group(1) if city_match else "Not Found"
            organisation_name = org_name_match.group(1) if org_name_match else "Not Found"
            remarks_text = remarks_match.group(1) if remarks_match else "Not Found"
            blacklist_text = blacklist_match.group(1) if blacklist_match else "Not Found"
            
            return organisation_dataid, city, organisation_name, remarks_text, blacklist_text
        else:
            # In case of failure, return None values to indicate issues
            return organisation_dataid, "Error", "Error", "Error", "Error"
    except Exception as e:
        print(f"Error for organisationDataid {organisation_dataid}: {e}")
        return organisation_dataid, "Error", "Error", "Error", "Error"

# Function to process and save the results to CSV
def process_and_save_to_csv(results):
    # Open the CSV file in write mode
    with open('organisations_data.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write the header row
        writer.writerow(['Organisation Data ID', 'City', 'Organisation Name', 'Remarks', 'Blacklist Reason'])
        
        # Write the data rows
        for organisation_dataid, city, org_name, remarks_text, blacklist_text in results:
            # Skip rows with empty organisation name or "Error"
            if org_name.strip() != "Not Found" and org_name.strip() != "Error":
                writer.writerow([organisation_dataid, city, org_name, remarks_text, blacklist_text])

# Main function to run concurrent requests
def main():
    # Define the range of organisationDataid (modify as needed)
    organisation_dataids = range(1, 20000)  # Assuming ids range from 1 to 10000 or any other range

    total_tasks = len(organisation_dataids)
    results = []

    # Use ThreadPoolExecutor to send requests concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:  # You can adjust the number of workers
        # Submit tasks for each organisationDataid
        future_to_id = {executor.submit(fetch_organisation_data, organisation_dataid): organisation_dataid for organisation_dataid in organisation_dataids}

        # Create a tqdm progress bar
        with tqdm(total=total_tasks, desc="Processing Requests", unit="request") as pbar:
            # Wait for all futures to complete and collect the results
            for future in as_completed(future_to_id):
                organisation_dataid, city, org_name, remarks_text, blacklist_text = future.result()
                # Only collect results with valid data (not "Error")
                if city != "Error" and org_name != "Error":
                    results.append((organisation_dataid, city, org_name, remarks_text, blacklist_text))
                pbar.update(1)  # Update the progress bar after each task

    # Process and save the results to a CSV
    process_and_save_to_csv(results)
    print("Data collection complete and saved to 'organisations_data.csv'")

# Run the main function
if __name__ == "__main__":
    main()

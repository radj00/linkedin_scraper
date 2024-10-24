from linkedin_scraper import JobSearch, actions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import os
from time import sleep
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()
email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")
search_term = os.getenv("SEARCH_TERM")
location = os.getenv("LOCATION")

# Function to save job listings to a CSV file
def save_jobs_to_csv(job_listings, search_term):
    """Save the list of Job objects to a CSV file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{search_term.replace(' ', '_')}.csv"  # Format filename
    print(f"Step 11: Saving {len(job_listings)} job(s) to CSV: {filename}...")  # Indicate saving to CSV
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Job Title", "Company", "Location", "LinkedIn URL"])  # Header
        for job in job_listings:
            writer.writerow([job.job_title, job.company, job.location, job.linkedin_url])
    print("Jobs saved successfully.")  # Indicate success

# Step 1: Set up the Selenium WebDriver
print("Step 1: Setting up the WebDriver...")  # Indicate WebDriver setup
driver = webdriver.Chrome()

# Step 2: Log in to LinkedIn
try:
    print("Step 2: Logging in to LinkedIn...")  # Indicate login start
    actions.login(driver, email, password)
    # Step 3: Wait for user input to continue
    input("Step 3: Press Enter to proceed...") 
    print("Login successful.")  # Indicate successful login
except Exception as e:
    print("An error occurred during login.")  # Error in login
    print(f"Error details: {e}")
    with open("page_source.txt", "w", encoding="utf-8") as f:
        print("Saving page source to 'page_source.txt'...")  # Save the page source on error
        f.write(driver.page_source)
    driver.quit()
    exit()

# Step 4: Initialize JobSearch without scraping initially
print("Step 4: Initializing JobSearch object...")  # Indicate JobSearch initialization
job_search = JobSearch(driver=driver, close_on_complete=False, scrape=False)

# Step 5: Initialize the list to hold all job listings
all_job_listings = []
job_found = False  # Flag to check if any job listings were found

try:
    # Step 6: Start searching for jobs
    print(f"Step 6: Searching for '{search_term}' jobs...")  # Indicate job search start
    job_listings = job_search.search(search_term, location)  # First page results
    all_job_listings.extend(job_listings)
    
    if job_listings:  # Check if any job listings were found
        job_found = True  # Set flag to True
        print(f"Found {len(job_listings)} job(s) on the first page.")  # Indicate jobs found
    else:
        print("No job listings found on the first page.")  # No jobs found

    # Step 11: Save the job listings to a CSV file
    if job_found:  # Save to CSV only if jobs were found
        save_jobs_to_csv(all_job_listings, search_term)

except Exception as e:
    print("An error occurred during job search.")  # Error during job search
    print(f"Error details: {e}")
    with open("page_source.txt", "w", encoding="utf-8") as f:
        print("Saving page source to 'page_source.txt'...")  # Save page source on error
        f.write(job_search.driver.page_source)

# Step 12: Optionally, close the driver after scraping
print("Step 12: Closing the WebDriver...")  # Indicate WebDriver closure
driver.quit()

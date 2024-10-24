import os
from typing import List
from time import sleep
import urllib.parse
import logging

from .objects import Scraper
from . import constants as c
from .jobs import Job

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoAlertPresentException, TimeoutException

class JobSearch(Scraper):
    AREAS = ["recommended_jobs", None, "still_hiring", "more_jobs"]
    
    def __init__(self, driver, base_url="https://www.linkedin.com/jobs/", close_on_complete=False, scrape=True, scrape_recommended_jobs=True):
        print("A: Initializing JobSearch... (JobSearch.__init__)")  # Indicate initialization
        super().__init__()
        self.driver = driver
        self.base_url = base_url
        self.error_count = 0  # Initialize error count

        # Set up logging
        logging.basicConfig(filename='error_log.txt', level=logging.ERROR, format='%(asctime)s - %(message)s')

        if scrape:
            print("B: Starting the scraping process... (JobSearch.__init__)")  # Indicate scraping start
            self.scrape(close_on_complete, scrape_recommended_jobs)

    def log_error(self, message: str):
        """Log an error message to the text file and increment the error count."""
        logging.error(message)
        self.error_count += 1

    def report_errors(self):
        """Report the total number of errors to the console."""
        print(f"Total errors encountered: {self.error_count}. Check 'error_log.txt' for details.")

    def accept_alert(self):
        try:
            WebDriverWait(self.driver, 10).until(EC.alert_is_present())  # Wait for the alert to be present
            alert = self.driver.switch_to.alert  # Switch to the alert
            alert.accept()  # Accept the alert
            print("Alert accepted.")  # Log alert acceptance
        except TimeoutException:
            self.log_error("No alert present within the timeout period.")  # Log timeout exception
        except NoAlertPresentException:
            self.log_error("No alert present.")  # Log if no alert is present
        except Exception as e:
            self.log_error(f"An error occurred while handling the alert: {e}")  # Log other exceptions

    def scrape(self, close_on_complete=True, scrape_recommended_jobs=True):
        print("C: Checking if user is signed in... (JobSearch.scrape)")
        if self.is_signed_in():
            print("D: User is signed in. Proceeding to scrape... (JobSearch.scrape)")
            self.scrape_logged_in(close_on_complete=close_on_complete, scrape_recommended_jobs=scrape_recommended_jobs)
            self.accept_alert()  # Call the method to handle potential alerts
        else:
            self.log_error("User is not signed in. Raising NotImplemented error... (JobSearch.scrape)")
            raise NotImplementedError("This part is not implemented yet")

    def scrape_logged_in(self, close_on_complete=True, scrape_recommended_jobs=True):
        print("F: User is logged in. Navigating to base URL... (JobSearch.scrape_logged_in)")
        driver = self.driver
        driver.get(self.base_url)

        if scrape_recommended_jobs:
            print("G: Scraping recommended jobs... (JobSearch.scrape_logged_in)")
            self.focus()
            sleep(self.WAIT_FOR_ELEMENT_TIMEOUT)
            
            print("H: Waiting for job area to load... (JobSearch.scrape_logged_in)")
            job_area = self.wait_for_element_to_load(name="scaffold-finite-scroll__content")

            print("I: Loading all job areas... (JobSearch.scrape_logged_in)")
            areas = self.wait_for_all_elements_to_load(name="artdeco-card", base=job_area)
            for i, area in enumerate(areas):
                area_name = self.AREAS[i]
                if not area_name:
                    print(f"J: Skipping area {i} as it has no name... (JobSearch.scrape_logged_in)")
                    continue

                if "top-job-picks" in area.get_attribute("class"):  # Example class name
                    print(f"Skipping area: {area_name} as it is 'Top job picks for you'... (JobSearch.scrape_logged_in)")
                    continue

                print(f"K: Scraping area: {area_name}... (JobSearch.scrape_logged_in)")
                area_results = []
                for job_posting in area.find_elements_by_class_name("jobs-job-board-list__item"):
                    job = self.scrape_job_card(job_posting)
                    area_results.append(job)
                setattr(self, area_name, area_results)
        print("L: Completed scraping recommended jobs... (JobSearch.scrape_logged_in)")
        self.report_errors()  # Report any errors encountered

    def click_next_button(self):
        try:
            print("Step 8: Looking for the 'Next' button...")
            next_button = self.wait_for_element_to_load(name="jobs-search-pagination__button--next")
            
            if next_button and next_button.is_enabled():
                print("Clicking the 'Next' button...")
                next_button.click()
                return True
            else:
                self.log_error("Next button not found.")  # Log button not found
                return False

        except Exception as e:
            self.log_error(f"Failed to click the 'Next' button: {e}")  # Log error
            return False

    def scrape_job_card(self, base_element) -> Job:
        #M: Scraping job card...
        try:
            job_div = self.wait_for_element_to_load(name="job-card-list__title", base=base_element)
            job_title = job_div.text.strip()
            linkedin_url = job_div.get_attribute("href")

            company = base_element.find_element(By.CLASS_NAME, "artdeco-entity-lockup__subtitle").text.strip()
            location = base_element.find_element(By.CLASS_NAME, "job-card-container__metadata-wrapper").text.strip()

            job = Job(linkedin_url=linkedin_url, job_title=job_title, company=company, location=location, scrape=False, driver=self.driver)
            return job
        
        except Exception as e:
            self.log_error(f"Error scraping job card: {e}")  # Log job card scraping error
            return None

    def search(self, search_term: str, location: str = None, continue_searching: bool = False) -> List[Job]:
        if not continue_searching:
            print(f"a: Searching for jobs with term: {search_term}... (JobSearch.search)")
            url = os.path.join(self.base_url, "search") + f"?keywords={urllib.parse.quote(search_term)}"
            
            if location:  # Check if location is provided
                url += f"&location={urllib.parse.quote(location)}"  # Add location to URL
            
            print(f"b: Generated search URL: {url} (JobSearch.search)")
            self.driver.get(url)

        print("c: Scrolling to bottom of job listing... (JobSearch.search)")
        self.scroll_to_bottom()
        self.focus()
        sleep(self.WAIT_FOR_ELEMENT_TIMEOUT)

        job_listing_class_name = "jobs-search-results-list"
        print(f"d: Waiting for job listing element to load: {job_listing_class_name}... (JobSearch.search)")
        job_listing = self.wait_for_element_to_load(name=job_listing_class_name)

        self.scroll_class_name_element_to_page_percent(job_listing_class_name, 0.3)
        self.focus()
        sleep(self.WAIT_FOR_ELEMENT_TIMEOUT)

        self.scroll_class_name_element_to_page_percent(job_listing_class_name, 0.6)
        self.focus()
        sleep(self.WAIT_FOR_ELEMENT_TIMEOUT)

        self.scroll_class_name_element_to_page_percent(job_listing_class_name, 1)
        self.focus()
        sleep(self.WAIT_FOR_ELEMENT_TIMEOUT)

        print("e: Scraping job results... (JobSearch.search)")
        job_results = []
        for job_card in self.wait_for_all_elements_to_load(name="job-card-list", base=job_listing):

            job = self.scrape_job_card(job_card)
            if job:  # Ensure job is not None before appending
                job_results.append(job)

        print(f"f: Found {len(job_results)} job(s)... (JobSearch.search)")

        if self.click_next_button():
            print("g: Proceeding to next page of job results... (JobSearch.search)\n")
            job_results += self.search(search_term, continue_searching=True)

        return job_results

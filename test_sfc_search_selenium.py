from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def sfc_search_selenium(name_to_search: str):
    """
    Searches the HKSFC Public Register using Selenium instead of pyppeteer.
    """
    print(f"--- Starting search for: {name_to_search} ---")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--headless")  # Uncomment to run in background
    
    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to the search page
        search_url = 'https://apps.sfc.hk/publicregWeb/search-by-name'
        driver.get(search_url)
        print(f"Navigated to {search_url}")
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
        # Select 'Individual' radio button
        individual_radio = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Individual']")))
        individual_radio.click()
        print("Selected 'Individual' radio button")
        
        # Find and fill the search input
        search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id^='searchtextname-']")))
        search_input.clear()
        search_input.send_keys(name_to_search)
        print(f"Typed name: {name_to_search}")
        
        # Click search button
        search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.sfcButton")))
        search_button.click()
        print("Clicked 'Search' button")
        
        # Wait for results
        time.sleep(3)  # Give time for results to load
        
        # Check for no results
        try:
            no_result = driver.find_element(By.CSS_SELECTOR, "div.x-form-display-field-red")
            error_text = no_result.text
            print("\n----------------------")
            print("Result: NO LICENSE")
            print(f"Reason: {error_text.strip()}")
            print("----------------------")
            driver.save_screenshot('sfc_no_license_found.png')
            
        except:
            # Look for results table and details link
            try:
                details_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//td[contains(@class, 'x-grid-cell')]//a[text()='details']")))
                details_link.click()
                
                # Wait for details page
                wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Licence Details for Individual')]")))
                
                print("\n----------------------")
                print("Result: LICENSE DETAILS FOUND")
                print("Successfully navigated to the details page.")
                print("Saving screenshot to 'sfc_license_details.png'")
                print("Saving page content to 'sfc_license_details.html'")
                print("----------------------")
                
                driver.save_screenshot('sfc_license_details.png')
                
                with open('sfc_license_details.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                    
            except Exception as e:
                print(f"Error finding details link: {e}")
                driver.save_screenshot('sfc_error.png')
                
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        driver.save_screenshot('sfc_error.png')
        
    finally:
        driver.quit()
        print("--- Search finished ---")

if __name__ == "__main__":
    # Test with a name that should have a license
    sfc_search_selenium("KEUNG Yat Long") 
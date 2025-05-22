from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv


def init_driver(): #this function helps to initialize the Chrome driver
    options = Options()
    # options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def scrape_tender():#main function to scrape the tender listings.
    driver = init_driver()
    url = 'https://www.gebiz.gov.sg/ptn/opportunity/BOListing.xhtml?origin=opportunities' #GeBiz URL
    driver.get(url)
    wait = WebDriverWait(driver, 10) #wait for the page to load
    try:
        print("Finding the search box…")
        
        #wait for the searh box to load
        kw = wait.until(EC.presence_of_element_located((
        By.ID, "contentForm:j_idt179_searchBar_INPUT-SEARCH"
        )))
    except Exception as e:
        print("Failed to load the search box.")
        print(e)
        return
    kw.clear()                                                                                  #clear the search box
    print("Entering search term…")
    old = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "commandLink_TITLE-BLUE"))
    )                                                                                           #Find the old element to wait for staleness
    
    kw.send_keys("Facilities Management")                                                       #entering the keywords for search
    
    go_btn = wait.until(
        EC.element_to_be_clickable((By.ID, "contentForm:j_idt179_searchBar_BUTTON-GO")))        #wait for the search button to be clickable
    
    go_btn.click()
    print("Clicking search button…")
    WebDriverWait(driver, 15).until(EC.staleness_of(old))                                       #wait for the old element to be stale

    try:
        #wait for new search results to load
        wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "commandLink_TITLE-BLUE"))
        )
        
        #scrape the tender titles
        titles = driver.find_elements(By.CLASS_NAME, "commandLink_TITLE-BLUE")
        
        for i, title in enumerate(titles, 1):
            print(f"{i}. {title.text.strip()}")
    except Exception as e:
        print("Failed to find tender listings.")
        print(e)
    driver.quit()
    
def scrape_by_keyword(keyword):
    results = []
    driver = init_driver()
    url = 'https://www.gebiz.gov.sg/ptn/opportunity/BOListing.xhtml?origin=opportunities' #GeBiz URL
    driver.get(url)
    wait = WebDriverWait(driver, 20) #wait for the page to load
    try:
        print("Finding the search box…")
        #wait for the searh box to load
        kw = wait.until(EC.presence_of_element_located((
        By.ID, "contentForm:j_idt179_searchBar_INPUT-SEARCH"
        )))
    except Exception as e:
        print("Failed to load the search box.")
        print(e)
        return
    kw.clear()                                                                                  #clear the search box
    print("Entering search term…")
    old = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "commandLink_TITLE-BLUE"))
    )                                                                                           #Find the old element to wait for staleness
    kw.send_keys(keyword)    
    go_btn = wait.until(
    EC.element_to_be_clickable((By.ID, "contentForm:j_idt179_searchBar_BUTTON-GO")))        #wait for the search button to be clickable
    go_btn.click()
    print("Clicking search button…")
    WebDriverWait(driver, 15).until(EC.staleness_of(old))                                   #wait for the old element to be stale
    #scrape open tab first
    open_results = scrape_current_page(driver, wait, "Open")
    results.extend(open_results)
    #scrape closed tab
    try:
        closed_tab = wait.until(
            EC.element_to_be_clickable((By.ID, "contentForm:j_idt794_TabAction_1"))
        )
        closed_tab.click()
        print("Clicking closed tab…")
        WebDriverWait(driver, 15).until(EC.staleness_of(old)) #wait for the old element to be stale
        closed_results = scrape_current_page(driver, wait, "Closed")
    except Exception as e:
        print("Failed to find closed tab.")
        print(e)
        closed_results = []
    results.extend(closed_results)
    return results
        
        
    
def scrape_current_page(driver, wait, tag):
    page_results = []
    i = 2; #for next button to start from page 2
    while True:
        try:
            #wait for new search results to load
            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "commandLink_TITLE-BLUE"))
            ) 
            #scrape the tender titles
            titles = driver.find_elements(By.CLASS_NAME, "commandLink_TITLE-BLUE")
            old = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "commandLink_TITLE-BLUE"))
            )
            for t in titles:
                page_results.append({"Tab": tag, "Title": t.text.strip()})
            try:
                next_button = wait.until(
                    EC.element_to_be_clickable((By.ID, f"contentForm:j_idt906:j_idt957_Next_{i}"))
                    )
                next_button.click()
                print(f"Clicking next button for page {i}…") # for debugging
                WebDriverWait(driver, 15).until(EC.staleness_of(old)) #wait for the old element to be stale
                i += 1 #to increment and find the next button for subsequent pages if any.
            except:
                print(f"Total pages: {i-1}")
                break   
        except Exception as e:
            print("Failed to find tender listings.")
            break
    return page_results

#for i, title in enumerate(titles, 1): <incase
#print(f"{i}. {title.text.strip()}")
    
if __name__ == "__main__": #main function to run the script. Mostly used for testing.
    print("Starting GeBIZ scraper…")
    Keywords = ["Facilities Management", "FM", "IFM","Digital FM", "Integrated FM", "Integrated Facilities Management"]
    all_results = []
    for keyword in Keywords:
        print(f"Scraping for keyword: {keyword}")
        keyword_results = []
        keyword_results.extend(scrape_by_keyword(keyword))
        all_results.extend(keyword_results)
    
    for result in all_results:
        print(f"Tab: {result['Tab']}, Title: {result['Title']}")
    print("Scrape complete.")
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


options = Options()
options.add_argument('--headless')  # optional: hide browser window
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
url = 'https://www.gebiz.gov.sg/ptn/opportunity/BOListing.xhtml?origin=opportunities'
driver.get(url)
wait = WebDriverWait(driver, 20)

# Wait for page to load
try:
    wait.until(
        EC.invisibility_of_element_located((By.CLASS_NAME, "loadingScreen_BACKGROUND"))
    )
except TimeoutException:
    print("⚠️ Loading screen element not found or already gone. Continuing...")
    
try:
    #Wait for tender link appears
    wait.until(
        EC.presence_of_element_located((By.CLASS_NAME, "commandLink_TITLE-BLUE"))
    )
    
    #Now scrape the tender titles
    titles = driver.find_elements(By.CLASS_NAME, "commandLink_TITLE-BLUE")
    
    for i, title in enumerate(titles, 1):
        print(f"{i}. {title.text.strip()}")
except Exception as e:
    print("❌ Failed to find tender listings.")
    print(e)

driver.quit()
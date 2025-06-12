from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd


all_results = []

def init_driver(): #this function helps to initialize the Chrome driver
    options = Options()
    #options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

    
def scrape_by_keyword(keyword):
    results = []
    driver = init_driver()
    url = 'https://www.gebiz.gov.sg/' #GeBiz URL
    driver.get(url)
    wait = WebDriverWait(driver, 5) #wait for the page to load
    try:
        ##print("Finding the search box…")
        #wait for the searh box to load
        kw = wait.until(EC.presence_of_element_located((
        By.ID, "contentForm:searchBar_searchBar_INPUT-SEARCH"
        )))
    except Exception as e:
        ##print("Failed to load the search box.")
        print(e)
        return
    kw.clear()                                                                                  #clear the search box
    ##print("Entering search term…")                                                              
    kw.send_keys(keyword)
    go_btn = wait.until(
    EC.element_to_be_clickable((By.ID, "contentForm:j_idt187_searchBar_BUTTON-GO")))        #wait for the search button to be clickable
    go_btn.click()
    ##print("Clicking search button…")
    #scrape open tab first
    open_results = scrape_current_tab(driver, wait, "Open")
    for r in open_results:
        if r not in results:
            results.append(r)
    #scrape closed tab
    try:
        old = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "contentForm:j_idt794_TabAction_1"))
        )                                                                                         
        closed_tab = wait.until(
            EC.element_to_be_clickable((By.ID, "contentForm:j_idt794_TabAction_1"))
        )
        closed_tab.click()
        ##print("Clicking closed tab…")
        WebDriverWait(driver, 5).until(EC.staleness_of(old)) #wait for the old element to be stale
        closed_results = scrape_current_tab(driver, wait, "Closed")
    except Exception as e:
        ##print("Failed to find closed tab.")
        closed_results = []
    
    for r in closed_results:
        if r not in results:
            results.append(r)
    return results

def scrape_awardees(driver, wait, timeout=10):
    awardees=[]
    #wait for and find the "Awarded to" header
    wait.until(EC.presence_of_element_located((
        By.CSS_SELECTOR, "div.formSectionHeader4_MAIN"
    )))
    sections = driver.find_elements(By.CSS_SELECTOR, "div.formSectionHeader4_MAIN")
    
    print(len(sections))
    for sec in sections:
        try:
            #get just the header text inside this section
            header = sec.find_element(By.CSS_SELECTOR, "div.formSectionHeader4_TEXT").text.strip()
        except:
            continue
        
        if header != "Awarded to":
            #skip any other section
            continue
        
        #find its next sibling, which holds the awardee name
        try:
            content = sec.find_element(
                By.XPATH,
                "following-sibling::div[contains(@class,'formOutputText_MAIN')]"
            )
            #within that, pull the black-label div
            name_div = content.find_element(
                By.CSS_SELECTOR, "div.formOutputText_HIDDEN-LABEL.outputText_TITLE-BLACK"
            )
            text = name_div.text.strip()
            if text:
                awardees.append(text)
        except Exception:
            #if anything here fails, skip this section
            continue
    return awardees
        
    
def scrape_current_tab(driver, wait, tag):
    page_results = []
    def grab_links():
        #wait for new search results to load
        wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "commandLink_TITLE-BLUE"))
        )
        #scrape the tender titles
        link_elems = driver.find_elements(By.CLASS_NAME, "commandLink_TITLE-BLUE")
        links = [(e.text.strip(), e.get_attribute("href")) for e in link_elems]
        return links
    
    def scrape_single_tender(title, link):
        Quote = False
        driver.get(link)
        ##print(f"Clicked on link... {link}")
        wait.until(EC.presence_of_element_located((
            By.CLASS_NAME, "formOutputText_VALUE-DIV"
        )))
        try:
            tender_num = driver.find_element(
                By.XPATH,
                "//span[normalize-space(.)='Tender No.']"
                "/ancestor::div[contains(@class,'col-md-3')]"                   #up to the label’s row
                "/following-sibling::div[contains(@class,'col-md-9')]"          #the value’s container
                "//div[contains(@class,'formOutputText_VALUE-DIV')]"            #the value itself
            ).text.strip()
        except Exception as e:
            try:
                quotation = driver.find_element(
                    By.XPATH,
                    "//span[normalize-space(.)='Quotation No.']"
                    "/ancestor::div[contains(@class,'col-md-3')]"                   #up to the label’s row
                    "/following-sibling::div[contains(@class,'col-md-9')]"          #the value’s container
                    "//div[contains(@class,'formOutputText_VALUE-DIV')]"            #the value itself
                ).text.strip()
                Quote = True
            except Exception as e:
                ##print(f"Skipping tender {title} due to missing Tender/Quotation number.")
                return
        agency = driver.find_element(
            By.XPATH,
            "//span[normalize-space(.)='Agency']"
            "/ancestor::div[contains(@class,'col-md-3')]"                   #up to the label’s row
            "/following-sibling::div[contains(@class,'col-md-9')]"          #the value’s container
            "//div[contains(@class,'formOutputText_VALUE-DIV')]"            #the value itself
        ).text.strip()
        try:
            Ref_Num = driver.find_element(
            By.XPATH,
            "//span[normalize-space(.)='Reference No.']"
            "/ancestor::div[contains(@class,'col-md-3')]"                   #up to the label’s row
            "/following-sibling::div[contains(@class,'col-md-9')]"          #the value’s container
            "//div[contains(@class,'formOutputText_VALUE-DIV')]"            #the value itself
            ).text.strip()
            if Ref_Num == "":
                Ref_Num = "N/A"
        except Exception as e:
            Ref_Num = "N/A"
        ##print(f"Reference Number: {Ref_Num}")
        awarded = driver.find_element(
        By.ID, "j_idt238"
        ).text.strip()   
        try:
            respondents_btn = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "formTabBar_TAB-BUTTON"))
            )
            respondents_btn.click()
            ##print("Clicking on respondents button…")
            wait.until(EC.presence_of_element_located((
                By.CLASS_NAME, "formAccordion_TITLE-TEXT" 
            )))
            respondent_data = []
            accordion_blocks = driver.find_elements(By.CLASS_NAME, "formAccordion_MAIN")
            for block in accordion_blocks:
                try:
                    amount_elem = block.find_element(By.CLASS_NAME, "formAccordion_TITLE-BAR")
                    amount = amount_elem.text.strip()
                    respondent_elem = block.find_element(By.CLASS_NAME, "formAccordion_TITLE-TEXT")
                    respondent = respondent_elem.text.strip()                        
                    respondent_data.append((respondent, amount))
                    ##print(f"Respondent: {respondent}, Amount: {amount}")
                except Exception as e:
                    pass
                    ##print("Failed to find respondent or amount.")    
            if awarded == "AWARDED":
                ##print("Tender has been awarded, scraping awardee…")
                awarded_btn = wait.until(                        
                    EC.element_to_be_clickable((By.NAME, "contentForm:j_idt229_TabAction_2"))
                )
                awarded_btn.click()
                ##print("Clicking on awarded button…")
                awardee = scrape_awardees(driver, wait)
                ##print(f"Awardee: {awardee}")
                time.sleep(2)
            else:
                    awardee = "N/A"
        except Exception as e:
            ##print(f"No respondents found or failed to scrape them.")
            respondent_data = "N/A"
            awardee = "N/A"
        if Quote:
            print(f"Title: {title} Quotation Number: {quotation} Agency: {agency} ref_num: {Ref_Num} Awarded: {awarded} Respondents: {respondent_data} Awardee: {awardee}")
            page_results.append({"Title": title, "Tender Number": quotation, "Agency": agency , "Ref_Num": Ref_Num, "Awarded": awarded, "Respondents": respondent_data, "Awardee": awardee})
        else:
            print(f"Title: {title} Tender Number: {tender_num} Agency: {agency} ref_num: {Ref_Num} Awarded: {awarded} Respondents: {respondent_data} Awardee: {awardee}")
            page_results.append({"Title": title, "Tender Number": tender_num, "Agency": agency , "Ref_Num": Ref_Num, "Awarded": awarded, "Respondents": respondent_data, "Awardee": awardee}) 
    
    def back_to_results():
        try:
            #print("Finding back button to return to results page…")
            WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@value='Back to Search Results']"))
            )
            back_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Back to Search Results']"))
            )
            if back_btn:
                back_btn.click()
            else:
                driver.execute_script("""
            document.querySelector("input[value='Back to Search Results']").click();
            """)
            #print("Going back to results page…")
            return
        except Exception as e:
            #print("Failed to find back button.")
            print(e)
            return
        
    try:
        page_links = grab_links()
        old = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "commandLink_TITLE-BLUE"))
        )
        for title_text, href in page_links:
            if not any(r["Title"] == title_text for r in all_results):
                scrape_single_tender(title_text, href)
                back_to_results() #go back to the results page
                wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "commandLink_TITLE-BLUE"))
                )
            else:
                #print(f"Skipping {title_text} as it has already been scraped.")
                continue
    except Exception as e:
        pass
        #print("Failed to find tender listings.")
    i = 2; #for next button to start from page 2
    while True:   
        try:
            next_button = wait.until(
                EC.element_to_be_clickable((By.ID, f"contentForm:j_idt906:j_idt957_Next_{i}"))
                )
            next_button.click()
            #print(f"Clicking next button for page {i}…") # for debugging
            WebDriverWait(driver, 15).until(EC.staleness_of(old)) #wait for the old element to be stale
            i += 1 #to increment and find the next button for subsequent pages if any.
            page_links = grab_links()
            old = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "commandLink_TITLE-BLUE"))
            )
            for title_text, href in page_links:
                scrape_single_tender(title_text,href)
                back_to_results() #go back to the results page
                wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "commandLink_TITLE-BLUE"))
                )
        except:
            #print(f"Total pages: {i-1}")
            break
    return page_results
        
def save_to_csv(results, filename="gebiz_tenders.csv"):
    if not results:
        print("No results to save.")
    
    df = pd.DataFrame(results)
    
    sort_order = ["OPEN","AWARDED","PENDING AWARD","NO AWARD"]
    df['Awarded'] = pd.Categorical(df['Awarded'], categories=sort_order, ordered=True)
    
    df.sort_values(by=['Awarded', 'Title'], inplace=True)  # Sort by Tab and then Title
    df.insert(0, 'S/N', range(1, len(df)+1))
    
    columns = ['S/N', 'Awarded', 'Title', 'Agency' , 'Awardee', 'Tender Number', 'Ref_Num', 'Respondents']
    cols_to_write = [c for c in columns if c in df.columns]
    df.to_csv(filename, columns=cols_to_write, index=False, encoding='utf-8-sig')
    

#for i, title in enumerate(titles, 1): <incase
#print(f"{i}. {title.text.strip()}")
    
if __name__ == "__main__": #main function to run the script. Mostly used for testing.
    print("Starting GeBIZ scraper…")
    Keywords = ["Facilities Management", "IFM", "Integrated FM", "Integrated Facilities Management", "Integrated Building Services", "Building Services", "Managing Agent"]
    for keyword in Keywords:
        print(f"Scraping for keyword: {keyword}")
        keyword_results = []
        keyword_results.extend(scrape_by_keyword(keyword))
        for result in keyword_results:
            if result not in all_results:
                all_results.append(result)
    save_to_csv(all_results)
    print("Scrape complete.") 
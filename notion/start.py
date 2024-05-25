from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup

def start_scraping_after_manual_login():
    driver = webdriver.Chrome()
    driver.get("https://takanekofc.com/#/login")
    
    print("Please Login in to the website.")
    while input("Enter 'ok' after finishing login: ").strip().lower() != "ok":
        print("please re-enter 'ok'")

    max_page = int(input("maximum page: "))

    for page_number in range(1, max_page + 1):
        if page_number == 1:
            url = "https://takanekofc.com/#/notification"
        else:
            url = f"https://takanekofc.com/#/notification?page={page_number}"
        
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.link"))
        )
        
        links = driver.find_elements(By.CSS_SELECTOR, "a.link")
        number_of_links = len(links)
        
        for index in range(number_of_links):
            links = driver.find_elements(By.CSS_SELECTOR, "a.link")
            link = links[index]
            href = link.get_attribute('href')
            driver.get(href)  
            time.sleep(1)  
            
            content_data = extract_content(driver)
            if content_data:
                title, name, date, content = content_data
                # upload to notion
                upload_to_notion(title, name, date, content, "token", "id")
                print("Extracted and uploaded content:", title, name, date)
            driver.back()
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.link"))
            )

    driver.quit()

def format_date(original_date):
    try:
        # change date format to ISO 8601 to fit notion api
        datetime_object = datetime.strptime(original_date, "%Y.%m.%d %H:%M")
        iso_date = datetime_object.strftime("%Y-%m-%dT%H:%M:%SZ")
        return iso_date
    except ValueError:
        print("Date format error:", original_date)
        return None

def upload_to_notion(title, name, date, content, integration_token, database_id):
    headers = {
        "Authorization": "Bearer " + integration_token,
        "Content-Type": "application/json",
        "Notion-Version": "2022-02-22"
    }
    blocks = html_to_notion_blocks(content)
    data = {
        "parent": {"database_id": database_id},
        "properties": {
            "Title": {"rich_text": [{"text": {"content": title}}]},
            "Name": {"title": [{"text": {"content": name}}]},
            "Date": {"date": {"start": date}}
        },
        "children": blocks
    }
    response = requests.post('https://api.notion.com/v1/pages', headers=headers, json=data)
    if response.status_code != 200:
        print("Failed to upload data:", response.text)
    else:
        print("Data uploaded successfully to Notion!")

def extract_content(driver):
    try:
        title = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.fc-article-contents__title"))
        ).text
        
        name = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'flex column-align-center mt-10') and not(contains(@class,'fc-article-contents__icon'))]"))
        ).text
        
        original_date = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.fc-article-contents__date"))
        ).text
        
        # chage the date format to fit notion api
        date = format_date(original_date)
        
        content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.fc-article-contents__body"))
        ).get_attribute('innerHTML')
        
        print(f"Title: {title}\nName: {name}\nDate: {date}\nContent: {content[:100]}...")  # showing part of the context for debugging purpose
        return title, name, date, content
    except Exception as e:
        print(f"Error extracting content: {str(e)}")
        return None
 

def html_to_notion_blocks(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    blocks = []
    for element in soup.find_all('p'):  # find all p tag
        text_content = element.get_text(strip=True) if element.get_text(strip=True) else " " 
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": text_content}
                }]
            }
        })
    return blocks


start_scraping_after_manual_login()

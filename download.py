import os
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from urllib.parse import urljoin

def start_scraping_after_manual_login():
    driver = webdriver.Chrome()
    driver.get("https://takanekofc.com/#/login")
    
    print("Please login to the website.")
    while input("Enter 'ok' after finishing login: ").strip().lower() != "ok":
        print("Please re-enter 'ok'")

    max_page = int(input("Enter the maximum page number: "))

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

        for i in range(number_of_links):
            links = driver.find_elements(By.CSS_SELECTOR, "a.link")
            link = links[i]
            href = link.get_attribute('href')
            driver.get(href)

            if not content_already_exists(driver):  # Check if content already exists
                content_data = extract_content(driver)
                if content_data:
                    title, name, date, content = content_data
                    save_content(name, date, title, content, driver.page_source)
                    print("Extracted and saved content:", title, name, date)
                driver.back()
            else:
                print("Content already exists, skipping...")
                driver.back()
                
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.link"))
            )

    driver.quit()

def content_already_exists(driver):
    title = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h1.fc-article-contents__title"))
    ).text
    date = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.fc-article-contents__date"))
    ).text
    name = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'flex column-align-center mt-10') and not(contains(@class,'fc-article-contents__icon'))]"))
    ).text

    try:
        date_folder = datetime.strptime(date, "%Y.%m.%d %H:%M").strftime("%Y-%m-%d_%H-%M")
        member_folder = os.path.join(os.getcwd(), name)
        path = os.path.join(member_folder, date_folder, 'content.md')
        return os.path.exists(path)
    except ValueError as e:
        print(f"Error parsing date: {e}")
        return False

def extract_content(driver):
    try:
        title = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.fc-article-contents__title"))
        ).text
        
        name = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'flex column-align-center mt-10') and not(contains(@class,'fc-article-contents__icon'))]"))
        ).text
        
        date = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.fc-article-contents__date"))
        ).text
        
        content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.fc-article-contents__body"))
        ).get_attribute('innerHTML')
        
        return title, name, date, content
    except Exception as e:
        print(f"Error extracting content: {str(e)}")
        return None

def save_content(name, date, title, html_content, full_page_html):
    time.sleep(3)
    member_folder = os.path.join(os.getcwd(), name)
    try:
        date_folder = datetime.strptime(date, "%Y.%m.%d %H:%M").strftime("%Y-%m-%d_%H-%M")
    except ValueError as e:
        print(f"Error parsing date: {e}")
        return  

    path = os.path.join(member_folder, date_folder)
    
    if not os.path.exists(member_folder):
        os.makedirs(member_folder)
    if not os.path.exists(path):
        os.makedirs(path)
    
    file_path = os.path.join(path, 'content.md')
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write("# " + title + "\n\n" + html_content)  
    
    soup = BeautifulSoup(full_page_html, 'html.parser')
    base_url = 'https://takanekofc.com/'
    for img in soup.find_all('img'):
        img_url = img.get('src')
        if img_url:
            if not img_url.startswith(('http', 'https')):
                img_url = urljoin(base_url, img_url)  

            try:
                img_response = requests.get(img_url, stream=True)
                if img_response.status_code == 200:
                    img_name = os.path.basename(img_url)
                    img_path = os.path.join(path, img_name)
                    with open(img_path, 'wb') as img_file:
                        for chunk in img_response.iter_content(1024):
                            img_file.write(chunk)
                else:
                    print(f"Failed to download {img_url}: Server responded with status code {img_response.status_code}")
            except Exception as e:
                print(f"Error downloading {img_url}: {str(e)}")
        else:
            print("Found an image without a src attribute.")

    print(f"Content and images saved for {name} on {date}")

start_scraping_after_manual_login()

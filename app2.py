import streamlit as st
from bs4 import BeautifulSoup
import requests
from joblib import Parallel, delayed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# Function to scrape news text from NDTV
def get_news_text(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    news_paragraphs = soup.find_all('p')[:2]
    news_text = '\n'.join([p.text.strip() for p in reversed(news_paragraphs)])
    return news_text

# Function to scrape NDTV news
def scrape_page(url_pattern, tag_name, page_num):
    r = requests.get(f'{url_pattern}{page_num}')
    soup = BeautifulSoup(r.text, 'html.parser')
    news_items = soup.find_all(tag_name)
    results = []
    for item in news_items:
        headline = item.text.strip()
        link = item.a['href']
        news_text = get_news_text(link)
        results.append((headline, link, news_text))
    return results

# Function to scrape NDTV category
def scrape_category(url_pattern, tag_name, pages):
    results = Parallel(n_jobs=32, verbose=100)(delayed(scrape_page)(url_pattern, tag_name, page_num) for page_num in range(1, pages + 1))
    news_data = set()
    for page_result in results:
        for item in page_result:
            news_data.add(item)
    return news_data
#Function to scrap an news from addis insight
# import requests
# from bs4 import BeautifulSoup

# def scrape_addis_insight_headlines():
#     url = "https://www.addisinsight.net/"
#     response = requests.get(url)
#     soup = BeautifulSoup(response.content, 'html.parser')
    
#     # Use the correct selector to find all news links
#     news_links = soup.select('h3.entry-title a')
    
#     headlines = []
#     for link in news_links:
#         title = link.get_text(strip=True)
#         url = link.get('href')
#         if title and url:
#             headlines.append({'title': title, 'url': url})
    
#     return headlines

# if __name__ == "__main__":
#     headlines = scrape_addis_insight_headlines()
#     if headlines:
#         for item in headlines:
#             print(f"Title: {item['title']}")
#             print(f"URL: {item['url']}\n")
#     else:
#         print("No headlines found.")
# Function to scrape headlines and links from Google News
def scroll_down(driver, scroll_pause_time):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def scrape_google_news(category_url):
    chrome_options = Options()
    chrome_options.add_argument("--headless") 

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(category_url)
    time.sleep(5)
    scroll_down(driver, 2)
    page_source = driver.page_source
    driver.quit()

    soup = BeautifulSoup(page_source, 'html.parser')
    headlines = soup.find_all('a', class_='gPFEn')
    links = soup.find_all('a', class_='gPFEn')
    return headlines, links

# Streamlit app
st.title("News Aggregator")

source = st.selectbox("Select News Source", ["NDTV", "Google News", "Addis Insight"])

if source == "NDTV":
    category = st.selectbox("Select Category", ["Latest", "Cities", "Education", "Trending", "Offbeat"])
    
    if category == "Trending":
        news_data = scrape_category('https://www.ndtv.com/trends', 'h3', 1)
    else:
        url_pattern = f'https://www.ndtv.com/{category.lower()}/page-'
        pages = 14 if category != "Trending" else 1
        news_data = scrape_category(url_pattern, 'h2', pages)
        
        
        
elif source == "Addis Insight":
    category = st.selectbox(
        "Select Category",
        ["Latest", "Politics", "Business", "Culture", "Opinion"]
    )

    base_url = "https://www.addisinsight.net"
    category_paths = {
        "Latest": "/",
        "Politics": "/category/politics/",
        "Business": "/category/business/",
        "Culture": "/category/culture/",
        "Opinion": "/category/opinion/"
    }

    selected_path = category_paths.get(category, "/")

    # Build pattern for pagination
    url_pattern = base_url + selected_path + "page/{}/"
    pages = 3 if category != "Latest" else 1

    # Call the scraping function with the correct parameters for Addis Insight
    news_data = scrape_category(url_pattern, "h3.entry-title a", pages)
    
    # Optional: Display the scraped data
    if news_data:
        st.write(f"Found {len(news_data)} news articles.")
        # display logic here
    else:
        st.write("No news found for the selected category/source.")

        
elif source == "Google News":
    categories = {
        "Technology": "https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGRqTVhZU0JXVnVMVWRDR2dKSlRpZ0FQAQ?hl=en-IN&gl=IN&ceid=IN%3Aen",
        "World": "https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNRGx1YlY4U0JXVnVMVWRDS0FBUAE?hl=en-IN&gl=IN&ceid=IN%3Aen",
        "Business":"https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx6TVdZU0JXVnVMVWRDR2dKSlRpZ0FQAQ?hl=en-IN&gl=IN&ceid=IN%3Aen",
        "Ethiopia":"https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSkwyMHZNREU1Y0dOekVnVmxiaTFIUWlnQVAB?hl=en-ET&gl=ET&ceid=ET%3Aen"
    }
    selected_category = st.selectbox("Select a category", list(categories.keys()))
    category_url = categories[selected_category]
    headlines, links = scrape_google_news(category_url)
    if headlines:
        news_data = [(headline.text, "https://news.google.com" + link['href'], "") for headline, link in zip(headlines, links)]
    else:
        news_data = []

if news_data:
    st.subheader("Latest News")
    for headline, link, news_text in news_data:
        st.markdown(f"<h2 style='color: black; font-weight: bold;'>{headline}</h2>", unsafe_allow_html=True)
        if news_text:
            st.markdown(f"<p style='color: blue;'>{news_text}</p>", unsafe_allow_html=True)
        st.write('<a style="background-color: #2C3E50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;" href="'+link+'" target="_blank">Read more</a>', unsafe_allow_html=True)
        st.write("---")
else:
    st.warning("No news found for the selected category/source.")

import requests
from bs4 import BeautifulSoup
import streamlit as st

@st.cache_data(ttl=3600)
def scrape_news(url):

    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    paragraphs = soup.find_all("p")

    text = " ".join([p.get_text() for p in paragraphs])

    return text
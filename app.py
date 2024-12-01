from flask import Flask, render_template, request, redirect, url_for
from ollama import Client
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
import markdown

app = Flask(__name__)

def fetch_page_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def scrape_content(soup):
    title = soup.title.string if soup.title else "No title found"
    paragraphs = ' '.join([p.get_text().strip() for p in soup.find_all('p')])
    headings = [header.get_text().strip() for header in soup.find_all(['h1', 'h2', 'h3'])]
    return {
        "title": title,
        "paragraphs": paragraphs,
        "headings": headings
    }

def get_internal_links(soup, base_url):
    internal_links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(base_url, href)
        if is_internal_link(full_url, base_url):
            internal_links.add(full_url)
    return internal_links

def is_internal_link(url, base_url):
    base_domain = urlparse(base_url).netloc
    link_domain = urlparse(url).netloc
    return base_domain == link_domain

def clean_text(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'© \d{4}.*?(?=\s|$)', '', text)
    text = re.sub(r'(?i)privacy policy|terms of use|cookie policy', '', text)
    return text.strip()

def format_content_for_llm(page_data):
    title = clean_text(page_data['title'])
    headings = [clean_text(h) for h in page_data['headings']]
    paragraphs = clean_text(page_data['paragraphs'])
    
    formatted_text = f"""
    Company Website Analysis:
    Title: {title}

    Key Sections:
    {' | '.join(headings)}

    Detailed Content:
    {paragraphs[:3000]}  # Limit content length to avoid token limits
    """
    return formatted_text

def generate_summary(client, content, model_name="llama3.2"):
    prompt = f"""You are an expert business analyst. Based on this website content, create a useful and insightful summary:
    Content:
    {content}
    """
    try:
        # Get the response from Ollama
        response = client.generate(model=model_name, prompt=prompt, options={"temperature": 0.7})
        
        # Extract just the message content
        if hasattr(response, 'response'):
            summary_text = response.response
        elif isinstance(response, dict) and 'response' in response:
            summary_text = response['response']
        else:
            # If we can't find the response in the expected places, try to convert to string
            summary_text = str(response)
            # Extract just the response content if it's in the full string
            match = re.search(r'response="([^"]+)"', summary_text)
            if match:
                summary_text = match.group(1)
        
        # Clean up any escape characters
        summary_text = summary_text.replace('\\n', '\n').replace('\\t', '\t')
        
        # Convert markdown to HTML
        html_summary = markdown.markdown(summary_text)
        return html_summary
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def crawl_and_analyze(url, max_pages=5):
    client = Client()
    crawled_urls = set()
    to_crawl = {url}
    all_data = []

    while to_crawl and len(crawled_urls) < max_pages:
        current_url = to_crawl.pop()
        if current_url in crawled_urls:
            continue

        soup = fetch_page_content(current_url)
        if not soup:
            continue

        page_data = scrape_content(soup)
        all_data.append(page_data)
        
        internal_links = get_internal_links(soup, url)
        to_crawl.update(internal_links)
        crawled_urls.add(current_url)
        time.sleep(1)
    
    combined_content = ""
    for page_data in all_data:
        combined_content += format_content_for_llm(page_data)
    
    return generate_summary(client, combined_content)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        if url:
            summary = crawl_and_analyze(url)
            return render_template('result.html', summary=summary)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import sys
from collections import deque

class WebCrawler:
    def __init__(self, seed_urls, output_dir="downloaded_pages", index_file="index.txt"):
        self.seed_urls = seed_urls
        self.output_dir = output_dir
        self.index_file = index_file
        self.visited_urls = set()
        self.documents = []
        self.url_queue = deque(seed_urls)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(index_file, 'w', encoding='utf-8') as f:
            f.write("")

    def is_russian_page(self, text):
        russian_pattern = re.compile(r'[а-яА-ЯёЁ]')
        russian_chars = russian_pattern.findall(text)
        total_chars = len(re.findall(r'[a-zA-Zа-яА-ЯёЁ]', text))
        if total_chars == 0:
            return False

        return len(russian_chars) / total_chars > 0.5

    def count_words(self, text):
        words = re.findall(r'\b[а-яА-ЯёЁa-zA-Z]+\b', text)
        return len(words)

    def extract_text_from_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')

        for script in soup(["script", "style", "meta", "link"]):
            script.decompose()

        text = soup.get_text()

        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def extract_links(self, html_content, base_url):
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []

        for link in soup.find_all('a', href=True):
            absolute_url = urljoin(base_url, link['href'])

            parsed_url = urlparse(absolute_url)

            if parsed_url.scheme in ['http', 'https']:
                if not any(ext in parsed_url.path.lower() for ext in
                           ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.mp3', '.mp4']):
                    if parsed_url.fragment == '':
                        links.append(absolute_url)

        return links

    def download_page(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding

            return response.text
        except Exception as e:
            print(f"Ошибка при загрузке {url}: {str(e)}")
            return None

    def save_page(self, doc_num, url, text):
        filename = f"{doc_num:04d}.txt"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)

        with open(self.index_file, 'a', encoding='utf-8') as f:
            f.write(f"{doc_num}\t{url}\n")

        self.documents.append((doc_num, url))
        print(f"Сохранен документ #{doc_num}: {url}")

        return True

    def crawl(self, max_documents=100, min_words=1000):
        doc_counter = 0

        while self.url_queue and doc_counter < max_documents:
            url = self.url_queue.popleft()

            if url in self.visited_urls:
                continue

            print(f"Обработка URL: {url}")
            self.visited_urls.add(url)

            html_content = self.download_page(url)
            if not html_content:
                continue

            text = self.extract_text_from_html(html_content)
            if not self.is_russian_page(text):
                print(f"Страница {url} не содержит достаточного количества русского текста")
                continue

            word_count = self.count_words(text)
            if word_count < min_words:
                print(f"Страница {url} содержит недостаточно слов ({word_count} < {min_words})")
                continue

            doc_counter += 1
            self.save_page(doc_counter, url, text)

            links = self.extract_links(html_content, url)
            for link in links:
                if link not in self.visited_urls and link not in self.url_queue:
                    self.url_queue.append(link)

            time.sleep(1)

        print(f"\nСкачано {doc_counter} страниц")
        return doc_counter


def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    seed_urls = sys.argv[1:]
    crawler = WebCrawler(seed_urls)
    downloaded = crawler.crawl(max_documents=100, min_words=1000)

if __name__ == "__main__":
    main()
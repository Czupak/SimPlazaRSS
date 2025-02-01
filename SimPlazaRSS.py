from dataclasses import dataclass

import html
import requests
from bs4 import BeautifulSoup
import datetime as dt
from rfeed import *


@dataclass
class Article:
    title: str
    magnet: str
    url: str
    image: str = ""
    description: str = ""
    pub_date: dt.datetime = dt.datetime.now()

    @property
    def rss_description(self):
        rss_desc = f"{self.image}\n<pre>{self.description}</pre>"
        return rss_desc


class Articles:
    def __init__(self):
        self.articles = []

    def _add_article(self, article: Article) -> None:
        self.articles.append(article)

    def add_article(self, title, magnet, url, image="", description="", pub_date=dt.datetime.now()) -> Article:
        new_art = Article(title, magnet, url, image, description, pub_date)
        self.articles.append(new_art)
        return new_art

    def get_articles(self) -> list:
        return self.articles


class SimPlazaRSS:
    def __init__(self):
        self.articles = Articles()
        self.urls = []
        self.read_config()
        self.read_cache()
        self.run()

    def read_config(self):
        pass

    def read_cache(self):
        pass

    def get_latest_posts(self):
        url = "https://simplaza.org/"
        post_links = []
        # TODO: pages
        for i in range(1, 2):
            new_url = url
            if i > 1:
                new_url = f"{url}page/{i}"
            print(f"Fetching {new_url}")
            response = requests.get(new_url)
            if response.status_code != 200:
                print("Failed to fetch the website")
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all("article")

            for article in articles:
                link = article.find("a", href=True)
                if link:
                    post_links.append(link["href"])

        return post_links

    def get_post_soup(self, post_url):
        response = requests.get(post_url)
        if response.status_code != 200:
            print(f"Failed to fetch post page: {post_url}")
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        return soup

    def parse_post_soup(self, soup):

        headers = soup.find_all('h1')
        header = None
        for h1 in headers:
            if h1['class'] == ['title', 'entry-title']:
                header = html.escape(h1.string)
                break

        divs = soup.find_all("div")
        desc = None
        for div in divs:
            try:
                if div['class'] == ['su-spoiler-content', 'su-u-clearfix', 'su-u-trim']:
                    desc = div.get_text()
                    break
            except:
                pass

        time_tags = soup.find_all("time")
        created = None
        for tag in time_tags:
            if tag['class'] == ['entry-date', 'published']:
                created = tag['datetime']
                break

        images = soup.find_all("img")
        image = None
        for tag in images:
            try:
                if tag['class'] == ['aligncenter', 'size-large', 'wp-image-58']:
                    image = tag['src']
                    break
            except:
                pass

        download_links = soup.find_all("a", href=True, string="Download")
        for link in download_links:
            if "torrent" in link["href"]:
                return [link["href"], header, desc, created, image]

        return [None, header, desc, created, image]

    def get_magnet_link(self, download_url):
        response = requests.get(download_url)
        if response.status_code != 200:
            print(f"Failed to fetch download page: {download_url}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        magnet_link = soup.find("a", string="Open Magnet Link", href=True)

        if magnet_link:
            return magnet_link["href"]

        return None

    def generate_rss_feed(self, articles: list):
        items = []
        for art in articles:
            article = art.magnet
            header = art.title
            desc = art.description
            created = art.pub_date
            image = art.image
            url = art.url
            items.append(Item(
                title=header,
                link=article,
                description=f"<img src='{image}'/>\n<br/><a href='{url}'>{url}</a><br/>\n<pre>{desc}</pre>",
                # author="Santiago L. Valdarrama",
                # guid=Guid("http://www.example.com/articles/2"),
                pubDate=dt.datetime.fromisoformat(created)
            )
            )

        feed = Feed(
            title="Simplaza.org RSS Feed",
            link="localhost",
            description="by Czupak",
            language="en-US",
            lastBuildDate=dt.datetime.now(),
            items=items)
        return feed.rss()

    def run(self):
        print("Checking for new posts...")
        new_posts = self.get_latest_posts()
        for post in new_posts:
            if post not in self.urls:
                self.urls.append(post)
                post_soup = self.get_post_soup(post)
                if post_soup is not None:
                    [download_link, header, desc, created, image] = self.parse_post_soup(post_soup)
                    if download_link:
                        magnet_link = self.get_magnet_link(download_link)
                        if magnet_link:
                            print(f"{header=} {created=} {image=}")
                            print("Magnet Link Found:", magnet_link)
                            art = self.articles.add_article(header, magnet_link, post, image, desc, created)
        print('Preparing RSS...')
        rss = self.generate_rss_feed(self.articles.get_articles())
        print('Preparing index.html...')
        with open('index.html', 'w', encoding="UTF-8") as fh:
            fh.write(rss)
        print("All done!")


if __name__ == "__main__":
    SimPlazaRSS()

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
    def __init__(self, site='SceneryAddons.org'):
        self.site = site
        self.max_pages = 2
        self.articles = Articles()
        self.urls = []
        self.config = self.read_config()
        self.read_cache()
        self.run()

    def read_config(self):
        configs = {
            'SimPlaza.org': {
                'base_url': 'https://simplaza.org',
                'title': ['title', 'entry-title'],
                'desc': ['su-spoiler-content', 'su-u-clearfix', 'su-u-trim'],
                'created': ['entry-date', 'published'],
                'img': ['aligncenter', 'size-large', 'wp-image-58']
            },
            'SceneryAddons.org': {
                'base_url': 'https://sceneryaddons.org',
                'title': ['title', 'entry-title'],
                'desc': ['scad-description'],
                'created': ['entry-date', 'published'],
                'img': ['aligncenter']
            }
        }

        return configs[self.site]

    def read_cache(self):
        pass

    def get_latest_posts(self):
        post_links = []
        for i in range(1, self.max_pages + 1):
            new_url = self.config['base_url']
            if i > 1:
                new_url = f"{self.config['base_url']}/page/{i}"
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
        config = self.config
        headers = soup.find_all('h1')
        header = None
        for h1 in headers:
            if h1['class'] == config['title']:
                if h1.string is None:
                    header = html.escape(h1.text)
                else:
                    header = html.escape(h1.string)
                break

        divs = soup.find_all("div")
        desc = None
        for div in divs:
            try:
                if div['class'] == config['desc']:
                    desc = div.get_text()
                    break
            except:
                pass

        time_tags = soup.find_all("time")
        created = None
        for tag in time_tags:
            if tag['class'] == config['created']:
                created = tag['datetime']
                break

        images = soup.find_all("img")
        image = None
        for tag in images:
            try:
                if tag['class'] == config['img']:
                    image = tag['src']
                    break
            except:
                pass

        download_links = soup.find_all("a", href=True)
        for link in download_links:
            if "hoster=torrent" in link["href"]:
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
            title=f"{self.site} RSS Feed",
            link="localhost",
            description="by Czupak",
            language="en-US",
            lastBuildDate=dt.datetime.now(),
            items=items)
        return feed.rss()

    def run(self):
        print("Checking for new posts...")
        new_posts = self.get_latest_posts()

        for i in range(len(new_posts)):
            post = new_posts[i]
            if post not in self.urls:
                self.urls.append(post)
                post_soup = self.get_post_soup(post)
                if post_soup is not None:
                    [download_link, header, desc, created, image] = self.parse_post_soup(post_soup)
                    if download_link:
                        magnet_link = self.get_magnet_link(download_link)
                        if magnet_link:
                            print(f"{i + 1}/{len(new_posts)}: {header=} {created=} {image=}")
                            print("Magnet Link Found:", magnet_link)
                            art = self.articles.add_article(header, magnet_link, post, image, desc, created)
        print('Preparing RSS...')
        rss = self.generate_rss_feed(self.articles.get_articles())
        print(f'Preparing {self.site}.html...')
        with open(f'{self.site}.html', 'w', encoding="UTF-8") as fh:
            fh.write(rss)
        print("All done!")


if __name__ == "__main__":
    SimPlazaRSS(site='SceneryAddons.org')
    SimPlazaRSS(site='SimPlaza.org')

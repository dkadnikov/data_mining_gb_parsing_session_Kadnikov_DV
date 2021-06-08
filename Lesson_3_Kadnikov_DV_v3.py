import time
import typing
import datetime
import requests
from urllib.parse import urljoin
import bs4

from Lesson_3_database.Lesson_3_database import Database


class GbBlogParse:
    def __init__(self, start_url, db):
        self.time = time.time()
        self.start_url = start_url
        self.db = db
        self.done_urls = set()
        self.tasks = []
        start_task = self.get_task(self.start_url, self.parse_feed)
        self.tasks.append(start_task)
        self.done_urls.add(self.start_url)

    def _get_response(self, url, *args, **kwargs):
        if self.time + 0.9 < time.time():
            time.sleep(0.5)
        response = requests.get(url, *args, **kwargs)
        self.time = time.time()
        print(url)
        return response

    def _get_soup(self, url, *args, **kwargs):
        soup = bs4.BeautifulSoup(self._get_response(url, *args, **kwargs).text, "lxml")
        return soup

    def get_task(self, url: str, callback: typing.Callable) -> typing.Callable:
        def task():
            soup = self._get_soup(url)
            return callback(url, soup)

        if url in self.done_urls:
            return lambda *_, **__: None
        self.done_urls.add(url)
        return task

    def task_creator(self, url, tags_list, callback):
        links = set(
            urljoin(url, itm.attrs.get("href")) for itm in tags_list if itm.attrs.get("href")
        )
        for link in links:
            task = self.get_task(link, callback)
            self.tasks.append(task)

    def parse_feed(self, url, soup):
        ul_pagination = soup.find("ul", attrs={"class": "gb__pagination"})
        self.task_creator(url, ul_pagination.find_all("a"), self.parse_feed)
        post_wrapper = soup.find("div", attrs={"class": "post-items-wrapper"})
        self.task_creator(
            url, post_wrapper.find_all("a", attrs={"class": "post-item__title"}), self.parse_post
        )

    def parse_post(self, url, soup):
        author_tag = soup.find("div", attrs={"itemprop": "author"})

        first_img = soup.find("div", attrs={"class": "blogpost-content"}).find("img")
        if first_img:  # Попались статьи без картинок
            first_img_link = first_img.attrs.get("src")
        else:
            first_img_link = None

        date_published = soup.find("div", attrs={"class": "blogpost-date-views"}).find("time").attrs.get("datetime")
        date_obj = datetime.datetime.strptime(date_published, '%Y-%m-%dT%H:%M:%S%z')

        data = {
            "post_data": {
                "title": soup.find("h1", attrs={"class": "blogpost-title"}).text,
                "url": url,
                "id": soup.find("comments").attrs.get("commentable-id"),
                "img_url": first_img_link,
                "date_published": date_obj,
            },
            "author_data": {
                "url": urljoin(url, author_tag.parent.attrs.get("href")),
                "name": author_tag.text,
            },
            "tags_data": [
                {"name": tag.text, "url": urljoin(url, tag.attrs.get("href"))}
                for tag in soup.find_all("a", attrs={"class": "small"})
            ],
            "comments_data": self._get_comments(soup.find("comments").attrs.get("commentable-id")),
        }
        return data

    def _get_comments(self, post_id):
        api_path = f"/api/v2/comments?commentable_type=Post&commentable_id={post_id}&order=desc"
        response = self._get_response(urljoin(self.start_url, api_path))
        data = response.json()
        data = self._restructure_comments(data, post_id)
        return data

    def _restructure_comments(self, data, post_id):
        comment_keys = ('id', 'parent_id', 'body', 'created_at')
        result = []
        for itm in data:
            tmp_dict = {}
            for param in comment_keys:
                tmp_dict.update({param: itm["comment"][param]})
            tmp_dict.update({"post_id": post_id})
            tmp_dict.update({"author_of_comment": itm["comment"]["user"]['full_name']})
            # Убрал миллисекунды из 'created_at', формат '%Y-%m-%dT%H:%M:%S.%f%z' выдавал ошибку
            tmp_dict['created_at'] = tmp_dict['created_at'][:19] + tmp_dict['created_at'][23:]
            tmp_dict['created_at'] = datetime.datetime.strptime(tmp_dict['created_at'], '%Y-%m-%dT%H:%M:%S%z')
            result.append(tmp_dict)
            if itm["comment"]["children"]:
                for child in self._restructure_comments(itm["comment"]["children"], post_id):
                    result.append(child)
        return result

    def run(self):
        for task in self.tasks:
            task_result = task()
            if isinstance(task_result, dict):
                self.save(task_result)

    def save(self, data):
        self.db.add_post(data)


if __name__ == "__main__":
    # collection = MongoClient()["gb_parse_20_04"]["gb_blog"]
    db = Database("sqlite:///gb_blog.db")
    parser = GbBlogParse("https://gb.ru/posts", db)
    parser.run()
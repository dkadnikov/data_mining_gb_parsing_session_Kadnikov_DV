# import necessary packages
import json
import time
from pathlib import Path
import requests


# create class Parse5ka
class Parse5ka:
    # parameters & headers
    params = {
        'records_per_page': 200,
        'page': 1,
        'categories': None
    }
    headers = {
        "User-Agent": "Kielbasa Filippa",
        "Accept-Language": "en-US,en;q=0.5",
    }

    # params = {"records_per_page": 30, "page": 1, "categories": None}
    # define init
    def __init__(self, new_url_products, new_url_categories, new_save_path: Path):
        self.new_url_products = new_url_products
        self.new_url_categories = new_url_categories
        self.new_save_path = new_save_path

    # define _get_response
    @staticmethod
    def _get_response(url, *args, **kwargs):
        while True:
            response = requests.get(url, *args, **kwargs)
            if response.status_code == 200:
                print(f'Start new request: {response.url}')
                return response
            time.sleep(2)

    # define run
    def run(self):
        try:
            for category in self._get_response(self.new_url_categories, headers=self.headers).json():
                products = []
                for product in self._parse(self.new_url_products, category["parent_group_code"]):
                    products.append(product)
                file_path = self.new_save_path.joinpath(f'{category["parent_group_name"]}.json')
                self._save(category, products, file_path)
                print(f'Return: {category["parent_group_name"]}')
        except Exception as e:
            print(e)

    # define _parse
    def _parse(self, url, categories):
        self.params["categories"] = categories
        page = 1
        self.params["page"] = page
        while url:
            time.sleep(0.1)
            data = self._get_response(url, headers=self.headers, params=self.params).json()
            page += 1
            self.params["page"] = page
            url = url.replace("monolith", "5ka.ru") if data["next"] else None
            for product in data["results"]:
                yield product

    # define _save
    @staticmethod
    def _save(category, products, file_path):
        data = dict()
        data["name"] = category["parent_group_name"]
        data["code"] = category["parent_group_code"]
        data["products"] = products
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


# define _get_save_path
def get_save_path(dir_name):
    new_save_path = Path(__file__).parent.joinpath(dir_name)
    if not new_save_path.exists():
        new_save_path.mkdir()
    return new_save_path


# do the run
if __name__ == "__main__":
    save_path = get_save_path("products")
    url_products = "https://5ka.ru/api/v2/special_offers/"
    url_categories = "https://5ka.ru/api/v2/categories/"
    parser = Parse5ka(url_products, url_categories, save_path)
    parser.run()
    print("Congratulations! Mining process finished!")

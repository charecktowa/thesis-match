import re
import requests
from bs4 import BeautifulSoup


def get_soup(url) -> BeautifulSoup:
    response = requests.get(url)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.content, "html.parser")
    return soup


def extraer_id(url):
    # input www.enlace.com/algo/alg/13127
    # extraer el último siempre que sean números
    match = re.search(r"(\d+)$", url)
    if match:
        return int(match.group(1))
    return None


def save_to_file(data) -> None:
    with open("output.html", "w", encoding="utf-8") as file:
        file.write(data.prettify())

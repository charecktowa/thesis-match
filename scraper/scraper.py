import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = f"https://www.saber.cic.ipn.mx/"
URL_TEMPLATE = BASE_URL + "/SABERv3/alumnos/webAlumnos/{status}/{program}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def parse_table_rows(soup: BeautifulSoup):
    table = soup.select_one(".middleTable")
    if not table:
        return []

    rows = []
    for tr in table.select("tr"):
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue

        no_ = tds[0].get_text(strip=True)

        a_alumno = tds[1].find("a")
        nombre = (
            a_alumno.get_text(strip=True) if a_alumno else tds[1].get_text(strip=True)
        )
        url_alumno = (
            urljoin(BASE_URL, a_alumno["href"])
            if a_alumno and a_alumno.has_attr("href")
            else ""
        )

        a_tesis = tds[2].find("a")
        tesis = a_tesis.get_text(strip=True) if a_tesis else tds[2].get_text(strip=True)
        url_tesis = (
            urljoin(BASE_URL, a_tesis["href"])
            if a_tesis and a_tesis.has_attr("href")
            else ""
        )

        rows.append(
            {
                "No": no_,
                "Nombre": nombre,
                "URL_Alumno": url_alumno,
                "Tesis": tesis,
                "URL_Tesis": url_tesis,
            }
        )
    return rows


def get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return BeautifulSoup(response.text, "html.parser")


def parse_table_rows(soup: BeautifulSoup, program: int, status: int):
    table = soup.select_one(".middleTable")
    if not table:
        return []

    rows = []
    for tr in table.select("tr"):
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue

        no_ = tds[0].get_text(strip=True)

        a_alumno = tds[1].find("a")
        nombre = (
            a_alumno.get_text(strip=True) if a_alumno else tds[1].get_text(strip=True)
        )
        url_alumno = (
            urljoin(BASE_URL, a_alumno["href"])
            if a_alumno and a_alumno.has_attr("href")
            else ""
        )

        a_tesis = tds[2].find("a")
        tesis = a_tesis.get_text(strip=True) if a_tesis else tds[2].get_text(strip=True)
        url_tesis = (
            urljoin(BASE_URL, a_tesis["href"])
            if a_tesis and a_tesis.has_attr("href")
            else ""
        )

        rows.append(
            {
                "No": no_,
                "Nombre": nombre,
                "URL_Alumno": url_alumno,
                "Tesis": tesis,
                "URL_Tesis": url_tesis,
                "Programa": program,
                "Estatus": status,
            }
        )
    return rows


def prepare_data(students_table):
    # Here you can transform the data as needed before saving to the database
    if not students_table:
        print("No data found.")
        return students_table

    # Transform the data as needed
    for student in students_table:
        student["Nombre"] = student["Nombre"].title()
        student["Tesis"] = student["Tesis"].title()
        student["No"] = int(student["No"]) if student["No"].isdigit() else None
        student["Programa"] = int(student["Programa"])
        student["Estatus"] = int(student["Estatus"])
        student["URL_Alumno"] = student["URL_Alumno"].strip()
        student["URL_Tesis"] = student["URL_Tesis"].strip()

    return students_table


def main():
    program = 1  # MCC
    status = 1  # Graduados
    url = URL_TEMPLATE.format(status=status, program=program)
    soup = get_soup(url)
    students_table = parse_table_rows(soup, program, status)

    # Save into database (PostgreSQL) thorugh sqlalchemy
    students_table = prepare_data(students_table)


if __name__ == "__main__":
    main()

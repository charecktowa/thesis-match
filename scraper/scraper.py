import requests
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup



BASE_URL = "https://www.cic.ipn.mx/"

# Aquí encontramos todos los laboratorios
TARGET_URL = "https://www.cic.ipn.mx/index.php/comunidad-menu/labscic"


def get_soup(url):
    response = requests.get(url)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.content, "html.parser")
    return soup


def save_to_file(data):
    with open("output.html", "w", encoding="utf-8") as file:
        file.write(data.prettify())


def extraer_laboratorios(url):
    soup = get_soup(url)
    links = soup.find_all("a", href=True)
    acerca_links = [link for link in links if "acerca-de-" in link["href"]]
    full_url = [urljoin(BASE_URL, link["href"]) for link in acerca_links]
    return full_url


def extraer_enlace_miembros(url):
    soup = get_soup(url)

    links = soup.find_all("a", class_="accordeonck", href=True)
    miembros_links = [
        link
        for link in links
        # Hay una sola página con un typo
        if "profesores-" in link["href"]
        or "alumnos-" in link["href"]
        or "alunmos-" in link["href"]
    ]

    return [urljoin(BASE_URL, link["href"]) for link in miembros_links]


def extraer_informacion_investigadores(url):
    soup = get_soup(url)
    investigadores = []

    for bloque in soup.select(".sppb-addon-image-layout-wrap"):
        # Enlace a página personal
        pagina_elem = bloque.select_one(".sppb-addon-image-layout-image a")
        pagina_url = urljoin(BASE_URL, pagina_elem["href"]) if pagina_elem else ""

        # Nombre y puesto
        nombre_elem = bloque.select_one("h3.sppb-image-layout-title")
        partes = list(nombre_elem.stripped_strings) if nombre_elem else []
        nombre = partes[0] if partes else ""

        # Buscar puesto (en h3 o en párrafo aparte)
        if len(partes) > 1:
            puesto = partes[1]
        else:
            puesto_elem = bloque.select_one(".sppb-addon-image-layout-text span")
            puesto = puesto_elem.get_text(strip=True) if puesto_elem else ""

        # Correo
        correo_elem = bloque.select_one('a[href^="mailto:"]')
        correo = correo_elem.get_text(strip=True) if correo_elem else ""

        # Laboratorio

        investigadores.append(
            {"nombre": nombre, "puesto": puesto, "correo": correo, "pagina": pagina_url}
        )

    return investigadores


def extraer_id_y_laboratorio(url):
    soup = get_soup(url)

    save_to_file(soup)

    # Buscar cualquier iframe con src que contenga "saber"
    iframe = soup.find("iframe", src=re.compile(r"saber", re.I))

    _id = None
    if iframe and "src" in iframe.attrs:
        match = re.search(r"(\d{1,})$", iframe["src"])
        if match:
            _id = int(match.group(1))

    # Buscar el único texto que diga "Laboratorio de XXXX" y añadirlo
    laboratorio_elem = soup.find(string=re.compile(r"Laboratorio de", re.I))
    if laboratorio_elem:
        laboratorio = laboratorio_elem.strip()
    else:
        laboratorio = None

    return _id, laboratorio


def extraer_investigadores(profesores):
    investigadores = extraer_informacion_investigadores(profesores)

    for investigador in investigadores:
        investigador_id, lab = extraer_id_y_laboratorio(investigador["pagina"])

        if not investigador_id and not lab:
            investigador["id"] = None
            investigador["laboratorio"] = None
        else:
            investigador["id"] = investigador_id
            investigador["laboratorio"] = lab

    return investigadores


def extraer_alumnos_url(url):
    print(f"Extrayendo información de: {url}")
    soup = get_soup(url)

    # Buscar iframe con "saber" en el src
    iframe = soup.find("iframe", src=re.compile(r"saber", re.I))

    if not (iframe and "src" in iframe.attrs):
        return None

    url = iframe["src"]

    return url


def extraer_metadatos(url):
    """
    Extrae metadatos de laboratorio.

    Del laboratorio podemos extraer la información de qué investigadores
    forman parte del laboratorio, por otra parte, la información de
    los alumnos (activos) del laboratorio se encuentra en SABER
    y todos los demás tanto de investigadores como de alumnos se encuentra en
    SABER, esta función y como todo en este archivo, se centra en la página
    del CIC, por lo que todo lo de SABER se encuentra en el archivo scraper_saber.py

    :param url: URL del laboratorio

    :return: Tupla con lista de profesores y enlace de alumnos (miembros lab)
    """

    profesores, alumnos = extraer_enlace_miembros(url)
    profesores = extraer_investigadores(profesores)
    alumnos = extraer_alumnos_url(alumnos)

    return profesores, alumnos


def main():
    laboratorios = extraer_laboratorios(TARGET_URL)

    for laboratorio in laboratorios:
        print("==============================================\n")
        print(f"Extrayendo metadatos de: {laboratorio}")
        lab_info = extraer_metadatos(laboratorio)

        profesores, alumnos = lab_info

        # Guardar 


if __name__ == "__main__":
    main()

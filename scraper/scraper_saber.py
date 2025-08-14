"""
Since www.cic.ipn.mx contains certain information
that it is obtained from their own database (saber)
this scraper is designed to extract information specifically
from www.saber.cic.ipn.mx
"""

from urllib.parse import urljoin
from bs4 import BeautifulSoup

from utils import get_soup, extraer_id, save_to_file
from db_handler import init_db, get_all_labs_id, save_student_data

BASE_URL = "https://www.saber.cic.ipn.mx/SABERv3/"
LAB_STUDENTS_URL = BASE_URL + "laboratorios/webLaboratorioAlumnos/"  # + id


def extraer_informacion_estudiantes(url: str):
    soup = get_soup(url)

    estudiantes = []

    for bloque in soup.select(".container-item.module.variant-person"):
        # Enlace a página personal
        enlace = bloque.select_one(".module-content a")
        href = enlace["href"].strip() if enlace and enlace.has_attr("href") else ""
        pagina_url = urljoin(BASE_URL, href) if href else ""

        # ID (de los últimos 4 dígitos de href)
        estudiante_id = extraer_id(href) if href else None

        # Nombre
        nombre_elem = bloque.select_one(".module-title")
        nombre = nombre_elem.get_text(strip=True) if nombre_elem else None

        # Correo
        correo_elem = bloque.select_one(".module-subtitle")
        correo = correo_elem.get_text(strip=True) if correo_elem else ""

        estudiantes.append(
            {
                "id": estudiante_id,
                "nombre": nombre,
                "correo": correo,
                "pagina": pagina_url,
            }
        )

    return estudiantes


def extraer_alumnos(laboratorio: str):
    alumnos = extraer_informacion_estudiantes(laboratorio)

    for alumno in alumnos:
        id_lab = extraer_id(laboratorio)

        if not id_lab:
            alumno["id_laboratorio"] = None
        else:
            alumno["id_laboratorio"] = id_lab

    return alumnos


def extraer_metadatos(laboratorio: str):
    alumnos = extraer_alumnos(laboratorio)
    return alumnos


def main():
    # Inicializar base de datos
    init_db()

    labs_id = get_all_labs_id()
    print(f"Found {len(labs_id)} laboratories to process")

    total_alumnos = 0
    for lab_id in labs_id:
        url = LAB_STUDENTS_URL + str(lab_id)
        print("=========================================\n")
        print(f"Extrayendo alumnos de: {url}")

        try:
            alumnos = extraer_metadatos(url)
            print(f"Found {len(alumnos)} students in lab {lab_id}")

            if alumnos:
                # Guardar estudiantes en la base de datos
                save_student_data(alumnos, lab_id)
                total_alumnos += len(alumnos)

        except Exception as e:
            print(f"Error processing lab {lab_id}: {e}")
            continue

    print(f"Total de alumnos extraídos: {total_alumnos}")


if __name__ == "__main__":
    main()

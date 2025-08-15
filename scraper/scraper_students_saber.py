from sqlalchemy import null
from utils import get_soup, extraer_id, save_to_file

from db_handler import create_fake_laboratory, init_db, save_student_data

# Constantes más descriptivas
STUDENT_STATUS = {"graduated": 1, "enrolled": 2}  # egresados  # inscritos

PROGRAMS = {
    "mcc": 1,  # Maestría en Ciencias de la Computación
    "mcic": 2,  # Maestría en Ciencias en Ingeniería de Cómputo
    "dcc": 3,  # Doctorado en Ciencias de la Computación
}

BASE_URL = "https://www.saber.cic.ipn.mx/SABERv3/"


def build_student_url(status: int, program: int) -> str:
    """Construye la URL para consultar estudiantes por estatus y programa."""
    return f"{BASE_URL}alumnos/webAlumnos/{status}/{program}"


def get_all_combinations():
    """Genera todas las combinaciones de estatus y programas."""
    for status in STUDENT_STATUS.values():
        for program in PROGRAMS.values():
            yield status, program


def extraer_informacion_alumnos(url: str):
    soup = get_soup(url)

    alumnos = []

    for fila in soup.select("tr"):
        enlace_alumno = fila.select_one("td:nth-of-type(2) a")
        if not enlace_alumno or not enlace_alumno.has_attr("href"):
            continue

        href = enlace_alumno["href"].strip()
        # Remover la barra inicial para construir URL relativa
        url_relativa = href.lstrip("/")
        url_final = f"https://www.saber.cic.ipn.mx/{url_relativa}"

        alumno_id = extraer_id(href)

        nombre = enlace_alumno.get_text(strip=True)

        alumnos.append(
            {
                "id": alumno_id,
                "nombre": nombre,
                "correo": "",
                "pagina": url_final,
            }
        )

    return alumnos


def main():
    init_db()
    create_fake_laboratory()

    for status, program in get_all_combinations():
        url = build_student_url(status, program)
        print(f"Procesando: {url}")

        try:
            alumnos = extraer_informacion_alumnos(url)
            print(f"Found {len(alumnos)} students in {url}")

            if alumnos:
                # Ya que egresaron, no tienen laboratorio entonces ponemos 999
                save_student_data(alumnos, lab_id=999)

        except Exception as e:
            print(f"Error procesando {url}: {e}")


if __name__ == "__main__":
    main()

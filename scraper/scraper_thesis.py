from db_handler import init_db, get_all_professors_ids, save_multiple_theses
from utils import get_soup, extraer_id

# Constantes más descriptivas
STUDENT_STATUS = {"graduated": 1, "enrolled": 2}  # egresados  # inscritos

BASE_URL = "https://www.saber.cic.ipn.mx/SABERv3/"


def build_student_url(id: int, status: int) -> str:
    """Construye la URL para consultar tesis por id profesor y estatus."""
    return f"{BASE_URL}tesis/webLista3/{id}/{status}"


def extraer_datos_tesis(soup, id_profesor: int):
    """
    Extrae información de las tesis desde el HTML parseado

    Args:
        soup: BeautifulSoup object del HTML
        id_profesor: ID del profesor que está siendo consultado

    Returns:
        List[dict]: Lista de diccionarios con datos de tesis
    """
    tesis_data = []

    # Buscar todas las tablas con las características específicas
    tablas = soup.find_all("table", {"cellpadding": "0", "cellspacing": "0"})

    # La segunda tabla contiene las tesis (la primera contiene info del profesor)
    tabla_tesis = None
    for tabla in tablas:
        headers = tabla.find_all("th")
        if len(headers) >= 3:  # Debe tener columnas: No., Tesis, Alumno
            header_text = [th.get_text(strip=True) for th in headers]
            if (
                "No." in header_text
                and "Tesis" in header_text
                and "Alumno" in header_text
            ):
                tabla_tesis = tabla
                break

    if not tabla_tesis:
        return tesis_data

    # Buscar todas las filas de datos (saltando el header)
    filas = tabla_tesis.find_all("tr")[1:]  # Saltar el header

    for fila in filas:
        celdas = fila.find_all("td")
        if len(celdas) < 3:  # Debe tener al menos 3 celdas: No., Tesis, Alumno
            continue

        # Extraer título y enlace de la tesis
        celda_tesis = celdas[1]
        enlace_tesis = celda_tesis.find("a")
        if not enlace_tesis:
            continue

        titulo = enlace_tesis.get_text(strip=True)
        url_tesis = enlace_tesis.get("href", "")

        # Extraer ID de la tesis desde la URL
        id_tesis = extraer_id(url_tesis)
        if not id_tesis:
            continue

        # Extraer información del alumno
        celda_alumno = celdas[2]
        enlace_alumno = celda_alumno.find("a")
        if not enlace_alumno:
            continue

        url_alumno = enlace_alumno.get("href", "")
        id_alumno = extraer_id(url_alumno)
        if not id_alumno:
            continue

        # Extraer tipo de dirección (Director 1 o Director 2)
        texto_celda = celda_alumno.get_text()
        es_director_principal = "Director 1" in texto_celda

        tesis_info = {
            "id": id_tesis,
            "title": titulo,
            "student_id": id_alumno,
            "advisor1_id": id_profesor if es_director_principal else None,
            "advisor2_id": id_profesor if not es_director_principal else None,
        }

        tesis_data.append(tesis_info)

    return tesis_data


def extraer_tesis(url: str):
    """
    Extrae tesis de una URL específica

    Args:
        url: URL para hacer scraping

    Returns:
        List[dict]: Lista de tesis extraídas
    """
    soup = get_soup(url)

    # Extraer ID del profesor desde la URL
    id_profesor = int(url.split("/")[-2])

    # Extraer datos de las tesis
    tesis_data = extraer_datos_tesis(soup, id_profesor)

    print(f"Found {len(tesis_data)} theses for professor {id_profesor}")

    return tesis_data


def main():
    init_db()

    professors_ids = get_all_professors_ids()

    print(f"Processing theses for {len(professors_ids)} professors...")

    all_theses = []

    for professor_id in professors_ids:
        print(f"\nProcessing professor {professor_id}:")

        for status_name, status_value in STUDENT_STATUS.items():
            url = build_student_url(professor_id, status_value)
            print(f"  Extracting {status_name} theses from: {url}")

            try:
                theses = extraer_tesis(url)

                if theses:
                    all_theses.extend(theses)
                    print(f"    Found {len(theses)} theses")
                else:
                    print("    No theses found")

            except Exception as e:
                print(f"    Error processing {url}: {e}")

    # Guardar todas las tesis en la base de datos
    if all_theses:
        print(f"\nSaving {len(all_theses)} theses to database...")
        save_multiple_theses(all_theses)
        print("Theses saved successfully!")

        # Mostrar estadísticas finales
        from db_handler import get_thesis_stats

        get_thesis_stats()
    else:
        print("No theses found to save.")


if __name__ == "__main__":
    main()

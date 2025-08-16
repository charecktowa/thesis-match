from db_handler import (
    get_all_student_profile_urls,
    init_db,
    save_multiple_academic_programs,
    get_academic_program_stats,
)
from utils import get_soup, extraer_id, save_to_file

BASE_URL = "https://www.saber.cic.ipn.mx/SABERv3/"


def extraer_informacion_academica(url: str):
    soup = get_soup(url)
    estudios = []

    # Ubicar la tabla específica de "Estudios académicos"
    tabla = None
    for contenedor in soup.select(".middleTable"):
        caption = contenedor.find("caption")
        if caption and caption.get_text(strip=True).lower() == "estudios académicos":
            tabla = contenedor
            break

    if not tabla:
        return estudios

    # Soporta tablas con y sin <tbody>
    filas = tabla.find_all("tr")
    actual = None

    for tr in filas:
        celdas = tr.find_all("td")
        if not celdas:
            continue

        clases = celdas[0].get("class") or []

        # Filas útiles: primer <td> con class="texto" (etiqueta) y el segundo es el valor
        if "texto" in clases:
            etiqueta = celdas[0].get_text(strip=True).lower()
            valor_td = celdas[1] if len(celdas) > 1 else None

            if etiqueta == "programa":
                # Inicia un nuevo bloque
                if actual and any(actual.values()):
                    estudios.append(actual)
                actual = {
                    "programa": None,
                    "situacion": None,
                    "tesis": None,
                    "tesis_url": "",
                }
                actual["programa"] = valor_td.get_text(strip=True) if valor_td else None

            elif actual is not None and etiqueta in ("situación", "situacion"):
                actual["situacion"] = (
                    valor_td.get_text(strip=True) if valor_td else None
                )

            elif actual is not None and etiqueta == "tesis":
                tesis_texto = None
                tesis_url = ""
                if valor_td:
                    enlace = valor_td.find("a")
                    if enlace:
                        tesis_texto = enlace.get_text(strip=True)
                        href = (enlace.get("href") or "").strip()
                        if href:
                            # Si ya es absoluta, úsala tal cual; si es relativa, prefix al dominio
                            if href.startswith("http://") or href.startswith(
                                "https://"
                            ):
                                tesis_url = href
                            else:
                                tesis_url = (
                                    f"https://www.saber.cic.ipn.mx/SABERv3{href}"
                                )
                    else:
                        tesis_texto = valor_td.get_text(strip=True)
                actual["tesis"] = tesis_texto or None
                actual["tesis_url"] = tesis_url

    # Agregar el último bloque si existe
    if actual and any(actual.values()):
        estudios.append(actual)

    return estudios


def extraer_programas(url: str):
    programas = extraer_informacion_academica(url)

    # Convertir formato para ser compatible con la base de datos
    programas_formatted = []
    for programa in programas:
        # Mapear campos al formato esperado
        programa_formatted = {
            "programa": programa.get("programa"),
            "status": programa.get("situacion", "").lower(),  # normalizar status
            "tesis_titulo": programa.get("tesis"),
            "tesis_url": programa.get("tesis_url"),
        }

        # Normalizar valores de status
        if programa_formatted["status"] in ["activo", "vigente"]:
            programa_formatted["status"] = "inscrito"
        elif programa_formatted["status"] in ["titulado", "terminado"]:
            programa_formatted["status"] = "graduado"

        # Solo agregar si tiene programa válido
        if programa_formatted["programa"]:
            programas_formatted.append(programa_formatted)

    return programas_formatted


def extraer_metadatos(url: str):
    return extraer_programas(url)


def main() -> None:
    print("Starting academic program extraction")
    init_db()

    urls = get_all_student_profile_urls()
    print(f"Found {len(urls)} student profiles to process")

    processed = 0
    for url in urls:
        print(f"\n[{processed + 1}/{len(urls)}] Extrayendo metadatos de: {url}")

        try:
            # Extraer ID del estudiante de la URL
            student_id = extraer_id(url)
            if not student_id:
                print(f"   Could not extract student ID from URL: {url}")
                continue

            # Extraer información académica
            programas = extraer_metadatos(url)

            if programas:
                print(f"   Found {len(programas)} academic programs")
                # Guardar en la base de datos
                save_multiple_academic_programs(student_id, programas)
            else:
                print(f"   No academic programs found for student {student_id}")

            processed += 1

        except Exception as e:
            print(f"   Error processing {url}: {e}")
            continue

    print(f"\nProcessing completed: {processed}/{len(urls)} profiles processed")

    # Mostrar estadísticas finales
    get_academic_program_stats()


if __name__ == "__main__":
    main()

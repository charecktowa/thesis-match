from db_handler import (
    init_db,
    get_all_professors_ids,
    save_multiple_research_products,
    get_research_product_stats,
)
from utils import get_soup, save_to_file
from bs4 import Tag
import re

BASE_URL = "https://www.saber.cic.ipn.mx/SABERv3/"

# Tipos de productos: 1=artículos, 2=ponencias/conferencias
PRODUCT_TYPES = [1, 2]

PRODUCTS_URL = BASE_URL + "publicacions/webListaUsuario/{id}/{type}"


def extraer_titulo_de_celda(celda):
    """Extrae el título de una celda, ya sea de un enlace o texto directo"""
    try:
        enlace = celda.find("a")
        if enlace and hasattr(enlace, "get_text"):
            return enlace.get_text(strip=True)
        return celda.get_text(strip=True) if hasattr(celda, "get_text") else ""
    except Exception:
        return ""


def extraer_texto_de_celda(celda):
    """Extrae texto de una celda de forma segura"""
    try:
        return celda.get_text(strip=True) if hasattr(celda, "get_text") else ""
    except Exception:
        return ""


def extraer_ano_de_texto(texto):
    """Convierte texto a año entero"""
    try:
        return int(texto) if texto.isdigit() else None
    except (ValueError, TypeError):
        return None


def extraer_productos_investigacion(url: str):
    """
    Extrae productos de investigación de una página de SABER

    Args:
        url: URL de la página de productos del profesor

    Returns:
        Lista de diccionarios con información de productos
    """
    soup = get_soup(url)
    productos = []

    # Buscar todas las filas de tabla que contienen datos
    filas = soup.select("table tr")
    if len(filas) <= 1:
        return productos

    # Procesar cada fila (saltando headers)
    for fila in filas[1:]:
        celdas = fila.find_all("td")
        if len(celdas) < 3:
            continue

        titulo = extraer_titulo_de_celda(celdas[0])
        descripcion = extraer_texto_de_celda(celdas[1])
        año_texto = extraer_texto_de_celda(celdas[2])
        año = extraer_ano_de_texto(año_texto)

        # Solo agregar si tenemos datos válidos
        if titulo and descripcion and año:
            productos.append(
                {
                    "title": titulo,
                    "site": descripcion,
                    "year": año,
                }
            )

    return productos


def extraer_metadatos(profesor_id: int):
    """
    Extrae todos los productos de investigación de un profesor

    Args:
        profesor_id: ID del profesor en SABER

    Returns:
        Lista con todos los productos del profesor
    """
    productos_totales = []

    for tipo_producto in PRODUCT_TYPES:
        url = PRODUCTS_URL.format(id=profesor_id, type=tipo_producto)
        print(f"   Extrayendo tipo {tipo_producto} de: {url}")

        try:
            productos = extraer_productos_investigacion(url)
            productos_totales.extend(productos)
            print(f"   Found {len(productos)} products of type {tipo_producto}")
        except Exception as e:
            print(f"   Error extracting type {tipo_producto}: {e}")

    return productos_totales


def main():
    """Función principal del scraper de productos de investigación"""
    print("Starting research products extraction")
    init_db()

    prof_ids = get_all_professors_ids()
    print(f"Found {len(prof_ids)} professors to process")

    total_productos = 0
    processed = 0

    for prof_id in prof_ids:
        print(f"\n[{processed + 1}/{len(prof_ids)}] Processing professor {prof_id}")

        try:
            productos = extraer_metadatos(prof_id)

            if productos:
                print(f"   Found {len(productos)} total research products")
                # Guardar en la base de datos
                save_multiple_research_products(prof_id, productos)
                total_productos += len(productos)
            else:
                print(f"   No research products found for professor {prof_id}")

            processed += 1

        except Exception as e:
            print(f"   Error processing professor {prof_id}: {e}")
            continue

    print(f"\nProcessing completed: {processed}/{len(prof_ids)} professors processed")
    print(f"Total research products extracted: {total_productos}")

    # Mostrar estadísticas finales
    get_research_product_stats()


if __name__ == "__main__":
    main()

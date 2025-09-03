"""
Funciones CRUD específicas para el sistema de recomendaciones
"""

from http import HTTPStatus
import os
from time import sleep
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

import dashscope
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import text

from . import models, schemas

load_dotenv()

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/api/v1"


def clean_text(text: str) -> str:
    """Limpia y normaliza texto para generar embeddings"""
    # Normalize unicode
    text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
    # Trim
    text = text.strip()
    # Remove characters
    text = text.replace("\n", " ").replace("\r", " ")
    return text


def generate_query_embedding(query: str) -> list[float] | None:
    """
    Genera embedding para una consulta de texto usando Dashscope
    """
    try:
        cleaned_query = clean_text(query)

        resp = dashscope.TextEmbedding.call(
            model=dashscope.TextEmbedding.Models.text_embedding_v4,
            input=[cleaned_query],
            text_type="query",  # Indicamos que es una consulta
            dimension=1024,
        )

        if resp.status_code == HTTPStatus.OK:
            return resp.output["embeddings"][0]["embedding"]
        else:
            print(f"Error generating embedding for query: {resp.text}")
            return None

    except Exception as e:
        print(f"Exception during embedding generation: {e}")
        return None


def search_similar_theses_by_embedding(
    db: Session, embedding: list[float], k: int = 10
) -> list:
    """
    Busca las k tesis más similares usando similitud de coseno con pgvector
    """
    # Convertir el embedding a string para la consulta SQL
    embedding_str = f"[{','.join(map(str, embedding))}]"

    query = text(
        f"""
        SELECT 
            t.id,
            t.title,
            t.student_id,
            s.name as student_name,
            p1.name as advisor1_name,
            p2.name as advisor2_name,
            1 - (t.embedding <=> '{embedding_str}') as similarity_score
        FROM theses t
        JOIN students s ON t.student_id = s.id
        JOIN professors p1 ON t.advisor1_id = p1.id
        LEFT JOIN professors p2 ON t.advisor2_id = p2.id
        WHERE t.embedding IS NOT NULL
        ORDER BY t.embedding <=> '{embedding_str}'
        LIMIT {k}
    """
    )

    return db.execute(query).fetchall()


def search_similar_research_products_by_embedding(
    db: Session, embedding: list[float], k: int = 10
) -> list:
    """
    Busca los k productos de investigación más similares usando similitud de coseno con pgvector
    """
    # Convertir el embedding a string para la consulta SQL
    embedding_str = f"[{','.join(map(str, embedding))}]"

    query = text(
        f"""
        SELECT 
            rp.id,
            rp.title,
            rp.site,
            rp.year,
            rp.professor_id,
            p.name as professor_name,
            l.name as laboratory_name,
            1 - (rp.embedding <=> '{embedding_str}') as similarity_score
        FROM research_products rp
        JOIN professors p ON rp.professor_id = p.id
        JOIN laboratories l ON p.laboratory_id = l.id
        WHERE rp.embedding IS NOT NULL
        ORDER BY rp.embedding <=> '{embedding_str}'
        LIMIT {k}
    """
    )

    return db.execute(query).fetchall()


def get_thesis_by_id_with_embedding(db: Session, thesis_id: int):
    """Obtiene una tesis por ID incluyendo su embedding"""
    return (
        db.query(models.Thesis)
        .filter(models.Thesis.id == thesis_id, models.Thesis.embedding.is_not(None))
        .first()
    )


def get_research_product_by_id_with_embedding(db: Session, product_id: int):
    """Obtiene un producto de investigación por ID incluyendo su embedding"""
    return (
        db.query(models.ResearchProduct)
        .filter(
            models.ResearchProduct.id == product_id,
            models.ResearchProduct.embedding.is_not(None),
        )
        .first()
    )


def find_similar_items_by_id(
    db: Session,
    thesis_id: int | None = None,
    research_product_id: int | None = None,
    k: int = 10,
    search_type: str = "both",
) -> dict:
    """
    Encuentra elementos similares basándose en el ID de una tesis o producto de investigación
    """
    results = {"theses": [], "research_products": []}

    # Obtener el embedding del elemento de referencia
    reference_embedding = None

    if thesis_id:
        thesis = get_thesis_by_id_with_embedding(db, thesis_id)
        if thesis and thesis.embedding:
            reference_embedding = thesis.embedding
    elif research_product_id:
        product = get_research_product_by_id_with_embedding(db, research_product_id)
        if product and product.embedding:
            reference_embedding = product.embedding

    if not reference_embedding:
        return results

    # Buscar elementos similares
    if search_type in ["theses", "both"]:
        similar_theses = search_similar_theses_by_embedding(db, reference_embedding, k)
        # Filtrar el elemento de referencia si es una tesis
        if thesis_id:
            similar_theses = [t for t in similar_theses if t[0] != thesis_id]
        results["theses"] = similar_theses

    if search_type in ["research_products", "both"]:
        similar_products = search_similar_research_products_by_embedding(
            db, reference_embedding, k
        )
        # Filtrar el elemento de referencia si es un producto de investigación
        if research_product_id:
            similar_products = [
                p for p in similar_products if p[0] != research_product_id
            ]
        results["research_products"] = similar_products

    return results


def get_all_theses_with_embeddings(db: Session):
    """Obtiene todas las tesis que tienen embeddings para análisis de clusters"""
    return db.query(models.Thesis).filter(models.Thesis.embedding.is_not(None)).all()


def get_all_research_products_with_embeddings(
    db: Session, min_year: int | None = None, max_year: int | None = None
):
    """Obtiene todos los productos de investigación que tienen embeddings para análisis de clusters"""
    query = db.query(models.ResearchProduct).filter(
        models.ResearchProduct.embedding.is_not(None)
    )

    if min_year:
        query = query.filter(models.ResearchProduct.year >= min_year)
    if max_year:
        query = query.filter(models.ResearchProduct.year <= max_year)

    return query.all()


def perform_cluster_analysis(
    db: Session,
    entity_type: str,
    n_clusters: int = 5,
    min_year: int | None = None,
    max_year: int | None = None,
) -> dict:
    """
    Realiza análisis de clustering en tesis o productos de investigación
    """
    if entity_type == "theses":
        items = get_all_theses_with_embeddings(db)
        get_item_info = lambda item: {
            "id": item.id,
            "title": item.title,
            "student_name": item.student.name if item.student else None,
            "advisor1_name": item.advisor1.name if item.advisor1 else None,
            "advisor2_name": item.advisor2.name if item.advisor2 else None,
        }
    elif entity_type == "research_products":
        items = get_all_research_products_with_embeddings(db, min_year, max_year)
        get_item_info = lambda item: {
            "id": item.id,
            "title": item.title,
            "site": item.site,
            "year": item.year,
            "professor_name": item.professor.name if item.professor else None,
            "laboratory_name": (
                item.professor.laboratory.name
                if item.professor and item.professor.laboratory
                else None
            ),
        }
    else:
        raise ValueError("entity_type debe ser 'theses' o 'research_products'")

    if len(items) < n_clusters:
        raise ValueError(
            f"No hay suficientes elementos ({len(items)}) para crear {n_clusters} clusters"
        )

    # Extraer embeddings
    embeddings = [item.embedding for item in items]
    embeddings_array = np.array(embeddings)

    # Realizar clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(embeddings_array)

    # Organizar resultados por cluster
    clusters = []
    for cluster_id in range(n_clusters):
        cluster_items = [
            get_item_info(items[i])
            for i in range(len(items))
            if cluster_labels[i] == cluster_id
        ]

        clusters.append(
            {
                "cluster_id": cluster_id,
                "items": cluster_items,
                "cluster_center": kmeans.cluster_centers_[cluster_id].tolist(),
                "cluster_size": len(cluster_items),
            }
        )

    return {"entity_type": entity_type, "clusters": clusters, "total_items": len(items)}


def get_trending_research_topics(
    db: Session, years: list[int] | None = None, top_k: int = 10
) -> dict:
    """
    Analiza tendencias en temas de investigación por año
    """
    if not years:
        # Por defecto, últimos 5 años
        current_year = 2024  # Puedes ajustar esto dinámicamente
        years = list(range(current_year - 4, current_year + 1))

    trends = {}

    for year in years:
        products = get_all_research_products_with_embeddings(
            db, min_year=year, max_year=year
        )

        if len(products) >= 3:  # Mínimo para clustering
            try:
                n_clusters = min(5, len(products) // 2)  # Ajustar número de clusters
                cluster_result = perform_cluster_analysis(
                    db, "research_products", n_clusters, year, year
                )

                trends[year] = {
                    "total_products": len(products),
                    "clusters": cluster_result["clusters"][:top_k],  # Top clusters
                }
            except Exception as e:
                print(f"Error clustering for year {year}: {e}")
                trends[year] = {"total_products": len(products), "clusters": []}
        else:
            trends[year] = {"total_products": len(products), "clusters": []}

    return trends


def get_professor_research_similarity(
    db: Session, professor1_id: int, professor2_id: int
) -> dict:
    """
    Calcula la similitud entre la investigación de dos profesores
    """
    # Obtener productos de investigación de ambos profesores
    products1 = (
        db.query(models.ResearchProduct)
        .filter(
            models.ResearchProduct.professor_id == professor1_id,
            models.ResearchProduct.embedding.is_not(None),
        )
        .all()
    )

    products2 = (
        db.query(models.ResearchProduct)
        .filter(
            models.ResearchProduct.professor_id == professor2_id,
            models.ResearchProduct.embedding.is_not(None),
        )
        .all()
    )

    if not products1 or not products2:
        return {
            "similarity_score": 0.0,
            "common_topics": [],
            "message": "Uno o ambos profesores no tienen productos con embeddings",
        }

    # Calcular embedding promedio para cada profesor
    embeddings1 = np.array([p.embedding for p in products1])
    embeddings2 = np.array([p.embedding for p in products2])

    avg_embedding1 = np.mean(embeddings1, axis=0)
    avg_embedding2 = np.mean(embeddings2, axis=0)

    # Calcular similitud coseno
    dot_product = np.dot(avg_embedding1, avg_embedding2)
    norm1 = np.linalg.norm(avg_embedding1)
    norm2 = np.linalg.norm(avg_embedding2)

    similarity = dot_product / (norm1 * norm2)

    # Encontrar productos más similares entre ambos profesores
    common_topics = []
    for p1 in products1:
        for p2 in products2:
            p1_emb = np.array(p1.embedding)
            p2_emb = np.array(p2.embedding)

            topic_similarity = np.dot(p1_emb, p2_emb) / (
                np.linalg.norm(p1_emb) * np.linalg.norm(p2_emb)
            )

            if topic_similarity > 0.8:  # Umbral de alta similitud
                common_topics.append(
                    {
                        "product1": {"id": p1.id, "title": p1.title, "year": p1.year},
                        "product2": {"id": p2.id, "title": p2.title, "year": p2.year},
                        "similarity": float(topic_similarity),
                    }
                )

    return {
        "similarity_score": float(similarity),
        "common_topics": sorted(
            common_topics, key=lambda x: x["similarity"], reverse=True
        )[:5],
        "total_products": {"professor1": len(products1), "professor2": len(products2)},
    }

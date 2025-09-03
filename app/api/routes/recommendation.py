from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db import schemas
from app.db.database import SessionLocal
from app.db.crud_recommendations import (
    generate_query_embedding,
    search_similar_theses_by_embedding,
    search_similar_research_products_by_embedding,
    find_similar_items_by_id,
    perform_cluster_analysis,
    get_trending_research_topics,
    get_professor_research_similarity,
)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/recommend",
    response_model=schemas.RecommendationResponse,
    tags=["recommendations"],
)
async def get_recommendations(
    request: schemas.RecommendationRequest, db: Session = Depends(get_db)
):
    """
    Obtiene recomendaciones de tesis y productos de investigación basadas en una consulta de texto
    """
    # Generar embedding para la consulta
    query_embedding = generate_query_embedding(request.query)

    if not query_embedding:
        raise HTTPException(
            status_code=500, detail="Error al generar embedding para la consulta"
        )

    response = schemas.RecommendationResponse(
        query=request.query, theses=[], research_products=[], total_results=0
    )

    # Buscar tesis similares
    if request.include_theses:
        thesis_results = search_similar_theses_by_embedding(
            db, query_embedding, request.k
        )

        for result in thesis_results:
            response.theses.append(
                schemas.ThesisRecommendation(
                    id=result[0],
                    title=result[1],
                    student_id=result[2],
                    student_name=result[3],
                    advisor1_name=result[4],
                    advisor2_name=result[5],
                    similarity_score=float(result[6]),
                )
            )

    # Buscar productos de investigación similares
    if request.include_research_products:
        product_results = search_similar_research_products_by_embedding(
            db, query_embedding, request.k
        )

        for result in product_results:
            response.research_products.append(
                schemas.ResearchProductRecommendation(
                    id=result[0],
                    title=result[1],
                    site=result[2],
                    year=result[3],
                    professor_id=result[4],
                    professor_name=result[5],
                    laboratory_name=result[6],
                    similarity_score=float(result[7]),
                )
            )

    response.total_results = len(response.theses) + len(response.research_products)

    return response


@router.post(
    "/similar",
    tags=["recommendations"],
)
async def find_similar_items(
    request: schemas.SimilaritySearchRequest, db: Session = Depends(get_db)
):
    """
    Encuentra elementos similares basándose en el ID de una tesis o producto de investigación existente
    """
    if not request.thesis_id and not request.research_product_id:
        raise HTTPException(
            status_code=400, detail="Debe proporcionar thesis_id o research_product_id"
        )

    if request.thesis_id and request.research_product_id:
        raise HTTPException(
            status_code=400,
            detail="Solo puede proporcionar thesis_id O research_product_id, no ambos",
        )

    results = find_similar_items_by_id(
        db=db,
        thesis_id=request.thesis_id,
        research_product_id=request.research_product_id,
        k=request.k,
        search_type=request.search_type,
    )

    # Formatear respuesta
    formatted_results = {
        "reference_item": {
            "type": "thesis" if request.thesis_id else "research_product",
            "id": request.thesis_id or request.research_product_id,
        },
        "similar_theses": [],
        "similar_research_products": [],
    }

    # Formatear tesis similares
    for result in results["theses"]:
        formatted_results["similar_theses"].append(
            {
                "id": result[0],
                "title": result[1],
                "student_id": result[2],
                "student_name": result[3],
                "advisor1_name": result[4],
                "advisor2_name": result[5],
                "similarity_score": float(result[6]),
            }
        )

    # Formatear productos de investigación similares
    for result in results["research_products"]:
        formatted_results["similar_research_products"].append(
            {
                "id": result[0],
                "title": result[1],
                "site": result[2],
                "year": result[3],
                "professor_id": result[4],
                "professor_name": result[5],
                "laboratory_name": result[6],
                "similarity_score": float(result[7]),
            }
        )

    return formatted_results


@router.post(
    "/cluster-analysis",
    response_model=schemas.ClusterAnalysisResponse,
    tags=["recommendations"],
)
async def cluster_analysis(
    request: schemas.ClusterAnalysisRequest, db: Session = Depends(get_db)
):
    """
    Realiza análisis de clustering en tesis o productos de investigación para identificar grupos temáticos
    """
    try:
        result = perform_cluster_analysis(
            db=db,
            entity_type=request.entity_type,
            n_clusters=request.n_clusters,
            min_year=request.min_year,
            max_year=request.max_year,
        )

        # Convertir a esquema de respuesta
        clusters = []
        for cluster in result["clusters"]:
            clusters.append(
                schemas.ClusterResult(
                    cluster_id=cluster["cluster_id"],
                    items=cluster["items"],
                    cluster_center=cluster["cluster_center"],
                    cluster_size=cluster["cluster_size"],
                )
            )

        return schemas.ClusterAnalysisResponse(
            entity_type=result["entity_type"],
            clusters=clusters,
            total_items=result["total_items"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error en análisis de clustering: {str(e)}"
        )


@router.get(
    "/trends",
    tags=["recommendations"],
)
async def get_research_trends(
    years: List[int] | None = None, top_k: int = 10, db: Session = Depends(get_db)
):
    """
    Analiza tendencias en temas de investigación por año
    """
    try:
        trends = get_trending_research_topics(db, years, top_k)
        return {
            "years_analyzed": list(trends.keys()),
            "trends": trends,
            "summary": {
                "total_years": len(trends),
                "total_products": sum(
                    trend["total_products"] for trend in trends.values()
                ),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analizando tendencias: {str(e)}"
        )


@router.get(
    "/professor-similarity/{professor1_id}/{professor2_id}",
    tags=["recommendations"],
)
async def compare_professors(
    professor1_id: int, professor2_id: int, db: Session = Depends(get_db)
):
    """
    Compara la similitud de investigación entre dos profesores
    """
    try:
        similarity = get_professor_research_similarity(db, professor1_id, professor2_id)
        return similarity
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error comparando profesores: {str(e)}"
        )


@router.get(
    "/recommendations/stats",
    tags=["recommendations"],
)
async def get_recommendation_stats(db: Session = Depends(get_db)):
    """
    Obtiene estadísticas del sistema de recomendaciones
    """
    from sqlalchemy import text

    try:
        # Contar elementos con embeddings
        thesis_count = db.execute(
            text("SELECT COUNT(*) FROM theses WHERE embedding IS NOT NULL")
        ).scalar()

        product_count = db.execute(
            text("SELECT COUNT(*) FROM research_products WHERE embedding IS NOT NULL")
        ).scalar()

        # Estadísticas adicionales
        total_professors = db.execute(
            text(
                "SELECT COUNT(DISTINCT professor_id) FROM research_products WHERE embedding IS NOT NULL"
            )
        ).scalar()

        total_students = db.execute(
            text(
                "SELECT COUNT(DISTINCT student_id) FROM theses WHERE embedding IS NOT NULL"
            )
        ).scalar()

        year_range = db.execute(
            text(
                "SELECT MIN(year), MAX(year) FROM research_products WHERE embedding IS NOT NULL"
            )
        ).fetchone()

        return {
            "total_theses_with_embeddings": thesis_count or 0,
            "total_research_products_with_embeddings": product_count or 0,
            "total_professors_with_research": total_professors or 0,
            "total_students_with_theses": total_students or 0,
            "research_year_range": {
                "min_year": year_range[0] if year_range else None,
                "max_year": year_range[1] if year_range else None,
            },
            "system_ready": (thesis_count or 0) > 0 or (product_count or 0) > 0,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}"
        )


@router.get(
    "/health",
    tags=["recommendations"],
)
async def recommendation_health_check():
    """
    Verifica el estado del sistema de recomendaciones
    """
    import os

    return {
        "status": "healthy",
        "dashscope_configured": bool(os.getenv("DASHSCOPE_API_KEY")),
        "version": "1.0.0",
        "features": [
            "text_based_recommendations",
            "similarity_search",
            "cluster_analysis",
            "trend_analysis",
            "professor_comparison",
        ],
    }

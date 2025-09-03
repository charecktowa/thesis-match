# Sistema de Recomendaciones - Thesis Match

Este sistema implementa un avanzado motor de recomendaciones basado en embeddings para encontrar tesis y productos de investigación similares.

## 🚀 Características

### 1. Recomendaciones Basadas en Texto
- **Endpoint**: `POST /api/v1/recommend`
- **Descripción**: Encuentra tesis y productos de investigación similares a una consulta de texto
- **Parámetros**:
  - `query`: Texto de consulta (ej: "machine learning", "redes neuronales")
  - `k`: Número de resultados a retornar (default: 10)
  - `include_theses`: Incluir tesis en resultados (default: true)
  - `include_research_products`: Incluir productos de investigación (default: true)

**Ejemplo de uso**:
```json
{
  "query": "inteligencia artificial",
  "k": 5,
  "include_theses": true,
  "include_research_products": true
}
```

### 2. Búsqueda de Similitud por ID
- **Endpoint**: `POST /api/v1/similar`
- **Descripción**: Encuentra elementos similares basándose en una tesis o producto existente
- **Parámetros**:
  - `thesis_id` o `research_product_id`: ID del elemento de referencia
  - `k`: Número de resultados (default: 10)
  - `search_type`: "theses", "research_products", o "both" (default: "both")

**Ejemplo de uso**:
```json
{
  "thesis_id": 123,
  "k": 5,
  "search_type": "both"
}
```

### 3. Análisis de Clustering
- **Endpoint**: `POST /api/v1/cluster-analysis`
- **Descripción**: Agrupa tesis o productos de investigación en clusters temáticos usando K-Means
- **Parámetros**:
  - `entity_type`: "theses" o "research_products"
  - `n_clusters`: Número de clusters a crear (default: 5)
  - `min_year`, `max_year`: Filtros por año (opcional)

**Ejemplo de uso**:
```json
{
  "entity_type": "research_products",
  "n_clusters": 5,
  "min_year": 2020,
  "max_year": 2024
}
```

### 4. Análisis de Tendencias
- **Endpoint**: `GET /api/v1/trends`
- **Descripción**: Analiza tendencias de investigación por año
- **Parámetros**:
  - `years`: Lista de años a analizar (opcional)
  - `top_k`: Número de clusters principales por año (default: 10)

**Ejemplo de uso**:
```
GET /api/v1/trends?years=2020&years=2021&years=2022&top_k=5
```

### 5. Comparación de Profesores
- **Endpoint**: `GET /api/v1/professor-similarity/{professor1_id}/{professor2_id}`
- **Descripción**: Compara la similitud entre la investigación de dos profesores
- **Retorna**: Puntuación de similitud y temas comunes

**Ejemplo de uso**:
```
GET /api/v1/professor-similarity/1/2
```

### 6. Estadísticas del Sistema
- **Endpoint**: `GET /api/v1/recommendations/stats`
- **Descripción**: Proporciona estadísticas del sistema de recomendaciones
- **Retorna**: Número de elementos con embeddings, rangos de años, etc.

### 7. Health Check
- **Endpoint**: `GET /api/v1/health`
- **Descripción**: Verifica el estado del sistema de recomendaciones
- **Retorna**: Estado del sistema y configuración

## 🔧 Tecnologías Utilizadas

### Embeddings
- **Modelo**: Dashscope Text Embedding v4 (1024 dimensiones)
- **Proveedor**: Alibaba Cloud Dashscope
- **Base de datos**: PostgreSQL con extensión pgvector

### Machine Learning
- **Clustering**: K-Means (scikit-learn)
- **Similitud**: Distancia coseno con pgvector
- **Análisis**: PCA para reducción dimensional

### Framework
- **Backend**: FastAPI
- **ORM**: SQLAlchemy
- **Base de datos**: PostgreSQL + pgvector

## 📊 Algoritmos Implementados

### 1. Similitud Coseno
```sql
-- Búsqueda vectorial optimizada con pgvector
SELECT *, 1 - (embedding <=> 'query_embedding') as similarity_score
FROM table
ORDER BY embedding <=> 'query_embedding'
LIMIT k
```

### 2. K-Means Clustering
- Agrupa elementos en clusters temáticos
- Utiliza embeddings como características
- Identifica centros de clusters para análisis

### 3. Análisis de Tendencias
- Agrupa productos por año
- Realiza clustering temporal
- Identifica evolución de temas

## 🚀 Instalación y Configuración

### 1. Dependencias
```bash
pip install -r requirements.txt
```

### 2. Variables de Entorno
```bash
# Configurar en .env
DASHSCOPE_API_KEY=your_dashscope_api_key
DATABASE_URL=postgresql://user:pass@localhost/thesis_match
```

### 3. Generar Embeddings
```bash
# Generar embeddings para datos existentes
python -m scraper.generate_embeddings
```

### 4. Ejecutar Aplicación
```bash
# Iniciar servidor
python -m app.main
```

## 🧪 Pruebas

### Script de Pruebas
```bash
# Ejecutar pruebas completas
python test_recommendations.py
```

### Pruebas Manuales
```python
import requests

# Probar recomendaciones
response = requests.post("http://localhost:8000/api/v1/recommend", json={
    "query": "machine learning",
    "k": 5
})
```

## 📈 Métricas de Rendimiento

### Similitud
- **Precisión**: Basada en distancia coseno
- **Recall**: Ajustable mediante parámetro `k`
- **Velocidad**: Optimizada con índices pgvector

### Clustering
- **Algoritmo**: K-Means con inicialización k-means++
- **Métricas**: Inercia intra-cluster, silhouette score
- **Escalabilidad**: Hasta 10,000+ elementos

## 🔄 Flujo de Trabajo

1. **Ingesta de Datos**: Los scrapers recolectan tesis y productos
2. **Generación de Embeddings**: Dashscope procesa títulos
3. **Almacenamiento**: PostgreSQL + pgvector almacena vectores
4. **Consultas**: API REST proporciona recomendaciones
5. **Análisis**: Clustering y tendencias en tiempo real

## 🎯 Casos de Uso

### Para Estudiantes
- Encontrar tesis relacionadas con su tema de interés
- Descubrir productos de investigación relevantes
- Identificar posibles asesores por área temática

### Para Profesores
- Comparar similitud con otros investigadores
- Encontrar colaboraciones potenciales
- Analizar tendencias en su área de investigación

### Para Administradores
- Análisis de clusters de investigación
- Tendencias institucionales por año
- Métricas de productividad académica

## 🔮 Funcionalidades Futuras

1. **Recomendaciones Híbridas**: Combinar contenido + colaborativo
2. **Filtros Avanzados**: Por laboratorio, programa, año
3. **Recomendaciones Personalizadas**: Basadas en historial de usuario
4. **Análisis de Sentimientos**: En abstracts y conclusiones
5. **Visualizaciones**: Mapas de clusters, grafos de similitud
6. **API Rate Limiting**: Para uso en producción
7. **Cache Redis**: Para consultas frecuentes

## 📝 Contribución

1. Fork del repositorio
2. Crear branch para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

[Licencia del proyecto]

## 📞 Soporte

Para reportar bugs o solicitar features, crear un issue en el repositorio.

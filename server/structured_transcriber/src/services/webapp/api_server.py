"""
FastAPI Server for Transcription Search and Meeting Management

This module provides REST API endpoints for:
- Semantic search across transcriptions
- Meeting listing and detail retrieval
- RAG-based Q&A over meeting content
"""

import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core import config
from src.core.logging_config import init_logging, get_logger
from src.services.vector_db.query_vector_index import VectorIndexQuery
from src.models.db_manager import DatabaseManager

# Initialize logging
init_logging(environment="development")
logger = get_logger(__name__)

# ==================== Prometheus Metrics ====================

from prometheus_client import REGISTRY, CollectorRegistry

# Create metrics only if they don't exist (prevents duplicate errors on reload)
try:
    # Request counters
    request_count = Counter(
        'api_requests_total',
        'Total number of API requests',
        ['method', 'endpoint', 'status']
    )

    # Request duration histogram
    request_duration = Histogram(
        'api_request_duration_seconds',
        'API request duration in seconds',
        ['method', 'endpoint']
    )

    # Active requests gauge
    active_requests = Gauge(
        'api_active_requests',
        'Number of active API requests'
    )

    # Database query metrics
    db_query_duration = Histogram(
        'db_query_duration_seconds',
        'Database query duration in seconds',
        ['query_type']
    )

    # Vector DB metrics
    vector_db_documents = Gauge(
        'vector_db_documents_total',
        'Total number of documents in Vector DB'
    )

    # SQLite metrics
    sqlite_meetings = Gauge(
        'sqlite_meetings_total',
        'Total number of meetings in SQLite DB'
    )
except ValueError:
    # Metrics already registered (hot reload)
    request_count = REGISTRY._names_to_collectors.get('api_requests_total')
    request_duration = REGISTRY._names_to_collectors.get('api_request_duration_seconds')
    active_requests = REGISTRY._names_to_collectors.get('api_active_requests')
    db_query_duration = REGISTRY._names_to_collectors.get('db_query_duration_seconds')
    vector_db_documents = REGISTRY._names_to_collectors.get('vector_db_documents_total')
    sqlite_meetings = REGISTRY._names_to_collectors.get('sqlite_meetings_total')


# ==================== Pydantic Models ====================

class SearchRequest(BaseModel):
    """Request model for semantic search"""
    query: str = Field(..., min_length=1, description="Search query text")
    n_results: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    meeting_id: Optional[str] = Field(default=None, description="Filter by specific meeting ID")


class SearchResult(BaseModel):
    """Single search result"""
    meeting_id: str
    file_name: str
    speaker: str
    text: str
    timestamp: Optional[str]
    distance: float
    relevance_score: float


class SearchResponse(BaseModel):
    """Response model for semantic search"""
    query: str
    results: List[SearchResult]
    total_results: int
    processing_time_ms: float


class MeetingListItem(BaseModel):
    """Meeting summary for list view"""
    meeting_id: str
    file_name: str
    created_at: str
    total_segments: int
    total_speakers: int
    duration_minutes: Optional[float]


class MeetingDetail(BaseModel):
    """Detailed meeting information"""
    meeting_id: str
    file_name: str
    created_at: str
    participants: List[str]
    total_segments: int
    segments: List[Dict[str, Any]]


class QARequest(BaseModel):
    """Request model for RAG Q&A"""
    question: str = Field(..., min_length=1, description="Question to answer")
    meeting_id: Optional[str] = Field(default=None, description="Filter by specific meeting ID")
    n_context: int = Field(default=5, ge=1, le=20, description="Number of context chunks to retrieve")


class QAResponse(BaseModel):
    """Response model for RAG Q&A"""
    question: str
    answer: str
    context_chunks: List[SearchResult]
    processing_time_ms: float


# Global instances
vector_query: Optional[VectorIndexQuery] = None
db_manager: Optional[DatabaseManager] = None


# ==================== Lifecycle Management ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle (startup and shutdown)"""
    global vector_query, db_manager

    # Startup
    print("🚀 Starting Transcription API...")

    # Initialize Vector DB query
    vector_db_path = Path(config.VECTOR_DB_PATH)
    if vector_db_path.exists():
        vector_query = VectorIndexQuery(str(vector_db_path))
        print(f"✅ Vector DB loaded from {vector_db_path}")
    else:
        print(f"⚠️  Vector DB not found at {vector_db_path}")

    # Initialize SQLite DB
    db_path = Path(config.SQLITE_DB_PATH)
    if db_path.exists():
        db_manager = DatabaseManager(str(db_path))
        print(f"✅ SQLite DB loaded from {db_path}")
    else:
        print(f"⚠️  SQLite DB not found at {db_path}")

    yield  # Application runs here

    # Shutdown
    print("🛑 Shutting down Transcription API...")
    if db_manager:
        db_manager.close()
        print("✅ Database connections closed")


# ==================== FastAPI App ====================

app = FastAPI(
    title="Transcription API",
    description="API for searching and managing meeting transcriptions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Request Metrics Middleware ====================

@app.middleware("http")
async def metrics_middleware(request, call_next):
    """
    Middleware to track request metrics with Prometheus.

    Tracks:
    - Request count by endpoint and status
    - Request duration by endpoint
    - Active requests
    """
    # Skip metrics for /metrics endpoint to avoid recursion
    if request.url.path == "/metrics":
        return await call_next(request)

    # Increment active requests
    active_requests.inc()

    # Start timer
    start_time = time.time()

    try:
        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        # Log request
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {duration*1000:.2f}ms"
        )

        return response

    except Exception as e:
        # Record error
        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500
        ).inc()

        logger.error(f"Error processing request: {e}", exc_info=True)
        raise

    finally:
        # Decrement active requests
        active_requests.dec()


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")

    health_status = {
        "status": "healthy",
        "service": "Transcription API",
        "timestamp": datetime.now().isoformat(),
        "vector_db_available": vector_query is not None,
        "sqlite_db_available": db_manager is not None
    }

    # Update Prometheus metrics
    if vector_query:
        try:
            # Get document count from Vector DB
            vector_db_documents.set(vector_query.collection.count())
        except Exception as e:
            logger.warning(f"Failed to get Vector DB count: {e}")

    if db_manager:
        try:
            # Get meeting count from SQLite
            meetings = db_manager.get_all_meetings()
            sqlite_meetings.set(len(meetings))
        except Exception as e:
            logger.warning(f"Failed to get SQLite meeting count: {e}")

    return health_status


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    logger.debug("Metrics endpoint requested")
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/api/stats")
async def api_stats():
    """
    Get API statistics and database info.

    Returns:
        API statistics including database counts and health info
    """
    logger.info("API stats requested")

    stats = {
        "timestamp": datetime.now().isoformat(),
        "api_version": "1.0.0",
        "databases": {
            "vector_db": {
                "available": vector_query is not None,
                "document_count": 0
            },
            "sqlite": {
                "available": db_manager is not None,
                "meeting_count": 0,
                "participant_count": 0
            }
        }
    }

    # Get Vector DB stats
    if vector_query:
        try:
            stats["databases"]["vector_db"]["document_count"] = vector_query.collection.count()
        except Exception as e:
            logger.error(f"Error getting Vector DB count: {e}")

    # Get SQLite stats
    if db_manager:
        try:
            meetings = db_manager.get_all_meetings()
            stats["databases"]["sqlite"]["meeting_count"] = len(meetings)

            participants = db_manager.get_all_participants()
            stats["databases"]["sqlite"]["participant_count"] = len(participants)
        except Exception as e:
            logger.error(f"Error getting SQLite stats: {e}")

    return stats


# ==================== Search Endpoints ====================

@app.post("/api/search", response_model=SearchResponse)
async def search_transcriptions(request: SearchRequest):
    """
    Semantic search across all transcriptions

    Args:
        request: SearchRequest with query text and parameters

    Returns:
        SearchResponse with ranked results
    """
    if not vector_query:
        raise HTTPException(status_code=503, detail="Vector DB not available")

    start_time = datetime.now()

    try:
        # Query vector DB
        results = vector_query.search(
            query_text=request.query,
            n_results=request.n_results,
            filter_meeting_id=request.meeting_id
        )

        # Convert to SearchResult models
        search_results = []
        for result in results:
            metadata = result.get('metadata', {})
            distance = result.get('distance', 0.0)

            search_results.append(SearchResult(
                meeting_id=metadata.get('meeting_id', 'unknown'),
                file_name=metadata.get('file_name', 'unknown'),
                speaker=metadata.get('speaker', 'unknown'),
                text=result.get('text', ''),
                timestamp=metadata.get('timestamp'),
                distance=distance,
                relevance_score=1.0 - distance  # Convert distance to similarity score
            ))

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results),
            processing_time_ms=processing_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# ==================== Meeting Endpoints ====================

@app.get("/api/meetings", response_model=List[MeetingListItem])
async def list_meetings(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
):
    """
    List all meetings with summary information

    Args:
        limit: Maximum number of meetings to return
        offset: Number of meetings to skip

    Returns:
        List of MeetingListItem
    """
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        meetings = db_manager.get_all_meetings(limit=limit, offset=offset)

        result = []
        for meeting in meetings:
            result.append(MeetingListItem(
                meeting_id=meeting['meeting_id'],
                file_name=meeting['file_name'],
                created_at=meeting['created_at'],
                total_segments=meeting.get('total_segments', 0),
                total_speakers=meeting.get('total_speakers', 0),
                duration_minutes=meeting.get('duration_minutes')
            ))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list meetings: {str(e)}")


@app.get("/api/meetings/{meeting_id}", response_model=MeetingDetail)
async def get_meeting_detail(meeting_id: str):
    """
    Get detailed information about a specific meeting

    Args:
        meeting_id: Meeting ID to retrieve

    Returns:
        MeetingDetail with full transcript
    """
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        meeting = db_manager.get_meeting(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found")

        segments = db_manager.get_meeting_segments(meeting_id)
        participants = db_manager.get_meeting_participants(meeting_id)

        return MeetingDetail(
            meeting_id=meeting['meeting_id'],
            file_name=meeting['file_name'],
            created_at=meeting['created_at'],
            participants=[p['name'] for p in participants],
            total_segments=len(segments),
            segments=segments
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get meeting: {str(e)}")


# ==================== RAG Q&A Endpoint ====================

@app.post("/api/qa", response_model=QAResponse)
async def answer_question(request: QARequest):
    """
    Answer questions using RAG over meeting transcriptions

    Args:
        request: QARequest with question and parameters

    Returns:
        QAResponse with answer and context
    """
    if not vector_query:
        raise HTTPException(status_code=503, detail="Vector DB not available")

    start_time = datetime.now()

    try:
        # Retrieve relevant context
        results = vector_query.search(
            query_text=request.question,
            n_results=request.n_context,
            filter_meeting_id=request.meeting_id
        )

        # Convert to SearchResult models
        context_chunks = []
        context_texts = []

        for result in results:
            metadata = result.get('metadata', {})
            distance = result.get('distance', 0.0)
            text = result.get('text', '')

            context_chunks.append(SearchResult(
                meeting_id=metadata.get('meeting_id', 'unknown'),
                file_name=metadata.get('file_name', 'unknown'),
                speaker=metadata.get('speaker', 'unknown'),
                text=text,
                timestamp=metadata.get('timestamp'),
                distance=distance,
                relevance_score=1.0 - distance
            ))

            context_texts.append(f"[{metadata.get('speaker', 'unknown')}]: {text}")

        # Generate answer (simple concatenation for now - can be enhanced with LLM)
        if not context_texts:
            answer = "申し訳ありません。関連する情報が見つかりませんでした。"
        else:
            # For now, return top context as answer
            # In future, integrate with OpenAI/Gemini for actual RAG
            answer = f"以下の関連する発言が見つかりました:\n\n{context_texts[0]}"
            if len(context_texts) > 1:
                answer += f"\n\n他に{len(context_texts)-1}件の関連発言があります。"

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return QAResponse(
            question=request.question,
            answer=answer,
            context_chunks=context_chunks,
            processing_time_ms=processing_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(e)}")


# ==================== Main ====================

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

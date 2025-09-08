#!/usr/bin/env python3
"""
AI Integration Enhancement Module for Westfall Personal Assistant

Provides document chunking, sliding window context management, priority-based RAG,
query planning, and AI capability detection with fallback systems.
"""

import logging
import re
import math
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
import hashlib
import json
from datetime import datetime
import threading
import queue

logger = logging.getLogger(__name__)


class ChunkType(Enum):
    """Types of document chunks."""
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"


class QueryType(Enum):
    """Types of AI queries."""
    SIMPLE = "simple"
    COMPLEX = "complex"
    MULTI_STEP = "multi_step"
    RETRIEVAL = "retrieval"


@dataclass
class DocumentChunk:
    """Represents a chunk of a document."""
    id: str
    content: str
    chunk_type: ChunkType
    start_index: int
    end_index: int
    metadata: Dict = None
    embedding: Optional[List[float]] = None
    priority: float = 1.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'content': self.content,
            'chunk_type': self.chunk_type.value,
            'start_index': self.start_index,
            'end_index': self.end_index,
            'metadata': self.metadata or {},
            'priority': self.priority,
            'has_embedding': self.embedding is not None
        }


@dataclass
class QueryStep:
    """Represents a step in a multi-step query plan."""
    step_id: str
    step_type: str
    description: str
    depends_on: List[str]
    parameters: Dict
    estimated_time: float = 0.0
    completed: bool = False
    result: Any = None


class DocumentChunker:
    """Handles document chunking with multiple strategies."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.chunk_counter = 0
    
    def chunk_by_paragraphs(self, text: str, max_chunk_size: int = None) -> List[DocumentChunk]:
        """Chunk document by paragraphs."""
        if max_chunk_size is None:
            max_chunk_size = self.chunk_size
        
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = ""
        current_start = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph would exceed the max size, create a chunk
            if current_chunk and len(current_chunk) + len(paragraph) + 2 > max_chunk_size:
                chunk = self._create_chunk(
                    current_chunk, 
                    ChunkType.PARAGRAPH, 
                    current_start, 
                    current_start + len(current_chunk)
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                current_start = current_start + len(current_chunk) - self.overlap
                current_chunk = current_chunk[-self.overlap:] + "\n\n" + paragraph if self.overlap > 0 else paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add remaining chunk
        if current_chunk:
            chunk = self._create_chunk(
                current_chunk, 
                ChunkType.PARAGRAPH, 
                current_start, 
                current_start + len(current_chunk)
            )
            chunks.append(chunk)
        
        return chunks
    
    def chunk_by_sentences(self, text: str, max_chunk_size: int = None) -> List[DocumentChunk]:
        """Chunk document by sentences."""
        if max_chunk_size is None:
            max_chunk_size = self.chunk_size
        
        # Simple sentence splitting (could be improved with spaCy/NLTK)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        current_start = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if current_chunk and len(current_chunk) + len(sentence) + 1 > max_chunk_size:
                chunk = self._create_chunk(
                    current_chunk, 
                    ChunkType.SENTENCE, 
                    current_start, 
                    current_start + len(current_chunk)
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                current_start = current_start + len(current_chunk) - self.overlap
                current_chunk = current_chunk[-self.overlap:] + " " + sentence if self.overlap > 0 else sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add remaining chunk
        if current_chunk:
            chunk = self._create_chunk(
                current_chunk, 
                ChunkType.SENTENCE, 
                current_start, 
                current_start + len(current_chunk)
            )
            chunks.append(chunk)
        
        return chunks
    
    def chunk_by_fixed_size(self, text: str, chunk_size: int = None) -> List[DocumentChunk]:
        """Chunk document by fixed character size."""
        if chunk_size is None:
            chunk_size = self.chunk_size
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Try to break at word boundary if not at end
            if end < len(text):
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk_text = text[start:end]
            chunk = self._create_chunk(chunk_text, ChunkType.FIXED_SIZE, start, end)
            chunks.append(chunk)
            
            # Move start with overlap
            start = end - self.overlap if self.overlap > 0 else end
        
        return chunks
    
    def _create_chunk(self, content: str, chunk_type: ChunkType, start: int, end: int) -> DocumentChunk:
        """Create a document chunk."""
        self.chunk_counter += 1
        chunk_id = f"chunk_{self.chunk_counter}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        
        return DocumentChunk(
            id=chunk_id,
            content=content,
            chunk_type=chunk_type,
            start_index=start,
            end_index=end,
            metadata={
                'length': len(content),
                'word_count': len(content.split()),
                'created_at': datetime.now().isoformat()
            }
        )


class SlidingWindowManager:
    """Manages sliding window context for AI conversations."""
    
    def __init__(self, window_size: int = 4096, max_context_tokens: int = 8192):
        self.window_size = window_size
        self.max_context_tokens = max_context_tokens
        self.context_history = []
        self.current_position = 0
        self.lock = threading.RLock()
    
    def add_context(self, content: str, context_type: str = "user", metadata: Dict = None):
        """Add content to the sliding window context."""
        with self.lock:
            context_entry = {
                'content': content,
                'type': context_type,
                'timestamp': datetime.now().isoformat(),
                'position': self.current_position,
                'metadata': metadata or {},
                'token_estimate': self._estimate_tokens(content)
            }
            
            self.context_history.append(context_entry)
            self.current_position += 1
            
            # Maintain window size
            self._maintain_window_size()
    
    def get_context_window(self, max_tokens: int = None) -> str:
        """Get the current context window as a string."""
        if max_tokens is None:
            max_tokens = self.max_context_tokens
        
        with self.lock:
            context_parts = []
            total_tokens = 0
            
            # Add context from most recent backwards
            for entry in reversed(self.context_history):
                entry_tokens = entry['token_estimate']
                
                if total_tokens + entry_tokens > max_tokens:
                    break
                
                context_parts.insert(0, f"[{entry['type']}] {entry['content']}")
                total_tokens += entry_tokens
            
            return "\n".join(context_parts)
    
    def get_relevant_context(self, query: str, max_tokens: int = None) -> str:
        """Get context relevant to a specific query."""
        if max_tokens is None:
            max_tokens = self.max_context_tokens // 2
        
        with self.lock:
            # Simple relevance scoring based on keyword overlap
            scored_entries = []
            query_words = set(query.lower().split())
            
            for entry in self.context_history:
                content_words = set(entry['content'].lower().split())
                overlap = len(query_words.intersection(content_words))
                relevance_score = overlap / max(len(query_words), 1)
                
                scored_entries.append((relevance_score, entry))
            
            # Sort by relevance and recent-ness
            scored_entries.sort(key=lambda x: (x[0], x[1]['position']), reverse=True)
            
            # Build context within token limit
            context_parts = []
            total_tokens = 0
            
            for score, entry in scored_entries:
                if score == 0:  # No relevance
                    continue
                
                entry_tokens = entry['token_estimate']
                if total_tokens + entry_tokens > max_tokens:
                    continue
                
                context_parts.append(f"[{entry['type']}] {entry['content']}")
                total_tokens += entry_tokens
            
            return "\n".join(context_parts)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough estimate: 1 token ≈ 4 characters for English text
        return len(text) // 4
    
    def _maintain_window_size(self):
        """Maintain the sliding window size."""
        total_tokens = sum(entry['token_estimate'] for entry in self.context_history)
        
        while total_tokens > self.max_context_tokens and self.context_history:
            removed_entry = self.context_history.pop(0)
            total_tokens -= removed_entry['token_estimate']
    
    def clear_context(self):
        """Clear all context history."""
        with self.lock:
            self.context_history.clear()
            self.current_position = 0
    
    def get_context_stats(self) -> Dict:
        """Get statistics about the current context."""
        with self.lock:
            total_tokens = sum(entry['token_estimate'] for entry in self.context_history)
            
            return {
                'total_entries': len(self.context_history),
                'total_tokens': total_tokens,
                'max_tokens': self.max_context_tokens,
                'utilization': (total_tokens / self.max_context_tokens) * 100,
                'oldest_entry': self.context_history[0]['timestamp'] if self.context_history else None,
                'newest_entry': self.context_history[-1]['timestamp'] if self.context_history else None
            }


class PriorityRAG:
    """Priority-based Retrieval Augmented Generation system."""
    
    def __init__(self, max_results: int = 10):
        self.max_results = max_results
        self.document_store = {}
        self.chunk_index = {}
        self.priority_weights = {
            'recency': 0.3,
            'relevance': 0.4,
            'priority': 0.2,
            'user_rating': 0.1
        }
        self.lock = threading.RLock()
    
    def add_document(self, doc_id: str, chunks: List[DocumentChunk], metadata: Dict = None):
        """Add a document and its chunks to the RAG system."""
        with self.lock:
            self.document_store[doc_id] = {
                'chunks': chunks,
                'metadata': metadata or {},
                'added_at': datetime.now(),
                'access_count': 0,
                'last_accessed': None
            }
            
            # Index chunks
            for chunk in chunks:
                self.chunk_index[chunk.id] = {
                    'doc_id': doc_id,
                    'chunk': chunk,
                    'keywords': self._extract_keywords(chunk.content)
                }
    
    def retrieve(self, query: str, max_results: int = None, filters: Dict = None) -> List[Tuple[DocumentChunk, float]]:
        """Retrieve relevant chunks with priority scoring."""
        if max_results is None:
            max_results = self.max_results
        
        with self.lock:
            query_keywords = self._extract_keywords(query)
            scored_chunks = []
            
            for chunk_id, chunk_data in self.chunk_index.items():
                chunk = chunk_data['chunk']
                doc_info = self.document_store[chunk_data['doc_id']]
                
                # Apply filters
                if filters and not self._passes_filters(chunk, doc_info, filters):
                    continue
                
                # Calculate composite score
                scores = {
                    'relevance': self._calculate_relevance(query_keywords, chunk_data['keywords']),
                    'recency': self._calculate_recency_score(doc_info['added_at']),
                    'priority': chunk.priority,
                    'user_rating': doc_info.get('user_rating', 0.5)
                }
                
                composite_score = sum(
                    scores[factor] * weight 
                    for factor, weight in self.priority_weights.items()
                )
                
                scored_chunks.append((chunk, composite_score, scores))
            
            # Sort by composite score
            scored_chunks.sort(key=lambda x: x[1], reverse=True)
            
            # Update access statistics
            for chunk, score, _ in scored_chunks[:max_results]:
                doc_id = self.chunk_index[chunk.id]['doc_id']
                self.document_store[doc_id]['access_count'] += 1
                self.document_store[doc_id]['last_accessed'] = datetime.now()
            
            return [(chunk, score) for chunk, score, _ in scored_chunks[:max_results]]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (simple implementation)."""
        # Remove punctuation and convert to lowercase
        cleaned_text = re.sub(r'[^\w\s]', '', text.lower())
        words = cleaned_text.split()
        
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _calculate_relevance(self, query_keywords: List[str], content_keywords: List[str]) -> float:
        """Calculate relevance score between query and content."""
        if not query_keywords or not content_keywords:
            return 0.0
        
        query_set = set(query_keywords)
        content_set = set(content_keywords)
        
        intersection = query_set.intersection(content_set)
        union = query_set.union(content_set)
        
        if not union:
            return 0.0
        
        # Jaccard similarity
        return len(intersection) / len(union)
    
    def _calculate_recency_score(self, added_at: datetime) -> float:
        """Calculate recency score (more recent = higher score)."""
        now = datetime.now()
        age_days = (now - added_at).days
        
        # Exponential decay: score = e^(-age_days/30)
        return math.exp(-age_days / 30)
    
    def _passes_filters(self, chunk: DocumentChunk, doc_info: Dict, filters: Dict) -> bool:
        """Check if chunk passes all filters."""
        for filter_key, filter_value in filters.items():
            if filter_key == 'doc_type':
                if doc_info['metadata'].get('type') != filter_value:
                    return False
            elif filter_key == 'min_priority':
                if chunk.priority < filter_value:
                    return False
            elif filter_key == 'chunk_type':
                if chunk.chunk_type.value != filter_value:
                    return False
        
        return True
    
    def update_priority_weights(self, weights: Dict[str, float]):
        """Update priority scoring weights."""
        with self.lock:
            total_weight = sum(weights.values())
            if abs(total_weight - 1.0) > 0.01:
                # Normalize weights
                weights = {k: v / total_weight for k, v in weights.items()}
            
            self.priority_weights.update(weights)
    
    def get_document_stats(self) -> Dict:
        """Get statistics about the document store."""
        with self.lock:
            total_chunks = sum(len(doc['chunks']) for doc in self.document_store.values())
            
            return {
                'total_documents': len(self.document_store),
                'total_chunks': total_chunks,
                'indexed_chunks': len(self.chunk_index),
                'priority_weights': self.priority_weights.copy()
            }


class QueryPlanner:
    """Plans and executes complex AI queries."""
    
    def __init__(self):
        self.step_handlers = {}
        self.active_plans = {}
        self.completed_plans = {}
        self.lock = threading.RLock()
    
    def register_step_handler(self, step_type: str, handler: Callable):
        """Register a handler for a specific step type."""
        self.step_handlers[step_type] = handler
    
    def create_query_plan(self, query: str, query_type: QueryType = QueryType.SIMPLE) -> str:
        """Create a query execution plan."""
        plan_id = f"plan_{datetime.now().timestamp()}_{hashlib.md5(query.encode()).hexdigest()[:8]}"
        
        if query_type == QueryType.SIMPLE:
            steps = [
                QueryStep(
                    step_id="step_1",
                    step_type="simple_query",
                    description="Execute simple query",
                    depends_on=[],
                    parameters={'query': query},
                    estimated_time=2.0
                )
            ]
        elif query_type == QueryType.RETRIEVAL:
            steps = [
                QueryStep(
                    step_id="step_1",
                    step_type="retrieve_context",
                    description="Retrieve relevant context",
                    depends_on=[],
                    parameters={'query': query},
                    estimated_time=1.0
                ),
                QueryStep(
                    step_id="step_2",
                    step_type="generate_response",
                    description="Generate response with context",
                    depends_on=["step_1"],
                    parameters={'query': query},
                    estimated_time=3.0
                )
            ]
        elif query_type == QueryType.COMPLEX:
            steps = [
                QueryStep(
                    step_id="step_1",
                    step_type="analyze_query",
                    description="Analyze query complexity",
                    depends_on=[],
                    parameters={'query': query},
                    estimated_time=1.0
                ),
                QueryStep(
                    step_id="step_2",
                    step_type="decompose_query",
                    description="Break down into sub-queries",
                    depends_on=["step_1"],
                    parameters={},
                    estimated_time=1.5
                ),
                QueryStep(
                    step_id="step_3",
                    step_type="execute_sub_queries",
                    description="Execute sub-queries",
                    depends_on=["step_2"],
                    parameters={},
                    estimated_time=5.0
                ),
                QueryStep(
                    step_id="step_4",
                    step_type="synthesize_results",
                    description="Combine results",
                    depends_on=["step_3"],
                    parameters={},
                    estimated_time=2.0
                )
            ]
        else:  # MULTI_STEP
            steps = [
                QueryStep(
                    step_id="step_1",
                    step_type="plan_multi_step",
                    description="Plan multi-step execution",
                    depends_on=[],
                    parameters={'query': query},
                    estimated_time=2.0
                ),
                QueryStep(
                    step_id="step_2",
                    step_type="execute_steps",
                    description="Execute planned steps",
                    depends_on=["step_1"],
                    parameters={},
                    estimated_time=10.0
                )
            ]
        
        with self.lock:
            self.active_plans[plan_id] = {
                'query': query,
                'query_type': query_type,
                'steps': {step.step_id: step for step in steps},
                'created_at': datetime.now(),
                'status': 'created',
                'progress': 0.0
            }
        
        return plan_id
    
    def execute_plan(self, plan_id: str) -> Dict:
        """Execute a query plan."""
        with self.lock:
            if plan_id not in self.active_plans:
                return {'error': 'Plan not found'}
            
            plan = self.active_plans[plan_id]
            plan['status'] = 'executing'
            
            try:
                results = {}
                completed_steps = set()
                
                while len(completed_steps) < len(plan['steps']):
                    # Find steps that can be executed (dependencies met)
                    ready_steps = []
                    for step_id, step in plan['steps'].items():
                        if step_id not in completed_steps and all(dep in completed_steps for dep in step.depends_on):
                            ready_steps.append(step)
                    
                    if not ready_steps:
                        return {'error': 'Circular dependencies or missing steps'}
                    
                    # Execute ready steps
                    for step in ready_steps:
                        result = self._execute_step(step, results)
                        results[step.step_id] = result
                        step.completed = True
                        step.result = result
                        completed_steps.add(step.step_id)
                        
                        # Update progress
                        plan['progress'] = len(completed_steps) / len(plan['steps']) * 100
                
                plan['status'] = 'completed'
                plan['results'] = results
                
                # Move to completed plans
                self.completed_plans[plan_id] = self.active_plans.pop(plan_id)
                
                return {'success': True, 'results': results}
                
            except Exception as e:
                plan['status'] = 'failed'
                plan['error'] = str(e)
                return {'error': str(e)}
    
    def _execute_step(self, step: QueryStep, previous_results: Dict) -> Any:
        """Execute a single step."""
        handler = self.step_handlers.get(step.step_type)
        if not handler:
            return f"No handler for step type: {step.step_type}"
        
        try:
            return handler(step, previous_results)
        except Exception as e:
            logger.error(f"Error executing step {step.step_id}: {e}")
            return f"Step execution failed: {e}"
    
    def get_plan_status(self, plan_id: str) -> Dict:
        """Get the status of a query plan."""
        with self.lock:
            if plan_id in self.active_plans:
                plan = self.active_plans[plan_id]
                return {
                    'status': plan['status'],
                    'progress': plan['progress'],
                    'steps_completed': sum(1 for step in plan['steps'].values() if step.completed),
                    'total_steps': len(plan['steps'])
                }
            elif plan_id in self.completed_plans:
                return {'status': 'completed', 'progress': 100.0}
            else:
                return {'status': 'not_found'}


class AICapabilityDetector:
    """Detects available AI capabilities and provides fallbacks."""
    
    def __init__(self):
        self.capabilities = {}
        self.fallback_handlers = {}
        self.last_check = None
        self.check_interval = 300  # 5 minutes
    
    def detect_capabilities(self) -> Dict:
        """Detect available AI capabilities."""
        capabilities = {
            'local_models': self._check_local_models(),
            'embeddings': self._check_embeddings(),
            'text_generation': self._check_text_generation(),
            'document_processing': self._check_document_processing(),
            'vector_search': self._check_vector_search()
        }
        
        self.capabilities = capabilities
        self.last_check = datetime.now()
        
        return capabilities
    
    def _check_local_models(self) -> Dict:
        """Check for available local AI models."""
        return {
            'available': False,  # Would check for actual model files
            'models': [],
            'fallback': 'remote_api'
        }
    
    def _check_embeddings(self) -> Dict:
        """Check for embedding capabilities."""
        return {
            'available': False,  # Would check for embedding models/APIs
            'provider': None,
            'fallback': 'keyword_search'
        }
    
    def _check_text_generation(self) -> Dict:
        """Check for text generation capabilities."""
        return {
            'available': True,  # Basic text processing always available
            'provider': 'basic',
            'fallback': 'template_responses'
        }
    
    def _check_document_processing(self) -> Dict:
        """Check for document processing capabilities."""
        return {
            'available': True,  # Basic text processing available
            'formats': ['txt', 'md'],
            'fallback': 'simple_text_extraction'
        }
    
    def _check_vector_search(self) -> Dict:
        """Check for vector search capabilities."""
        return {
            'available': False,  # Would check for vector databases
            'provider': None,
            'fallback': 'keyword_search'
        }
    
    def get_capability(self, capability_name: str) -> Dict:
        """Get information about a specific capability."""
        if not self.capabilities or self._should_refresh():
            self.detect_capabilities()
        
        return self.capabilities.get(capability_name, {'available': False})
    
    def register_fallback_handler(self, capability: str, handler: Callable):
        """Register a fallback handler for a capability."""
        self.fallback_handlers[capability] = handler
    
    def execute_with_fallback(self, capability: str, primary_func: Callable, *args, **kwargs):
        """Execute function with fallback if capability is not available."""
        capability_info = self.get_capability(capability)
        
        if capability_info.get('available', False):
            try:
                return primary_func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Primary function failed for {capability}: {e}")
        
        # Use fallback
        fallback_handler = self.fallback_handlers.get(capability)
        if fallback_handler:
            return fallback_handler(*args, **kwargs)
        else:
            raise RuntimeError(f"Capability {capability} not available and no fallback registered")
    
    def _should_refresh(self) -> bool:
        """Check if capabilities should be refreshed."""
        if not self.last_check:
            return True
        
        time_since_check = (datetime.now() - self.last_check).total_seconds()
        return time_since_check > self.check_interval


# Global instances
ai_integration = {
    'chunker': DocumentChunker(),
    'context_manager': SlidingWindowManager(),
    'rag_system': PriorityRAG(),
    'query_planner': QueryPlanner(),
    'capability_detector': AICapabilityDetector()
}


def get_ai_integration() -> Dict:
    """Get the global AI integration components."""
    return ai_integration
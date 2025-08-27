"""Advanced query optimization strategies for repository pattern."""

import logging
from typing import Dict, Any, List, Optional, Type, Union
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, Index
from sqlalchemy.orm import Query
from sqlalchemy.engine import Result

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Advanced query optimization strategies for the repository pattern."""
    
    def __init__(self):
        self._query_cache: Dict[str, Any] = {}
        self._cache_stats = {"hits": 0, "misses": 0, "size": 0}
        self._max_cache_size = 1000
        self._cache_ttl = 300  # 5 minutes
    
    def cache_key(self, query: str, params: Dict[str, Any] = None) -> str:
        """Generate cache key for query and parameters."""
        if params:
            # Sort params for consistent hashing
            sorted_params = json.dumps(params, sort_keys=True)
            cache_string = f"{query}::{sorted_params}"
        else:
            cache_string = query
        
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def should_cache_query(self, query: str) -> bool:
        """Determine if a query should be cached based on patterns."""
        cache_indicators = [
            "SELECT COUNT",
            "GROUP BY",
            "ORDER BY",
            "WHERE.*is_active = true",
            "JOIN.*JOIN",  # Multi-table joins
            "DISTINCT"
        ]
        
        avoid_cache_indicators = [
            "INSERT",
            "UPDATE", 
            "DELETE",
            "last_activity_at",
            "created_at >",
            "timestamp"
        ]
        
        query_upper = query.upper()
        
        # Don't cache queries with time-sensitive data
        for indicator in avoid_cache_indicators:
            if indicator.upper() in query_upper:
                return False
        
        # Cache queries with expensive operations
        for indicator in cache_indicators:
            if indicator.upper() in query_upper:
                return True
        
        return False
    
    async def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if available and not expired."""
        if cache_key not in self._query_cache:
            self._cache_stats["misses"] += 1
            return None
        
        cached_data = self._query_cache[cache_key]
        
        # Check if cache entry is expired
        if datetime.utcnow() - cached_data["timestamp"] > timedelta(seconds=self._cache_ttl):
            del self._query_cache[cache_key]
            self._cache_stats["misses"] += 1
            return None
        
        self._cache_stats["hits"] += 1
        return cached_data["result"]
    
    async def cache_result(self, cache_key: str, result: Any) -> None:
        """Cache query result with timestamp."""
        # Implement LRU eviction if cache is full
        if len(self._query_cache) >= self._max_cache_size:
            # Remove oldest entries (simple FIFO for now)
            oldest_key = min(
                self._query_cache.keys(),
                key=lambda k: self._query_cache[k]["timestamp"]
            )
            del self._query_cache[oldest_key]
        
        self._query_cache[cache_key] = {
            "result": result,
            "timestamp": datetime.utcnow()
        }
        self._cache_stats["size"] = len(self._query_cache)
    
    def clear_cache(self, pattern: Optional[str] = None) -> None:
        """Clear cache entries, optionally matching a pattern."""
        if pattern is None:
            self._query_cache.clear()
            self._cache_stats["size"] = 0
        else:
            keys_to_remove = [
                key for key in self._query_cache.keys()
                if pattern in key
            ]
            for key in keys_to_remove:
                del self._query_cache[key]
            self._cache_stats["size"] = len(self._query_cache)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (self._cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "hit_rate": round(hit_rate, 2),
            "cache_size": self._cache_stats["size"],
            "max_size": self._max_cache_size
        }


def cached_query(ttl: int = 300):
    """Decorator for caching query results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Generate cache key based on method name and arguments
            cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # Check if we have a cached result
            if hasattr(self, '_optimizer'):
                cached_result = await self._optimizer.get_cached_result(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result
            
            # Execute the original function
            result = await func(self, *args, **kwargs)
            
            # Cache the result if we have an optimizer
            if hasattr(self, '_optimizer'):
                await self._optimizer.cache_result(cache_key, result)
                logger.debug(f"Cached result for {func.__name__}")
            
            return result
        return wrapper
    return decorator


class IndexRecommendation:
    """Generate database index recommendations based on query patterns."""
    
    def __init__(self):
        self._query_patterns: List[Dict[str, Any]] = []
        self._table_access_patterns: Dict[str, Dict[str, int]] = {}
    
    def record_query_pattern(self, table: str, columns: List[str], query_type: str, frequency: int = 1):
        """Record a query pattern for analysis."""
        pattern = {
            "table": table,
            "columns": columns,
            "query_type": query_type,
            "frequency": frequency,
            "timestamp": datetime.utcnow()
        }
        self._query_patterns.append(pattern)
        
        # Update table access patterns
        if table not in self._table_access_patterns:
            self._table_access_patterns[table] = {}
        
        column_key = ",".join(sorted(columns))
        self._table_access_patterns[table][column_key] = (
            self._table_access_patterns[table].get(column_key, 0) + frequency
        )
    
    def get_index_recommendations(self, min_frequency: int = 5) -> List[Dict[str, Any]]:
        """Get index recommendations based on recorded patterns."""
        recommendations = []
        
        for table, column_patterns in self._table_access_patterns.items():
            for column_key, frequency in column_patterns.items():
                if frequency >= min_frequency:
                    columns = column_key.split(",")
                    
                    # Determine index type based on patterns
                    index_type = "btree"  # Default
                    if len(columns) == 1:
                        column = columns[0]
                        if any(
                            pattern in column.lower() 
                            for pattern in ["name", "title", "content", "description"]
                        ):
                            index_type = "gin"  # For text search
                    
                    recommendation = {
                        "table": table,
                        "columns": columns,
                        "frequency": frequency,
                        "index_type": index_type,
                        "priority": self._calculate_priority(frequency, len(columns)),
                        "estimated_benefit": self._estimate_benefit(frequency, len(columns))
                    }
                    recommendations.append(recommendation)
        
        # Sort by priority (highest first)
        recommendations.sort(key=lambda x: x["priority"], reverse=True)
        return recommendations
    
    def _calculate_priority(self, frequency: int, column_count: int) -> float:
        """Calculate index priority score."""
        # Higher frequency = higher priority
        # Single column indexes are generally more beneficial
        base_score = frequency * 10
        column_penalty = (column_count - 1) * 2  # Multi-column indexes are more expensive
        return max(base_score - column_penalty, 1)
    
    def _estimate_benefit(self, frequency: int, column_count: int) -> str:
        """Estimate the benefit of creating this index."""
        if frequency > 50:
            return "HIGH"
        elif frequency > 20:
            return "MEDIUM" if column_count <= 2 else "LOW"
        elif frequency > 10:
            return "LOW"
        else:
            return "MINIMAL"


class QueryProfiler:
    """Profile query performance and identify optimization opportunities."""
    
    def __init__(self):
        self._query_stats: Dict[str, Dict[str, Any]] = {}
        self._slow_queries: List[Dict[str, Any]] = []
        self._slow_query_threshold = 1.0  # 1 second
    
    async def profile_query(self, query: str, execution_time: float, result_count: int = 0):
        """Record query execution statistics."""
        query_hash = hashlib.md5(query.encode()).hexdigest()[:12]
        
        if query_hash not in self._query_stats:
            self._query_stats[query_hash] = {
                "query": query[:200] + "..." if len(query) > 200 else query,
                "total_time": 0.0,
                "execution_count": 0,
                "avg_time": 0.0,
                "max_time": 0.0,
                "min_time": float('inf'),
                "total_results": 0
            }
        
        stats = self._query_stats[query_hash]
        stats["total_time"] += execution_time
        stats["execution_count"] += 1
        stats["avg_time"] = stats["total_time"] / stats["execution_count"]
        stats["max_time"] = max(stats["max_time"], execution_time)
        stats["min_time"] = min(stats["min_time"], execution_time)
        stats["total_results"] += result_count
        
        # Record slow queries
        if execution_time > self._slow_query_threshold:
            self._slow_queries.append({
                "query": query,
                "execution_time": execution_time,
                "result_count": result_count,
                "timestamp": datetime.utcnow()
            })
            
            # Keep only recent slow queries (last 100)
            self._slow_queries = self._slow_queries[-100:]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not self._query_stats:
            return {"message": "No query statistics available"}
        
        # Find top slow queries by average time
        slowest_queries = sorted(
            self._query_stats.values(),
            key=lambda x: x["avg_time"],
            reverse=True
        )[:10]
        
        # Find most frequent queries
        frequent_queries = sorted(
            self._query_stats.values(),
            key=lambda x: x["execution_count"],
            reverse=True
        )[:10]
        
        # Calculate overall statistics
        total_queries = sum(stats["execution_count"] for stats in self._query_stats.values())
        total_time = sum(stats["total_time"] for stats in self._query_stats.values())
        avg_query_time = total_time / total_queries if total_queries > 0 else 0
        
        return {
            "overview": {
                "unique_queries": len(self._query_stats),
                "total_executions": total_queries,
                "total_time": round(total_time, 3),
                "average_query_time": round(avg_query_time, 3),
                "slow_queries_count": len([q for q in self._slow_queries if q["timestamp"] > datetime.utcnow() - timedelta(hours=24)])
            },
            "slowest_queries": [
                {
                    "query": q["query"],
                    "avg_time": round(q["avg_time"], 3),
                    "max_time": round(q["max_time"], 3),
                    "execution_count": q["execution_count"]
                }
                for q in slowest_queries
            ],
            "most_frequent_queries": [
                {
                    "query": q["query"],
                    "execution_count": q["execution_count"],
                    "avg_time": round(q["avg_time"], 3),
                    "total_time": round(q["total_time"], 3)
                }
                for q in frequent_queries
            ],
            "recent_slow_queries": [
                {
                    "query": q["query"][:100] + "..." if len(q["query"]) > 100 else q["query"],
                    "execution_time": round(q["execution_time"], 3),
                    "timestamp": q["timestamp"].isoformat()
                }
                for q in self._slow_queries[-10:]
            ]
        }
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Generate query optimization suggestions."""
        suggestions = []
        
        # Analyze query patterns for common issues
        for stats in self._query_stats.values():
            query = stats["query"].upper()
            
            # Suggest indexes for frequent WHERE clauses
            if stats["execution_count"] > 10 and "WHERE" in query:
                suggestions.append({
                    "type": "INDEX",
                    "priority": "HIGH" if stats["avg_time"] > 0.5 else "MEDIUM",
                    "query": stats["query"][:100] + "...",
                    "suggestion": "Consider adding index on WHERE clause columns",
                    "execution_count": stats["execution_count"],
                    "avg_time": round(stats["avg_time"], 3)
                })
            
            # Suggest query rewriting for slow queries
            if stats["avg_time"] > 1.0:
                suggestions.append({
                    "type": "REWRITE",
                    "priority": "HIGH",
                    "query": stats["query"][:100] + "...",
                    "suggestion": "Query is consistently slow - consider rewriting or optimization",
                    "avg_time": round(stats["avg_time"], 3)
                })
            
            # Suggest LIMIT clauses for queries returning many results
            if stats["total_results"] / max(stats["execution_count"], 1) > 1000:
                suggestions.append({
                    "type": "LIMIT",
                    "priority": "MEDIUM",
                    "query": stats["query"][:100] + "...",
                    "suggestion": "Consider adding LIMIT clause - query returns many results",
                    "avg_results": round(stats["total_results"] / stats["execution_count"])
                })
        
        return sorted(suggestions, key=lambda x: {"HIGH": 3, "MEDIUM": 2, "LOW": 1}[x["priority"]], reverse=True)


# Global instances for application-wide use
query_optimizer = QueryOptimizer()
index_recommender = IndexRecommendation()
query_profiler = QueryProfiler()


async def create_recommended_indexes(session: AsyncSession, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create database indexes based on recommendations."""
    created_indexes = []
    failed_indexes = []
    
    for rec in recommendations:
        if rec["priority"] < 50:  # Skip low-priority recommendations
            continue
        
        table = rec["table"]
        columns = rec["columns"]
        index_type = rec.get("index_type", "btree")
        
        # Generate index name
        index_name = f"idx_{table}_{'_'.join(columns)}"
        
        try:
            # Create index SQL
            if index_type == "gin":
                # For text search indexes
                index_sql = f"""
                CREATE INDEX IF NOT EXISTS {index_name} 
                ON {table} USING gin(to_tsvector('english', {columns[0]}))
                """
            else:
                # Standard btree index
                column_list = ", ".join(columns)
                index_sql = f"""
                CREATE INDEX IF NOT EXISTS {index_name} 
                ON {table} ({column_list})
                """
            
            await session.execute(text(index_sql))
            await session.commit()
            
            created_indexes.append({
                "index_name": index_name,
                "table": table,
                "columns": columns,
                "type": index_type
            })
            
            logger.info(f"Created index: {index_name}")
            
        except Exception as e:
            failed_indexes.append({
                "index_name": index_name,
                "table": table,
                "columns": columns,
                "error": str(e)
            })
            logger.error(f"Failed to create index {index_name}: {e}")
    
    return {
        "created": created_indexes,
        "failed": failed_indexes,
        "total_recommendations": len(recommendations),
        "created_count": len(created_indexes),
        "failed_count": len(failed_indexes)
    }
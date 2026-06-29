import json
import re
import time
import httpx
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel, Field
from app.core.config import settings

class RewrittenQueryPayload(BaseModel):
    normalized_query: str = Field(..., description="Legal statutory formulation of the query")
    legal_synonyms: List[str] = Field(default_factory=list, description="Statutory keywords")
    expanded_queries: List[str] = Field(default_factory=list, description="Alternative vector queries")

class ProductionQueryRewriterService:
    """
    Production-grade query rewriter with sub-millisecond static mapping,
    TTL caching, regex-based robust JSON parsing, and circuit breakers.
    """
    
    STATIC_LEGAL_MAP: Dict[str, str] = {
        "metro": "Transit-Oriented Development (TOD) station corridors",
        "metro station": "Transit-Oriented Development (TOD) Under Regulation 33(2)",
        "far": "Floor Space Index (FSI)",
        "cess building": "Redevelopment of Cess Buildings under Regulation 33(7)",
        "slum": "Slum Rehabilitation Scheme under Regulation 33(10)",
        "fungible": "Fungible Compensatory Area under Regulation 31(3)",
        "cluster": "Reconstruction or Redevelopment of Cluster(s) under Regulation 33(9)"
    }

    _ttl_cache: Dict[str, Tuple[RewrittenQueryPayload, float]] = {}
    _circuit_open: bool = False
    _last_failure_time: float = 0.0

    @classmethod
    def _extract_json_robustly(cls, text: str) -> Dict:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {}

    @classmethod
    async def rewrite_query_async(cls, raw_query: str, history_context: str = "") -> RewrittenQueryPayload:
        clean_q = raw_query.strip().lower()

        # 1. Quick-Win Lookup (0ms)
        for key, mapped_term in cls.STATIC_LEGAL_MAP.items():
            if key in clean_q:
                normalized = re.sub(re.escape(key), mapped_term, raw_query, flags=re.IGNORECASE)
                return RewrittenQueryPayload(
                    normalized_query=normalized,
                    legal_synonyms=[mapped_term],
                    expanded_queries=[normalized, raw_query]
                )

        # 2. Check TTL Memory Cache (5 minutes)
        now = time.time()
        if clean_q in cls._ttl_cache:
            payload, timestamp = cls._ttl_cache[clean_q]
            if now - timestamp < 300:
                return payload

        # 3. Circuit Breaker Check
        if cls._circuit_open:
            if now - cls._last_failure_time < 60:
                return RewrittenQueryPayload(normalized_query=raw_query, expanded_queries=[raw_query])
            else:
                cls._circuit_open = False

        # 4. Asynchronous LLM Query Rewriting
        prompt = f"""You are an expert legal term rewriter for Mumbai DCPR 2034.
CONVERSATION CONTEXT: {history_context if history_context else "None"}
USER QUERY: "{raw_query}"

Return ONLY a raw JSON object matching:
{{"normalized_query": "statutory version", "legal_synonyms": ["term1"], "expanded_queries": ["alt1", "alt2"]}}"""

        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1, "num_predict": 300}
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(settings.OLLAMA_URL, json=payload)
                if res.status_code == 200:
                    body = res.json()
                    raw_text = body.get("response") or body.get("thinking") or "{}"
                    parsed_dict = cls._extract_json_robustly(raw_text)
                    if parsed_dict:
                        result = RewrittenQueryPayload(**parsed_dict)
                        cls._ttl_cache[clean_q] = (result, now)
                        return result
        except Exception as e:
            print(f"[CircuitBreaker] Query rewriter error: {e}")
            cls._circuit_open = True
            cls._last_failure_time = now

        return RewrittenQueryPayload(normalized_query=raw_query, expanded_queries=[raw_query])

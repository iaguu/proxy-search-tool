import os
import time
from typing import List, Dict, Optional

import requests

from .proxy_manager import ProxyManager


class SearchResult:
    def __init__(self, url: str, title: str = "", snippet: str = "") -> None:
        self.url = url
        self.title = title
        self.snippet = snippet

    def __repr__(self) -> str:
        return f"<SearchResult url={self.url!r}>"


class GoogleSearchClient:
    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(
        self,
        api_key: Optional[str],
        cx: Optional[str],
        proxy_manager: Optional[ProxyManager] = None,
        user_agent: str = "ProxySearchTool/1.0",
    ) -> None:
        self.api_key = api_key
        self.cx = cx
        self.proxy_manager = proxy_manager
        self.user_agent = user_agent

    def is_configured(self) -> bool:
        return bool(self.api_key and self.cx)

    def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        if not self.is_configured():
            print("[GoogleSearchClient] Não configurado (GOOGLE_API_KEY/GOOGLE_CX faltando).")
            return []

        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": min(max_results, 10),
        }

        session = requests.Session()
        session.headers.update({"User-Agent": self.user_agent})

        kwargs = {}
        if self.proxy_manager:
            kwargs = self.proxy_manager.as_requests_kwargs()

        print(f"[GoogleSearchClient] Buscando: {query!r}")
        resp = session.get(self.BASE_URL, params=params, timeout=10, **kwargs)
        if resp.status_code != 200:
            print(f"[GoogleSearchClient] Erro HTTP {resp.status_code}: {resp.text[:200]}")
            return []

        data = resp.json()
        items = data.get("items", []) or []
        results: List[SearchResult] = []
        for item in items:
            url = item.get("link", "")
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            if url:
                results.append(SearchResult(url=url, title=title, snippet=snippet))
        print(f"[GoogleSearchClient] {len(results)} resultados obtidos.")
        return results


class DirectURLClient:
    """Cliente que apenas retorna a URL informada na query (engine=direct)."""

    def search(self, url: str, max_results: int = 1) -> List[SearchResult]:
        return [SearchResult(url=url)]

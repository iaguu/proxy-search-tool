import os
import time
import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict

import requests


class ProxyValidationResult:
    def __init__(self, proxy: str, ok: bool, latency_ms: Optional[float] = None, error: Optional[str] = None):
        self.proxy = proxy
        self.ok = ok
        self.latency_ms = latency_ms
        self.error = error or ""

    def score(self) -> float:
        if not self.ok or self.latency_ms is None:
            return float("inf")
        # Quanto menor a latência, melhor. Usamos ms diretamente como score.
        return self.latency_ms

    def __repr__(self) -> str:
        return f"<ProxyValidationResult proxy={self.proxy!r} ok={self.ok} latency_ms={self.latency_ms}>"


class ProxyManager:
    def __init__(
        self,
        proxies_file: str,
        settings: Dict,
        user_agent: Optional[str] = None,
    ) -> None:
        self.proxies_file = proxies_file
        self.settings = settings
        self.test_url = settings.get("test_url", "https://httpbin.org/ip")
        self.timeout = settings.get("proxy_timeout_seconds", 4)
        self.concurrency = settings.get("proxy_concurrency", 20)
        self.min_successful = settings.get("min_successful_proxies", 5)
        self.max_validated = settings.get("max_validated_proxies", 50)
        self.user_agent = user_agent or settings.get("user_agent", "ProxySearchTool/1.0")
        self._lock = threading.Lock()
        self._proxies: List[str] = []
        self._validated: List[ProxyValidationResult] = []
        self._idx = 0

    def load_proxies(self) -> List[str]:
        if not os.path.exists(self.proxies_file):
            print(f"[ProxyManager] Arquivo de proxies não encontrado: {self.proxies_file}. Seguiremos sem proxies.")
            self._proxies = []
            return self._proxies

        proxies: List[str] = []
        with open(self.proxies_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                proxies.append(line)
        random.shuffle(proxies)
        self._proxies = proxies
        print(f"[ProxyManager] {len(self._proxies)} proxies carregados de {self.proxies_file}.")
        return self._proxies

    def _to_requests_proxy(self, proxy_line: str) -> Dict[str, str]:
        # Aceita tanto ip:porta quanto user:pass@ip:porta
        if "://" in proxy_line:
            proxy_url = proxy_line
        else:
            proxy_url = f"http://{proxy_line}"
        return {"http": proxy_url, "https": proxy_url}

    def _validate_single(self, proxy_line: str) -> ProxyValidationResult:
        session = requests.Session()
        session.headers.update({"User-Agent": self.user_agent})
        proxies = self._to_requests_proxy(proxy_line)
        started = time.time()
        try:
            resp = session.get(self.test_url, timeout=self.timeout, proxies=proxies)
            elapsed_ms = (time.time() - started) * 1000.0
            if 200 <= resp.status_code < 400:
                print(f"[ProxyManager] OK {proxy_line} ({elapsed_ms:.0f} ms)")
                return ProxyValidationResult(proxy=proxy_line, ok=True, latency_ms=elapsed_ms)
            else:
                err = f"status={resp.status_code}"
                print(f"[ProxyManager] FAIL {proxy_line} -> {err}")
                return ProxyValidationResult(proxy=proxy_line, ok=False, latency_ms=None, error=err)
        except requests.RequestException as e:
            err = str(e)
            print(f"[ProxyManager] ERROR {proxy_line} -> {err}")
            return ProxyValidationResult(proxy=proxy_line, ok=False, latency_ms=None, error=err)

    def validate_proxies(self) -> List[str]:
        if not self._proxies:
            self.load_proxies()

        if not self._proxies:
            print("[ProxyManager] Nenhum proxy para validar. Rodando sem proxies.")
            self._validated = []
            return []

        sample = self._proxies[: self.max_validated]
        print(f"[ProxyManager] Validando até {len(sample)} proxies (máx={self.max_validated})...")
        results: List[ProxyValidationResult] = []

        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = {executor.submit(self._validate_single, p): p for p in sample}
            for fut in as_completed(futures):
                res = fut.result()
                results.append(res)

        valid = [r for r in results if r.ok]
        valid.sort(key=lambda r: r.score())
        self._validated = valid

        print(f"[ProxyManager] {len(valid)} proxies válidos encontrados.")
        if len(valid) < self.min_successful:
            print(f"[ProxyManager] Aviso: somente {len(valid)} proxies válidos (< min {self.min_successful}).")

        return [r.proxy for r in valid]

    def next_proxy(self) -> Optional[str]:
        with self._lock:
            if not self._validated:
                return None
            proxy = self._validated[self._idx % len(self._validated)].proxy
            self._idx += 1
            return proxy

    def as_requests_kwargs(self) -> Dict[str, Dict[str, str]]:
        proxy = self.next_proxy()
        if not proxy:
            return {}
        if "://" in proxy:
            proxy_url = proxy
        else:
            proxy_url = f"http://{proxy}"
        return {"proxies": {"http": proxy_url, "https": proxy_url}}

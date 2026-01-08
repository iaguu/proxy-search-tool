import os
import json
from typing import List, Tuple

from .proxy_manager import ProxyManager
from .search_clients import GoogleSearchClient, DirectURLClient
from .file_downloader import FileDownloader


CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "settings.json")


def load_settings() -> dict:
    if not os.path.exists(SETTINGS_PATH):
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {SETTINGS_PATH}")
    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_queries(path: str) -> List[Tuple[str, str, int, str]]:
    """Carrega queries no formato: engine;query;max_results;download_subdir"""
    queries: List[Tuple[str, str, int, str]] = []
    if not os.path.exists(path):
        print(f"[Main] Arquivo de queries não encontrado: {path}")
        return queries

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(";")]
            if len(parts) < 2:
                continue
            engine = parts[0]
            query = parts[1]
            max_results = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 5
            download_subdir = parts[3] if len(parts) >= 4 and parts[3] else engine
            queries.append((engine, query, max_results, download_subdir))
    return queries


def main() -> None:
    settings = load_settings()
    user_agent = settings.get("user_agent", "ProxySearchTool/1.0")

    proxies_file = os.path.join(CONFIG_DIR, "proxies.txt")
    queries_file = os.path.join(CONFIG_DIR, "queries.txt")
    downloads_base = settings.get("downloads_base_dir", "downloads")

    # 1) Carregar & validar proxies
    proxy_manager = ProxyManager(proxies_file=proxies_file, settings=settings, user_agent=user_agent)
    proxy_manager.load_proxies()
    proxy_manager.validate_proxies()

    # 2) Montar clientes de busca
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cx = os.getenv("GOOGLE_CX")

    google_client = GoogleSearchClient(
        api_key=google_api_key,
        cx=google_cx,
        proxy_manager=proxy_manager,
        user_agent=user_agent,
    )
    direct_client = DirectURLClient()

    # 3) Downloader
    downloader = FileDownloader(base_download_dir=downloads_base, proxy_manager=proxy_manager, user_agent=user_agent)

    # 4) Carregar queries
    queries = load_queries(queries_file)
    if not queries:
        print("[Main] Nenhuma query carregada. Ajuste config/queries.txt e tente novamente.")
        return

    # 5) Executar cada query
    for engine, query, max_results, subdir in queries:
        print(f"\n[Main] Executando query: engine={engine}, query={query!r}, max_results={max_results}, subdir={subdir}")

        if engine == "google":
            if not google_client.is_configured():
                print("[Main] Google não configurado (GOOGLE_API_KEY/GOOGLE_CX). Pulando esta query.")
                continue
            results = google_client.search(query=query, max_results=max_results)
        elif engine == "direct":
            results = direct_client.search(url=query, max_results=max_results)
        else:
            print(f"[Main] Engine desconhecida: {engine}. Pulando.")
            continue

        for res in results:
            print(f"[Main] Resultado: {res.url}")
            # Aqui fazemos o download – você pode alterar este comportamento
            downloader.download(res.url, subdir=subdir)


if __name__ == "__main__":
    main()

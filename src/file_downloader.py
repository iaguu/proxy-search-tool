import os
import time
from typing import Optional, Dict

import requests

from .proxy_manager import ProxyManager


class FileDownloader:
    def __init__(
        self,
        base_download_dir: str,
        proxy_manager: Optional[ProxyManager] = None,
        user_agent: str = "ProxySearchTool/1.0",
    ) -> None:
        self.base_download_dir = base_download_dir
        self.proxy_manager = proxy_manager
        self.user_agent = user_agent

    def _ensure_dir(self, subdir: str) -> str:
        out_dir = os.path.join(self.base_download_dir, subdir)
        os.makedirs(out_dir, exist_ok=True)
        return out_dir

    def _get_filename_from_url(self, url: str) -> str:
        # Simples: último segmento da URL, sem query string
        from urllib.parse import urlparse, unquote

        parsed = urlparse(url)
        path = parsed.path
        name = os.path.basename(path) or "downloaded_file"
        return unquote(name)

    def download(self, url: str, subdir: str = "default") -> Optional[str]:
        out_dir = self._ensure_dir(subdir)
        filename = self._get_filename_from_url(url)
        dest_path = os.path.join(out_dir, filename)

        session = requests.Session()
        session.headers.update({"User-Agent": self.user_agent})

        kwargs: Dict = {}
        if self.proxy_manager:
            kwargs = self.proxy_manager.as_requests_kwargs()

        print(f"[Downloader] Baixando: {url} -> {dest_path}")
        try:
            with session.get(url, stream=True, timeout=20, **kwargs) as r:
                r.raise_for_status()
                with open(dest_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        f.write(chunk)
            print("[Downloader] OK")
            return dest_path
        except Exception as e:
            print(f"[Downloader] Erro ao baixar {url}: {e}")
            return None

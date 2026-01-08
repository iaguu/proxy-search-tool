# Proxy Search Tool (Lícito)

Ferramenta genérica para:
- Validar proxies HTTP/HTTPS listados em `config/proxies.txt`
- Usar estes proxies (opcionalmente) para fazer buscas totalmente lícitas
  via Google Custom Search API e downloads de URLs explícitas definidas em `config/queries.txt`.

A ferramenta **não faz scraping agressivo** e **não é feita para procurar vazamentos de dados**.
O objetivo é uso legítimo: monitorar arquivos próprios, espelhos de download autorizados,
documentação pública etc.

## Estrutura

- `src/proxy_manager.py` — Carrega e valida proxies, gera um pool de proxies utilizáveis.
- `src/search_clients.py` — Implementa o cliente de busca (Google Custom Search API) e o
  cliente "direct" para URLs explícitas.
- `src/file_downloader.py` — Funções de download seguro de arquivos.
- `src/main.py` — Orquestrador: lê configs, valida proxies e executa as queries.
- `config/proxies.txt` — Lista de proxies (um por linha).
- `config/queries.txt` — Lista de queries em formato `engine;query;max_results;download_subdir`.
- `settings.json` — Configurações gerais de tempo limite, concorrência etc.
- `downloads/` — Pasta onde os arquivos serão salvos.

## Uso

1. Crie um ambiente virtual Python (opcional, mas recomendado):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   .venv\Scripts\activate   # Windows
   ```

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure seus proxies em `config/proxies.txt` (opcional — você também pode rodar sem proxies).

4. Configure suas queries em `config/queries.txt`.

   - Para `engine=google`, defina as variáveis de ambiente:

     ```bash
     export GOOGLE_API_KEY="sua_api_key_aqui"
     export GOOGLE_CX="seu_cx_id_aqui"
     ```

5. Execute o orquestrador:

   ```bash
   python -m src.main
   ```

O script irá:

- Validar os proxies (se existirem).
- Usar o pool de proxies válidos (ou conexão direta, se você preferir) para:
  - Executar buscas via Google Custom Search API.
  - Fazer download de URLs explícitas definidas com `engine=direct`.

## Aviso Legal

- Respeite os Termos de Serviço de cada serviço/API que você utilizar (Google, provedores de download, etc.).
- Use a ferramenta apenas para fins lícitos: auditoria de seus próprios conteúdos, download de arquivos
  que você está autorizado a obter, pesquisa de documentação pública, etc.
- Você é o único responsável pelo uso desta ferramenta.

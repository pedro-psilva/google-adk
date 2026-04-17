# google-adk

Automacao da Analise de Perfil do IEBT.

## Visao geral

Este projeto:

- recebe os arquivos de entrada da analise de perfil;
- normaliza esses dados em um bundle unico;
- executa o pipeline principal via ADK;
- gera o relatorio final em `.xlsx`;
- gera o relatorio final em `.pdf` a partir da propria planilha final.

O PDF final nao usa fallback alternativo. A entrega oficial sempre precisa ser fiel ao template do Excel.

Guia de deploy em producao:

- [`DEPLOY.md`](DEPLOY.md)

## Requisitos

### Execucao local no Windows

- Python com as dependencias do `requirements.txt`
- Node.js e npm
- Microsoft Excel instalado no host Windows

### Execucao via Docker

- Docker Desktop
- host Windows com Microsoft Excel instalado
- worker Windows de exportacao PDF ativo

## Como iniciar localmente

Use sempre os scripts da raiz do repositorio.

### Subir backend e frontend juntos

Na raiz do projeto:

```powershell
cmd.exe /c scripts\start_local_stack.cmd
```

Servicos esperados:

- backend: `http://127.0.0.1:8000`
- healthcheck backend: `http://127.0.0.1:8000/healthz`
- frontend: `http://127.0.0.1:4173`

Logs gerados na raiz:

- `backend.log`
- `frontend.log`

### Subir apenas o backend

```powershell
cmd.exe /c scripts\start_backend_local.cmd
```

### Subir apenas o frontend

```powershell
cmd.exe /c scripts\start_frontend_local.cmd
```

### Como o PDF funciona no modo local

Quando o backend roda localmente no Windows, ele exporta o PDF final diretamente pelo Microsoft Excel a partir da aba `Sintese`. Nesse modo, o worker HTTP de PDF nao e obrigatorio.

## Como iniciar com Docker

Quando o backend roda em container Linux, ele nao consegue gerar um PDF fiel ao Excel sozinho. Por isso, o container delega a exportacao final para um worker Windows com Excel.

### 1. Subir o worker Windows de PDF

Na raiz do projeto:

```powershell
cmd.exe /c scripts\start_pdf_export_worker.cmd
```

Endpoint esperado:

- `http://127.0.0.1:8010/healthz`

Log gerado:

- `pdf-export-worker.log`

### 2. Subir a stack Docker

Com o worker ativo:

```powershell
docker compose up --build
```

Configuracao padrao usada pelo backend em Docker:

- `PDF_EXPORT_WORKER_URL=http://host.docker.internal:8010`
- `PDF_EXPORT_WORKER_TIMEOUT_SECONDS=180`

Se o worker Windows nao estiver disponivel, o pipeline falha explicitamente na etapa do PDF. Isso e intencional para evitar a entrega de um PDF desalinhado ou diferente do template do Excel.

## Fluxo principal

1. Abrir o frontend em `http://127.0.0.1:4173`
2. Enviar os arquivos de entrada
3. Executar o pipeline
4. Baixar o `.xlsx` final
5. Baixar o `.pdf` final

## Entradas esperadas

- PDF do `NEO PI-R`
- PDF do `Profiler`
- planilha de `Ancoras de Carreira + Diagnostico de Cultura`
- planilha modelo do relatorio final, quando necessario para cache do template

## Saidas esperadas

- relatorio final em `.xlsx`
- relatorio final em `.pdf`
- artefatos intermediarios em `artifacts/`

## Comportamentos importantes

- O fluxo padrao do backend usa `draft_mode=preview` no uso local.
- O PDF final precisa vir da planilha final preenchida.
- O fallback de PDF alternativo foi removido de proposito.
- Em Docker, a fidelidade do PDF depende do worker Windows com Excel.
- Se houver processos antigos ocupando `8000` ou `4173`, reinicie o stack antes de testar.

## Scripts uteis

- [`scripts/start_local_stack.cmd`](scripts/start_local_stack.cmd): sobe backend e frontend localmente
- [`scripts/start_backend_local.cmd`](scripts/start_backend_local.cmd): sobe apenas o backend local
- [`scripts/start_frontend_local.cmd`](scripts/start_frontend_local.cmd): sobe apenas o frontend local
- [`scripts/start_pdf_export_worker.cmd`](scripts/start_pdf_export_worker.cmd): sobe o worker Windows de exportacao PDF
- [`scripts/serve_backend_api.py`](scripts/serve_backend_api.py): publica a API FastAPI
- [`scripts/serve_pdf_export_worker.py`](scripts/serve_pdf_export_worker.py): publica o worker HTTP de PDF
- [`scripts/export_excel_sheet_to_pdf.ps1`](scripts/export_excel_sheet_to_pdf.ps1): exporta a aba `Sintese` do Excel para PDF
- [`scripts/run_backend_pipeline.py`](scripts/run_backend_pipeline.py): executa o pipeline pela linha de comando

## Configuracao

As variaveis-base do backend estao em [`.env.example`](.env.example).

As mais relevantes para o fluxo atual sao:

- `APP_ENV`
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `VERTEX_MODEL`
- `PDF_EXPORT_WORKER_URL`
- `PDF_EXPORT_WORKER_TIMEOUT_SECONDS`

## Testes

Para validar os testes unitarios atuais:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

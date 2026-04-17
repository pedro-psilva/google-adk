# google-adk

Automacao da Analise de Perfil do IEBT.

## Visao geral

Esta branch funciona sem Microsoft Excel e sem worker Windows.

O pipeline atual:

- recebe os arquivos de entrada da analise de perfil;
- normaliza os dados em um bundle unico;
- executa o pipeline principal via ADK;
- gera o relatorio final em `.docx`;
- gera o relatorio final em `.pdf`;
- salva artefatos intermediarios em `artifacts/`.

O `.docx` e o `.pdf` sao montados diretamente em Python a partir do bundle normalizado. Nao existe dependencia de Excel para gerar a entrega final desta branch.

Guia de deploy em producao:

- [`DEPLOY.md`](DEPLOY.md)

## Requisitos

### Execucao local

- Python com as dependencias do `requirements.txt`
- Node.js e npm
- nenhuma instalacao de Microsoft Excel

### Execucao com Docker

- Docker Desktop ou Docker Engine
- nenhuma VM Windows
- nenhum worker auxiliar para PDF

## Como iniciar localmente

### Opcao 1. Subida rapida no Windows com os scripts do repositorio

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

### Opcao 2. Subida manual, sem depender de scripts `.cmd`

Backend, na raiz do projeto:

```powershell
python scripts/serve_backend_api.py
```

Frontend, em outro terminal:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 4173
```

Essa opcao e a mais simples para Linux, macOS ou qualquer ambiente que nao use os scripts `.cmd`.

## Como iniciar com Docker

Na raiz do projeto:

```powershell
docker compose up --build
```

Servicos esperados:

- backend: `http://127.0.0.1:8000`
- frontend: `http://127.0.0.1:4173`

Nesta branch, os containers `frontend` e `backend` sao suficientes. Nao existe dependencia de worker Windows nem de `PDF_EXPORT_WORKER_URL`.

## Fluxo principal

1. Abrir o frontend em `http://127.0.0.1:4173`
2. Enviar os arquivos de entrada
3. Executar o pipeline
4. Baixar o `.docx` final
5. Baixar o `.pdf` final

## Entradas esperadas

- PDF do `NEO PI-R`
- PDF do `Profiler`
- planilha de `Ancoras de Carreira + Diagnostico de Cultura`

## Saidas esperadas

- relatorio final em `.docx`
- relatorio final em `.pdf`
- artefatos intermediarios em `artifacts/`

## Comportamentos importantes

- O fluxo padrao do backend usa `draft_mode=preview` no uso local.
- O modo `preview` nao depende de Vertex AI para iniciar a aplicacao.
- O `.docx` e o `.pdf` sao entregas oficiais desta branch.
- Nao existe exportacao obrigatoria via `.xlsx`.
- Nao existe dependencia de Windows/Excel para desenvolvimento ou producao.
- Se houver processos antigos ocupando `8000` ou `4173`, reinicie o stack antes de testar.

## Scripts uteis

- [`scripts/start_local_stack.cmd`](scripts/start_local_stack.cmd): sobe backend e frontend localmente no Windows
- [`scripts/start_backend_local.cmd`](scripts/start_backend_local.cmd): sobe apenas o backend local no Windows
- [`scripts/start_frontend_local.cmd`](scripts/start_frontend_local.cmd): sobe apenas o frontend local no Windows
- [`scripts/serve_backend_api.py`](scripts/serve_backend_api.py): publica a API FastAPI
- [`scripts/run_backend_pipeline.py`](scripts/run_backend_pipeline.py): executa o pipeline pela linha de comando

## Configuracao

As variaveis-base do backend estao em [`.env.example`](.env.example).

As mais relevantes para o fluxo atual sao:

- `APP_ENV`
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `VERTEX_MODEL`

Se voce nao for usar `draft_mode=live`, as variaveis do Vertex podem ficar vazias no ambiente local.

## Testes

Para validar os testes unitarios atuais:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

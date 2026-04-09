# google-adk

Projeto de automação da Análise de Perfil do IEBT.

## O que este projeto faz

- Recebe os arquivos de entrada da análise de perfil
- Consolida os resultados em um bundle normalizado
- Roda o pipeline principal via ADK
- Gera o relatório final em `.xlsx`
- Exporta o PDF final a partir da planilha via automação do Excel no Windows

## Como o Codex deve iniciar o projeto

Use sempre os scripts locais do repositório.

### Backend

No diretório raiz do projeto:

```powershell
cmd.exe /c scripts\start_backend_local.cmd
```

Backend esperado em:

- `http://127.0.0.1:8000`
- healthcheck: `http://127.0.0.1:8000/healthz`

Logs:

- [backend.log](C:/Users/iebt/OneDrive/Desktop/Workspace/google-adk/backend.log)

### Frontend

No diretório raiz do projeto:

```powershell
cmd.exe /c scripts\start_frontend_local.cmd
```

Frontend esperado em:

- `http://127.0.0.1:4173`

Logs:

- [frontend.log](C:/Users/iebt/OneDrive/Desktop/Workspace/google-adk/frontend.log)

### Subir os dois juntos

```powershell
cmd.exe /c scripts\start_local_stack.cmd
```

## Fluxo principal para testar

1. Abrir o frontend em `http://127.0.0.1:4173`
2. Enviar os arquivos de entrada da análise
3. Rodar o pipeline
4. Baixar o `.xlsx` final
5. Baixar o `.pdf` final

## Observações importantes

- O fluxo atual é `upload -> análise -> download local`.
- O backend defaulta `draft_mode` para `preview`, para não depender de credenciais do Google Cloud no uso local.
- O PDF final é exportado da aba `Síntese` do Excel usando automação do Excel no Windows.
- Para o PDF funcionar corretamente, o ambiente precisa ter Microsoft Excel disponível para COM automation.
- Se backend ou frontend já estiverem rodando com uma versão antiga, reinicie antes de testar.

## Entradas e saída

Entradas principais:

- PDF do `NEO PI-R`
- PDF do `Profiler`
- planilha de `Âncoras de Carreira + Diagnóstico de Cultura`

Saídas principais:

- relatório final em `.xlsx`
- relatório final em `.pdf`

## Scripts úteis

- [run_backend_pipeline.py](C:/Users/iebt/OneDrive/Desktop/Workspace/google-adk/scripts/run_backend_pipeline.py): executa o pipeline direto pela linha de comando
- [serve_backend_api.py](C:/Users/iebt/OneDrive/Desktop/Workspace/google-adk/scripts/serve_backend_api.py): sobe a API FastAPI
- [export_excel_sheet_to_pdf.ps1](C:/Users/iebt/OneDrive/Desktop/Workspace/google-adk/scripts/export_excel_sheet_to_pdf.ps1): exporta a aba `Síntese` do Excel para PDF

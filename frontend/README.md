# Frontend

Interface web da plataforma de analise de perfil. Esta aplicacao roda separada do backend e consome apenas os contratos HTTP expostos pela API local.

## Stack

- React 19
- TypeScript
- Vite 7
- Organizacao de componentes em Atomic Design

## Requisitos

- Node.js
- npm
- Backend local disponivel em `http://127.0.0.1:8000`

## Execucao local

### Subida rapida da stack completa

No PowerShell, primeiro entre na raiz do repositorio e depois execute:

```powershell
cd C:\Users\iebt\OneDrive\Workspace\google-adk
.\scripts\start_local_stack.cmd
```

Se voce estiver em outra pasta, como `C:\WINDOWS\System32`, o caminho relativo acima nao vai funcionar. Nesse caso, use o caminho absoluto:

```powershell
& "C:\Users\iebt\OneDrive\Workspace\google-adk\scripts\start_local_stack.cmd"
```

Esse script abre duas janelas separadas:

- backend em `http://127.0.0.1:8000`
- frontend em `http://127.0.0.1:4173`

O backend passa a usar `.\.venv\Scripts\python.exe` automaticamente quando esse ambiente existe, entao voce nao precisa ativar a virtualenv manualmente para subir a stack.

Os logs ficam na raiz do projeto:

- `backend.log`
- `frontend.log`

### Rodar apenas o frontend

Dentro da pasta `frontend`:

```powershell
npm install
npm run dev -- --host 127.0.0.1 --port 4173
```

Aplicacao local:

- `http://127.0.0.1:4173`

## Virtualenv do backend

Se voce quiser ativar o ambiente manualmente no PowerShell, use:

```powershell
cd C:\Users\iebt\OneDrive\Workspace\google-adk
& .\.venv\Scripts\Activate.ps1
```

Se aparecer erro tentando usar `.\.venv\Scripts\activate`, o problema normalmente e o comando incorreto ou uma `.venv` quebrada. No PowerShell, prefira `Activate.ps1`.

## Variaveis de ambiente

Se precisar customizar o ambiente do frontend, copie `frontend/.env.example` para `frontend/.env`.

- `VITE_DEV_BACKEND_ORIGIN`: origem do backend usada pelo proxy do Vite em desenvolvimento. Padrao: `http://127.0.0.1:8000`
- `VITE_API_BASE_URL`: base absoluta da API fora do modo de desenvolvimento. Em desenvolvimento pode ficar vazia

## Proxy local

Durante o desenvolvimento, o Vite faz proxy das rotas abaixo para `VITE_DEV_BACKEND_ORIGIN`:

- `/api`
- `/healthz`

Isso permite que o frontend use caminhos relativos enquanto o backend roda localmente.

## Scripts disponiveis

- `npm run dev`: inicia o servidor Vite
- `npm run build`: gera o build de producao em `dist/`
- `npm run preview`: publica localmente o build gerado

## Fluxo atual da interface

1. Upload dos arquivos de entrada:
   - PDF do NEO PI-R
   - PDF do perfil comportamental
   - planilha de ancoras e diagnostico
2. Analise automatizada via backend
3. Download dos artefatos finais gerados localmente

## Observacoes

- Em desenvolvimento, o frontend usa base relativa para falar com a API.
- Se o backend nao estiver ativo, a interface exibira erro de conexao.
- Se frontend e backend forem publicados em origens diferentes, o backend ainda precisa de endurecimento de CORS em producao.

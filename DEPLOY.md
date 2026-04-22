# Deploy em Producao

Guia de deploy da branch sem dependencia de Windows, Microsoft Excel ou worker auxiliar.

## Regra principal

Nesta branch, a producao e composta apenas por:

- `frontend`
- `backend`
- volume persistente para `ARTIFACTS_ROOT`

O pipeline gera o `.docx` e o `.pdf` diretamente em Python. Nao existe dependencia de:

- host Windows;
- Microsoft Excel;
- worker HTTP de exportacao PDF;
- storage compartilhado entre Linux e Windows.

## Topologia recomendada

Arquitetura recomendada:

1. `frontend` publicado em container
2. `backend` publicado em container
3. volume persistente para `artifacts`
4. proxy reverso ou load balancer, se necessario pela sua infraestrutura

Fluxo dos artefatos:

1. o backend recebe os arquivos de entrada
2. o backend normaliza o bundle
3. o backend gera `.docx` e `.pdf`
4. os artefatos finais ficam disponiveis na arvore montada em `ARTIFACTS_ROOT`

## O que e obrigatorio

Os itens abaixo sao obrigatorios para o deploy desta branch:

- Docker Engine ou Docker Desktop
- uma imagem de backend baseada em Python
- uma imagem de frontend baseada em Node/Nginx
- volume persistente para `ARTIFACTS_ROOT`

Observacao:

- a imagem do backend agora e autocontida e builda apenas a partir da pasta `backend/`

## O que nao e necessario

Os itens abaixo nao sao mais necessarios nesta branch:

- VM Windows
- Microsoft Excel
- worker Windows
- `PDF_EXPORT_WORKER_URL`
- `PDF_EXPORT_WORKER_TIMEOUT_SECONDS`
- compartilhamento SMB entre backend e outro host

## Variaveis importantes

O backend usa principalmente:

- `APP_ENV`
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `VERTEX_MODEL`
- `ARTIFACTS_ROOT`
- `ARTIFACT_CLEANUP_ENABLED`
- `ARTIFACT_CLEANUP_INTERVAL_MINUTES`
- `DELIVERED_ARTIFACT_RETENTION_MINUTES`
- `STALE_ARTIFACT_RETENTION_HOURS`

Exemplo minimo:

```env
APP_ENV=production
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=
VERTEX_MODEL=gemini-2.5-flash
ARTIFACTS_ROOT=/data/artifacts
ARTIFACT_CLEANUP_ENABLED=true
ARTIFACT_CLEANUP_INTERVAL_MINUTES=10
DELIVERED_ARTIFACT_RETENTION_MINUTES=30
STALE_ARTIFACT_RETENTION_HOURS=6
```

Observacoes:

- o deploy sobe normalmente sem credenciais do Vertex quando o uso operacional fica em `draft_mode=preview`;
- configure credenciais do Google apenas se voce pretende usar `draft_mode=live`.

## Passo a passo de deploy

### 1. Preparar o host

No host ou VM de producao:

- instalar Docker;
- disponibilizar o codigo desta branch;
- preparar um volume persistente para `ARTIFACTS_ROOT`.

### 2. Configurar o ambiente

Na raiz do projeto, crie um `.env` com pelo menos:

```env
APP_ENV=production
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=
VERTEX_MODEL=gemini-2.5-flash
ARTIFACTS_ROOT=/data/artifacts
ARTIFACT_CLEANUP_ENABLED=true
ARTIFACT_CLEANUP_INTERVAL_MINUTES=10
DELIVERED_ARTIFACT_RETENTION_MINUTES=30
STALE_ARTIFACT_RETENTION_HOURS=6
```

Se for usar `draft_mode=live`, adicione tambem a autenticacao do Google/Vertex conforme a politica da sua infraestrutura.

### 3. Subir os containers

Na raiz do projeto:

```powershell
docker compose up -d --build
```

Servicos publicados pelo compose atual:

- backend: `http://127.0.0.1:8000`
- frontend: `http://127.0.0.1:4173`

### 4. Persistir `ARTIFACTS_ROOT`

O caminho configurado em `ARTIFACTS_ROOT` deve ficar em storage persistente.

Isso garante retencao de:

- bundles normalizados
- coverage reports
- drafts
- arquivos finais `.docx`
- arquivos finais `.pdf`

Se a sua infraestrutura usar outro caminho, ajuste o bind mount do `docker-compose.yml` e mantenha `ARTIFACTS_ROOT` consistente com ele.
O backend tambem executa limpeza automatica: uploads entregues sao removidos apos um TTL curto, e uploads/sessoes ADK abandonados sao removidos por TTL maior.

### 5. Publicar atras de proxy, se necessario

Se for expor a aplicacao publicamente, o comum e:

- manter o backend interno;
- publicar o frontend via proxy reverso;
- encaminhar chamadas `/api` para o backend.

## Healthchecks

### Backend

- `GET /healthz`

### Frontend

- raiz publicada pelo Nginx do container

## Checklist antes de liberar

1. `docker compose up -d --build` conclui sem erro
2. backend responde em `/healthz`
3. frontend responde na porta publicada
4. pipeline executa com os 3 arquivos de entrada
5. o backend gera `.docx`
6. o backend gera `.pdf`
7. os artefatos finais ficam salvos no storage montado em `ARTIFACTS_ROOT`

## Diagnostico rapido

### O backend sobe, mas o frontend nao abre

Verifique:

- build do frontend
- porta `4173`
- proxy reverso, se houver

### O frontend abre, mas a API falha

Verifique:

- healthcheck do backend
- porta `8000`
- regras de proxy/CORS da sua publicacao

### O pipeline roda, mas nao gera arquivos finais

Verifique:

- permissao de escrita em `ARTIFACTS_ROOT`
- disponibilidade das dependencias Python
- logs do backend

### Quero usar `draft_mode=live`

Nesse caso, alem do deploy padrao, verifique:

- credenciais do Google disponiveis no container do backend
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- acesso ao Vertex AI

## Recomendacao final

Para esta branch, a arquitetura oficial de producao e Linux-friendly e containerizada. Se o objetivo e operar sem Windows/Excel, o compose atual e suficiente como base de deploy e nao exige nenhum componente auxiliar fora dos containers. O unico requisito de persistencia e um storage externo ao filesystem da aplicacao, montado em `ARTIFACTS_ROOT`.

# Deploy em Producao

Guia de deploy para manter a geracao do PDF final fiel ao template do Excel.

## Regra principal

No ambiente de producao com backend em Docker/Linux, o worker Windows com Microsoft Excel e obrigatorio.

Sem esse worker:

- o backend nao consegue gerar o PDF final com fidelidade ao Excel;
- o pipeline deve falhar na etapa do PDF;
- esse comportamento e intencional para evitar a entrega de um PDF torto, desalinhado ou diferente do template oficial.

Em outras palavras: subir apenas os containers nao e suficiente para manter essa funcionalidade em producao.

## Topologia suportada

Arquitetura recomendada:

1. `frontend` publicado normalmente
2. `backend` rodando em Docker
3. `worker Windows` rodando fora do container, em uma maquina Windows com Microsoft Excel instalado
4. `storage compartilhado` entre backend e worker para a pasta de artefatos

Fluxo do PDF:

1. o backend gera o relatorio final em `.xlsx`
2. o backend chama o worker via `PDF_EXPORT_WORKER_URL`
3. o backend informa caminhos relativos dentro de `artifacts`
4. o worker abre a planilha no Excel e exporta o PDF
5. o PDF final volta a ficar disponivel na mesma arvore de `artifacts`

## O que e obrigatorio

Os itens abaixo sao obrigatorios para o PDF continuar funcionando em producao:

- um host Windows para o worker;
- Microsoft Excel instalado nesse host;
- Python e dependencias do projeto instalados nesse host;
- visibilidade compartilhada da pasta `artifacts` entre backend e worker;
- `PDF_EXPORT_WORKER_URL` configurada com a URL real do worker;
- worker monitorado como servico, com reinicio automatico.

## O que nao e suportado

Os cenarios abaixo nao mantem a funcionalidade do PDF:

- backend em Docker/Linux sem worker Windows;
- uso de LibreOffice como substituto do Excel para o PDF final;
- `host.docker.internal` como estrategia de producao padrao;
- backend e worker apontando para arvores diferentes de `artifacts`.

## Variaveis importantes

### Backend

O backend usa:

- `PDF_EXPORT_WORKER_URL`
- `PDF_EXPORT_WORKER_TIMEOUT_SECONDS`

Exemplo de producao:

```env
PDF_EXPORT_WORKER_URL=http://pdf-worker.interno:8010
PDF_EXPORT_WORKER_TIMEOUT_SECONDS=180
```

### Worker Windows

O worker usa:

- `PDF_EXPORT_ARTIFACTS_ROOT`
- `PDF_EXPORT_WORKER_HOST`
- `PDF_EXPORT_WORKER_PORT`

Exemplo:

```env
PDF_EXPORT_ARTIFACTS_ROOT=Z:\google-adk\artifacts
PDF_EXPORT_WORKER_HOST=0.0.0.0
PDF_EXPORT_WORKER_PORT=8010
```

## Storage compartilhado

Esse ponto e critico.

Hoje o backend nao envia o arquivo `.xlsx` para o worker por upload HTTP. Ele envia apenas caminhos relativos dentro de `artifacts`. Por isso, backend e worker precisam enxergar o mesmo conteudo fisico.

Exemplo valido:

- backend Docker monta `./artifacts` em `/app/artifacts`
- worker Windows aponta `PDF_EXPORT_ARTIFACTS_ROOT` para `Z:\google-adk\artifacts`
- ambos acessam os mesmos arquivos reais

Exemplo de implementacao:

- volume de rede
- compartilhamento SMB
- disco montado em ambos os lados

Se backend e worker nao compartilharem a mesma pasta de artefatos, o worker nao encontrara a planilha e o PDF falhara.

## Passo a passo de deploy

### 1. Preparar o host Windows do worker

No servidor ou VM Windows:

- instalar Microsoft Excel;
- instalar Python;
- disponibilizar acesso ao repositorio ou a um pacote de deploy do worker;
- garantir acesso ao storage compartilhado de `artifacts`.

### 2. Instalar o codigo e dependencias no worker

Na raiz do projeto no host Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configurar as variaveis do worker

Defina pelo menos:

```powershell
$env:PDF_EXPORT_ARTIFACTS_ROOT="Z:\google-adk\artifacts"
$env:PDF_EXPORT_WORKER_HOST="0.0.0.0"
$env:PDF_EXPORT_WORKER_PORT="8010"
```

### 4. Subir o worker

Para teste manual:

```powershell
cmd.exe /c scripts\start_pdf_export_worker.cmd
```

Healthcheck esperado:

- `http://127.0.0.1:8010/healthz`

Em producao, prefira rodar esse processo como servico do Windows.

Opcoes recomendadas:

- `NSSM`
- `Task Scheduler` com restart automatico
- servico dedicado de execucao da sua infraestrutura

## 5. Publicar backend e frontend

No ambiente Docker do backend:

- publicar a pasta `artifacts` em um volume persistente;
- garantir que esse volume corresponda ao mesmo storage compartilhado usado pelo worker;
- configurar a URL real do worker.

Exemplo de configuracao do backend:

```env
APP_ENV=production
PDF_EXPORT_WORKER_URL=http://pdf-worker.interno:8010
PDF_EXPORT_WORKER_TIMEOUT_SECONDS=180
```

Se usar `docker compose`, ajuste o compose de producao para:

- remover a dependencia de `host.docker.internal`;
- apontar para o hostname ou IP real do worker;
- manter o volume persistente de `artifacts`.

## 6. Validar antes de liberar

Checklist minimo:

1. backend responde em `/healthz`
2. worker responde em `/healthz`
3. backend consegue resolver `PDF_EXPORT_WORKER_URL`
4. worker consegue enxergar a planilha `.xlsx` dentro de `PDF_EXPORT_ARTIFACTS_ROOT`
5. pipeline gera `.xlsx`
6. pipeline gera `.pdf`
7. PDF final preserva o layout correto do Excel

## Healthchecks

### Backend

- `GET /healthz`

### Worker

- `GET /healthz`

Resposta esperada do worker:

- status `ok`
- caminho configurado de `artifacts_root`
- confirmacao de existencia do script de exportacao

## Recomendacoes operacionais

- Restrinja o worker a rede interna.
- Nao exponha o worker diretamente para a internet.
- Monitore indisponibilidade do worker.
- Habilite restart automatico do processo.
- Garanta permissao de leitura e escrita no storage compartilhado.
- Teste com um relatorio real antes do go-live.

## Diagnostico rapido de falhas

### O backend gera `.xlsx`, mas falha no `.pdf`

Verifique:

- `PDF_EXPORT_WORKER_URL`
- acessibilidade de rede entre backend e worker
- healthcheck do worker
- acesso do worker ao `PDF_EXPORT_ARTIFACTS_ROOT`
- instalacao e funcionamento do Microsoft Excel

### O worker responde, mas nao gera o PDF

Verifique:

- se o Excel abre normalmente na conta que executa o worker;
- se a conta do servico tem permissao de acesso ao storage;
- se a planilha existe no caminho relativo informado;
- se a aba esperada esta presente na planilha final.

### O deploy funciona localmente, mas nao em producao

O motivo mais comum e um destes:

- uso de `host.docker.internal` fora do ambiente local;
- storage nao compartilhado de verdade;
- worker rodando com outra conta sem acesso ao Excel ou ao compartilhamento;
- firewall bloqueando a porta do worker.

## Recomendacao final

Para manter a funcionalidade do PDF em producao, trate o worker Windows como parte obrigatoria da arquitetura, nao como um componente opcional.

Se o objetivo do deploy e preservar a fidelidade visual do relatorio final, o worker com Excel deve entrar no escopo oficial de infraestrutura, monitoramento e operacao.

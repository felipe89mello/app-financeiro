# Livro-Caixa — App Financeiro

Aplicativo de controle financeiro pessoal, com backend em **FastAPI** + **SQLite**,
interface web servida pelo próprio backend (Jinja2, sem frontend framework separado),
e empacotamento como aplicativo desktop nativo para Windows via **PyInstaller** +
**pywebview** + **Inno Setup**.

Nasceu da migração de uma planilha Excel de controle de gastos usada por anos — o
processo de migração incluiu extrair comentários de célula (viraram descrição dos
lançamentos) e cores de fonte (viraram forma de pagamento), preservando o histórico
sem perder informação.

## Stack

- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **Banco:** SQLite (arquivo único, sem servidor de banco separado)
- **Frontend:** HTML + Jinja2 + CSS puro (sem build step)
- **Desktop:** pywebview (janela nativa) + PyInstaller (empacotamento) + Inno Setup (instalador Windows)

## Funcionalidades

- Lançamento de despesas e ganhos, por categoria e forma de pagamento
- Dashboard mensal com navegação entre meses
- Detalhe por categoria (clique numa categoria do resumo pra ver os lançamentos)
- Balanço anual, com navegação entre anos
- Backup automático (local, rotativo) a cada abertura do app, com opção de espelhar
  numa pasta sincronizada com serviço de nuvem (Google Drive, OneDrive, etc.)

## Como rodar em modo desenvolvimento

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000`. O banco (`gastos.db`) é criado vazio automaticamente
na primeira execução.

## Como gerar o instalador do Windows

Ver [`COMO_GERAR_O_INSTALADOR.md`](./COMO_GERAR_O_INSTALADOR.md) — usa PyInstaller
para empacotar o app numa janela nativa, e Inno Setup para gerar o instalador final.
Precisa ser feito num Windows.

O `gastos_seed.db` incluído neste repositório é um banco completamente vazio
(sem categorias nem lançamentos) — é o que o instalador usa na primeira
execução do app. Cada pessoa cadastra as próprias categorias.

## Estrutura do projeto

```
app/
  main.py          → rotas da API e das páginas HTML
  models.py        → tabelas (SQLAlchemy)
  schemas.py       → formatos de entrada/saída da API (Pydantic)
  crud.py          → funções que acessam o banco
  database.py      → conexão SQLite e resolução do caminho do banco
  paths.py         → resolve caminhos de recursos/dados (dev vs. .exe empacotado)
  backup.py        → backup automático a cada abertura do app
  utils.py         → helpers de data/mês em português
  templates/        → páginas HTML (Jinja2)
  static/           → CSS
desktop.py          → ponto de entrada do app empacotado (janela nativa)
installer.iss       → script do Inno Setup
```

## Endpoints da API

- `GET/POST /categorias`, `DELETE /categorias/{id}`
- `GET/POST /transacoes`, `PATCH/DELETE /transacoes/{id}`
- `GET /resumo/{ano}/{mes}` — totais e por categoria de um mês
- `GET /balanco-anual/{ano}` — totais por mês de um ano

## Licença

Projeto pessoal, sem licença específica definida ainda.

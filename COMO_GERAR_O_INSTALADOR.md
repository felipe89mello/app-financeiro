# Como gerar o instalador do App Financeiro (Windows)

Esses passos são feitos no SEU computador Windows (não dá pra gerar um .exe
a partir do Linux/Mac — o PyInstaller empacota pro sistema operacional em
que ele roda).

## 0. Pré-requisitos

- Python instalado no Windows
- [Inno Setup](https://jrsoftware.org/isdl.php) instalado (gratuito) — só é
  necessário no passo 3, pra gerar o instalador final

## 1. Instalar o PyInstaller

Abra o terminal (PowerShell ou CMD) na pasta do projeto:

```
pip install pyinstaller
```

## 2. Gerar o executável

Ainda na pasta do projeto (onde está a pasta `app/` e o arquivo `desktop.py`):

```
pyinstaller --name AppFinanceiro --onedir --windowed --add-data "app/templates;app/templates" --add-data "app/static;app/static" --add-data "gastos_seed.db;." desktop.py
```

O que cada parte faz:
- `--name AppFinanceiro` → nome do executável final (`AppFinanceiro.exe`)
- `--onedir` → gera uma pasta com o .exe + arquivos de apoio (inicia mais
  rápido que `--onefile`, que descompacta tudo toda vez que abre)
- `--windowed` → não abre uma janela de terminal preta atrás do app
- `--add-data "app/templates;app/templates"` e `--add-data "app/static;app/static"`
  → inclui as telas HTML e o CSS dentro do pacote (sem isso o app abre em
  branco, sem estilo)
- `--add-data "gastos_seed.db;."` → inclui o banco inicial (completamente
  vazio), copiado automaticamente na primeira execução (ver observação abaixo)

Isso vai criar uma pasta `dist\AppFinanceiro\` com o `AppFinanceiro.exe` e
tudo que ele precisa. Teste clicando duas vezes nele — a janela do app deve
abrir sozinha, mostrando o dashboard vazio (o `AppFinanceiro.exe` copia o
`gastos_seed.db` automaticamente na primeira execução, pra dentro de
`%APPDATA%\AppFinanceiro\gastos.db`). A pessoa cadastra as próprias
categorias em "Categorias" antes do primeiro lançamento.

**Se o Windows pedir o "WebView2 Runtime"**: é o motor que o pywebview usa
pra desenhar a janela. No Windows 10/11 atualizado geralmente já vem
instalado; se não vier, o próprio Windows costuma baixar sozinho, ou você
pode baixar direto da Microsoft (busque "WebView2 Runtime download").

**Sobre o `gastos.db`**: depois da primeira execução, o app passa a usar
só o banco de `%APPDATA%\AppFinanceiro\gastos.db` — o `gastos_seed.db`
empacotado nunca é tocado de novo, então tudo que você lançar fica salvo
ali, mesmo se reinstalar o app depois (a menos que apague essa pasta).

## 3. Gerar o instalador (Setup.exe)

Com o Inno Setup instalado, abra o arquivo `installer.iss` (incluído no
projeto) — ele já está configurado pra pegar a pasta `dist\AppFinanceiro`
gerada no passo 2.

1. Abra `installer.iss` no Inno Setup Compiler
2. Clique em "Compile" (ou aperte F9)
3. O instalador final aparece em `installer_output\AppFinanceiro_Setup.exe`

Esse `.exe` é o que você distribui — ele instala o app, cria atalho na
área de trabalho e no menu iniciar, e já abre o app no final da instalação.

## Resumo dos comandos

```
pip install pyinstaller
pyinstaller --name AppFinanceiro --onedir --windowed --add-data "app/templates;app/templates" --add-data "app/static;app/static" --add-data "gastos_seed.db;." desktop.py
:: depois, abra installer.iss no Inno Setup e compile
```

## Se quiser gerar uma versão com seus próprios dados

Este `gastos_seed.db` do repositório é vazio de propósito.
Se você tem um backup do seu `gastos.db` pessoal e quer um instalador que já
abra com esse histórico:

1. Faça uma cópia desta pasta inteira em outro lugar (fora do repositório Git)
2. Nessa cópia, substitua o `gastos_seed.db` pelo seu backup (renomeado pra
   `gastos_seed.db`)
3. Rode o mesmo comando do PyInstaller e depois o Inno Setup nessa cópia

Assim o repositório em si (e qualquer instalador gerado direto dele) nunca
leva dados pessoais de ninguém.

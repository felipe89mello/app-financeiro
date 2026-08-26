; Script do Inno Setup — gera o instalador (Setup.exe) do App Financeiro.
; Baixe o Inno Setup (gratuito) em https://jrsoftware.org/isdl.php
; Depois de gerar a pasta com o PyInstaller (passo anterior), abra este
; arquivo com o Inno Setup Compiler e clique em "Compile".

#define MyAppName "Livro-Caixa - App Financeiro"
#define MyAppVersion "1.0"
#define MyAppExeName "AppFinanceiro.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\AppFinanceiro
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=AppFinanceiro_Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos adicionais:"

; ATENÇÃO: o caminho abaixo assume que você rodou o PyInstaller no modo
; --onedir (recomendado, inicia mais rápido) e que a pasta gerada se chama
; "dist\AppFinanceiro". Se usou --onefile, ajuste esta seção (veja o
; COMO_GERAR_O_INSTALADOR.md).
[Files]
Source: "dist\AppFinanceiro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir o App Financeiro agora"; Flags: nowait postinstall skipifsilent

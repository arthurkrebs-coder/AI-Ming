# PowerAim — versão pessoal pt-BR / ajustes de interface

Branch: `chatgpt-ptbr-layout-fix`

## Alterações aplicadas

- O seletor da configuração ativa foi incorporado ao menu da barra superior. A janela flutuante separada que exibia `Default` sobre a janela principal não é mais aberta na inicialização.
- A área central da barra superior não exige mais largura mínima fixa de 520 px; o conteúdo recebe rolagem horizontal quando não couber.
- A lista de idiomas passa a incluir `pt-BR`.
- `Locale_pt-BR.json` contém **1.196 de 1.196 entradas** com tradução para português brasileiro. As primeiras 186 foram revisadas manualmente; as restantes foram geradas automaticamente com Argos Translate e precisam de revisão de estilo quando testadas na interface.
- Textos fixos em vários diálogos e na edição de gatilhos foram ligados ao sistema de tradução, inclusive os de diagnóstico de controle, classes de alvo, seleção de processos e configurações.
- Um workflow em `.github/workflows/translate-ptbr.yml` verifica integridade do JSON/XAML e executa uma compilação de validação Windows x64.

## Como compilar no Windows

1. Instale o SDK do .NET 10 (x64) e as demais dependências indicadas no README do projeto.
2. Baixe o ZIP desta branch pelo GitHub e extraia.
3. Abra PowerShell na pasta que contém `PowerAim.sln`.
4. Execute o script oficial:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

Se preferir verificar a compilação antes de empacotar:

```powershell
dotnet restore .\PowerAim.sln
dotnet build .\PowerAim.sln -c Release -p:Platform=x64
```

O script original pode gerar diferentes variantes (CUDA e DirectML) e fazer downloads durante a preparação.

## Atenção

- Estas mudanças **ainda não foram compiladas nem testadas no Windows** nesta sessão.
- O problema de escala/multi-monitor pode exigir ajustes adicionais depois do primeiro teste.
- As demais funções e dependências do aplicativo permanecem as do projeto original.
- Para escolher o idioma: procure `Settings → UI Settings → Language → Portuguese (Brazil)` após compilar.
- Respeite os termos da licença PolyForm Noncommercial do repositório.

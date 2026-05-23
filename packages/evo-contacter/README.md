# Evo5 Web Scraper

Este é um scraper web construído com Playwright para automatizar o processo de login no sistema Evo5.

## Configuração

1. Certifique-se de ter o Node.js instalado em seu sistema
2. Instale as dependências:

```bash
npm install
```

## Executando o Script

Para executar o script, use:

```bash
npm start
```

O script irá:

1. Abrir uma janela do navegador Chrome
2. Navegar até a página de login
3. Preencher automaticamente as credenciais de login
4. Enviar o formulário

## Notas

- A janela do navegador permanecerá aberta após o login para fins de depuração
- Para fechar o navegador automaticamente, descomente a linha `await browser.close();` no código
- Para executar no modo headless (sem navegador visível), altere `headless: false` para `headless: true` no código

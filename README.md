# EvoTools

O **EvoTools** é um monorepo contendo ferramentas de automação, web-scraping e processamento de dados projetadas para se integrarem com o sistema de gestão de academias **Evo5**.

O workspace é estruturado com o [Nx](https://nx.dev) e utiliza npm workspaces para gerenciar seus pacotes.

---

## 📦 Visão Geral dos Pacotes

O repositório é dividido em três pacotes especializados, cada um responsável por uma parte do fluxo de trabalho:

| Pacote | Tecnologia | Descrição | Caminho |
| :--- | :--- | :--- | :--- |
| [**`evo-puppeteer`**](file:///Users/luchesigui/Dev/evo-tools/packages/evo-puppeteer) | Node.js (Puppeteer) | Biblioteca compartilhada que fornece ações comuns de navegação e automação no painel do Evo5 (como login automatizado e busca de contatos). | `packages/evo-puppeteer` |
| [**`evo-contacter`**](file:///Users/luchesigui/Dev/evo-tools/packages/evo-contacter) | Node.js (Puppeteer) | Utilitário que utiliza o `evo-puppeteer` para automatizar o envio de e-mails de comunicação para listas de IDs de membros da academia. | `packages/evo-contacter` |
| [**`evo-frequency-sorter`**](file:///Users/luchesigui/Dev/evo-tools/packages/evo-frequency-sorter) | Python (Pandas) | Script de processamento de dados que filtra planilhas de frequência de acesso para segmentar alunos regulares de agregadores (Wellhub, Totalpass) e VIPs. | `packages/evo-frequency-sorter` |

---

## 🚀 Como Começar

### 1. Pré-requisitos
- **Node.js** (v18+ recomendado)
- **Python** (v3.7+ para processamento de dados)
- **npm** (v7+ com suporte a workspaces)

### 2. Instalação

Instale todas as dependências Node.js do workspace executando o comando a partir da pasta raiz:
```bash
npm install
```

Para configurar o ambiente virtual do Python e instalar as dependências do `evo-frequency-sorter`, execute:
```bash
npm run --prefix packages/evo-frequency-sorter install
```

---

## 🛠️ Guias dos Pacotes

### 1. `evo-puppeteer` (Automação Compartilhada com Puppeteer)
Este é um pacote de utilitários compartilhado. Outros projetos Node do workspace o utilizam como dependência direta.
- **Funcionalidades principais**: Inicialização de navegador (modo headless/headful), fluxo de autenticação no portal, busca de membros e validação de status.
- Para detalhes de configuração, veja o diretório [evo-puppeteer](file:///Users/luchesigui/Dev/evo-tools/packages/evo-puppeteer).

### 2. `evo-contacter` (Comunicações Automatizadas)
Automatiza o envio de e-mails para um lote específico de IDs de clientes.
- **Como Usar**:
  1. Configure o arquivo `.env` dentro da pasta `packages/evo-contacter` com as credenciais de login e as variáveis de ambiente necessárias.
  2. Execute o script de contato:
     ```bash
     npx nx start evo-contacter
     ```
  3. O script abrirá o painel do Evo, fará login automaticamente, filtrará os IDs que necessitam de comunicação e enviará os e-mails um por um.
- Para mais detalhes, consulte o [README do evo-contacter](file:///Users/luchesigui/Dev/evo-tools/packages/evo-contacter/README.md).

### 3. `evo-frequency-sorter` (Triagem e Segmentação de Acessos)
Divide as planilhas de frequências exportadas em arquivos distintos para campanhas de marketing e controle operacional direcionados.
- **Entrada**: Planilha (Excel ou CSV) contendo o registro de frequência.
- **Saídas**:
  - `*acessos-alunos.xlsx` (Membros regulares da academia).
  - `*acessos-agregadores.xlsx` (Agregadores de benefícios corporativos, ex: Wellhub e Totalpass).
- **Como Usar**:
  1. Insira a planilha de entrada (ex: `FREQUENCIA.xlsx`) dentro do diretório do pacote.
  2. Execute o script de filtragem:
     ```bash
     npx nx start evo-frequency-sorter
     ```
- Para mais detalhes, consulte o [README do evo-frequency-sorter](file:///Users/luchesigui/Dev/evo-tools/packages/evo-frequency-sorter/README.md).

---

## 🧩 Recursos do Workspace Nx

Este monorepo utiliza o Nx para orquestração de tarefas e controle de releases.

### Execução de Tarefas
Para executar um script em um pacote específico, utilize:
```bash
npx nx <target> <package-name>
# Exemplo: Rodar testes do evo-contacter
npx nx test evo-contacter
```

### Versionamento e Releases
Para gerenciar o versionamento e release dos pacotes:
```bash
npx nx release
```
Use o parâmetro `--dry-run` para simular o processo de release sem commitar ou publicar.

---

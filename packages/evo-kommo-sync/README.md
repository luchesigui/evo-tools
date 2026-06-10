# Sincronização Evo-Kommo CRM (evo-kommo-sync)

Este pacote é um script Python integrado ao monorepo **EvoTools** para sincronizar clientes do sistema Evo (a partir de planilha XLSX exportada) com o Kommo CRM via API.

## Funcionalidades

- ✅ Lê clientes do arquivo XLSX do Evo
- ✅ Sanitiza números de telefone automaticamente  
- ✅ Busca contatos existentes no Kommo por telefone
- ✅ Cria novos contatos quando não encontrados
- ✅ Atualiza contatos existentes com Evo ID
- ✅ Cria leads no pipeline "Alunos" estágio "ATIVO"
- ✅ Gerencia campos customizados automaticamente
- ✅ Processamento em lotes com rate limiting
- ✅ Modo dry-run para simulação
- ✅ Refresh automático de tokens OAuth
- ✅ Logs detalhados e relatório final

## Pré-requisitos

- Python 3.11+
- Credenciais da API do Kommo (OAuth2)
- Arquivo XLSX exportado do Evo

## Instalação e Configuração

### 1. Configurar dependências e Ambiente Virtual
A partir da raiz do monorepo `evo-tools`, execute a instalação das dependências. Isso criará automaticamente o ambiente virtual `venv` local deste pacote e instalará os requisitos necessários:
```bash
npm install
```
Se preferir instalar/reinstalar apenas este pacote:
```bash
npx nx install evo-kommo-sync
```

### 2. Configurar variáveis de ambiente
1. Copie o arquivo de exemplo `.env.example` para `.env` dentro da pasta `packages/evo-kommo-sync/`:
   ```bash
   cp packages/evo-kommo-sync/.env.example packages/evo-kommo-sync/.env
   ```
2. Edite o arquivo `.env` com suas credenciais:
   ```env
   # Credenciais do Kommo CRM
   KOMMO_DOMAIN=pbsjcsatelite.kommo.com
   KOMMO_CLIENT_ID=seu_client_id_aqui
   KOMMO_CLIENT_SECRET=seu_client_secret_aqui  
   KOMMO_ACCESS_TOKEN=seu_access_token_aqui
   KOMMO_REFRESH_TOKEN=seu_refresh_token_aqui

   # Arquivo XLSX
   XLSX_FILE_PATH=/Users/guilhermeluchesi/Desktop/file_export_1781112543878.xlsx
   ```

## Como Usar

As tarefas são orquestradas usando o **Nx** na raiz do repositório.

### Simulação (Dry Run)
Teste a execução sem realizar alterações reais no Kommo CRM:
```bash
npx nx start evo-kommo-sync -- --dry-run --verbose
```

### Execução Real
Execute a sincronização real para enviar/atualizar contatos:
```bash
npx nx start evo-kommo-sync -- --verbose
```

### Opções Disponíveis
```bash
npx nx start evo-kommo-sync -- --help
```
- `--dry-run`: Simula execução sem fazer alterações
- `--verbose, -v`: Logs detalhados
- `--batch-size N`: Tamanho do lote (padrão: 50, máximo: 250)


---

## Estrutura do Arquivo XLSX

O script espera um arquivo XLSX com:
- **Sheet**: `data`
- **Colunas**:
  - `IdCliente`: ID único do cliente no Evo
  - `Nome`: Nome completo do cliente  
  - `Data de nascimento`: Data de nascimento
  - `Telefone/celular`: Telefone no formato `55 12988316247`

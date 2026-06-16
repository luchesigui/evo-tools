# Evo Kommo Broadcast

Pacote para envio de mensagens em massa via WhatsApp pelo Kommo CRM.

## Funcionalidades

- Lê uma lista de telefones e nomes de um arquivo XLSX
- Busca os contatos correspondentes no Kommo CRM via API v4
- Envia mensagens de WhatsApp para cada contato usando a Chats API do Kommo (amojo.kommo.com)
- Suporte a templates de mensagem com substituição de variáveis
- Modo dry-run para simulação
- Rate limiting para evitar sobrecarga das APIs
- Relatório detalhado de envios

## Configuração

### 1. Instalar dependências

```bash
npm run install
# ou
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Copie `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:

- **Credenciais do Kommo CRM (API v4)**: Obtenha em Configurações → Integrações → API
- **Chats API (amojo)**: Obtenha criando uma integração privada → Chat channel
- **Arquivo XLSX**: Caminho para o arquivo com a lista de contatos
- **Mensagem**: Template da mensagem a ser enviada

### 3. Formato do arquivo XLSX

O arquivo deve ter as seguintes colunas:

- **Coluna A**: Nome (opcional, pode estar em qualquer posição)
- **Coluna B**: Telefone (obrigatório, pode estar em qualquer posição)

Exemplos de formato de telefone aceitos:
- `5512988316247`
- `55 12 98831-6247`
- `(12) 98831-6247`

## Uso

### Comando básico

```bash
npm start
# ou
./venv/bin/python broadcast.py
```

### Opções avançadas

```bash
# Modo simulação (não envia mensagens)
./venv/bin/python broadcast.py --dry-run

# Logs detalhados
./venv/bin/python broadcast.py --verbose

# Arquivo XLSX personalizado
./venv/bin/python broadcast.py --xlsx /path/to/contatos.xlsx

# Mensagem personalizada
./venv/bin/python broadcast.py --message "Olá {nome}! Esta é uma mensagem personalizada."

# Delay personalizado entre mensagens (em segundos)
./venv/bin/python broadcast.py --delay 3.0

# Combinação de opções
./venv/bin/python broadcast.py --dry-run --verbose --delay 1.5
```

## Template de Mensagem

A mensagem suporta variáveis que são substituídas automaticamente:

- `{nome}`: Nome do contato (da planilha ou do Kommo)

Exemplo:
```
Olá {nome}! Bem-vindo ao nosso sistema. Sua mensagem personalizada aqui.
```

## Fluxo de Execução

1. **Leitura do XLSX**: Carrega lista de contatos do arquivo
2. **Busca no Kommo**: Para cada telefone, busca o contato correspondente no CRM
3. **Criação de Chats**: Para contatos encontrados, cria um chat via Chats API
4. **Envio de Mensagens**: Envia a mensagem para cada chat criado
5. **Relatório**: Exibe estatísticas finais do envio

## Relatório de Envio

O script gera um relatório detalhado:

```
RELATÓRIO FINAL DO BROADCAST
============================================================
Total na planilha:      150
Encontrados no Kommo:   142
Não encontrados:        8
Mensagens enviadas:     140
Erros no envio:         2
============================================================
```

## Tratamento de Erros

- **Rate limiting**: Aguarda automaticamente quando APIs retornam 429
- **Token expirado**: Renova automaticamente o access token
- **Retry**: Tenta novamente em caso de falhas temporárias
- **Validação**: Verifica se todas as credenciais estão configuradas

## Limitações

- Depende de ter os contatos já cadastrados no Kommo CRM
- Requer configuração de um chat channel no Kommo
- Rate limiting pode tornar o processo lento para listas muito grandes
- Mensagens são enviadas uma por vez (não em lote)

## Logs e Debug

Use `--verbose` para logs detalhados que incluem:
- Progresso da busca no Kommo
- Detalhes das requisições HTTP
- Lista de contatos não encontrados
- Informações de debug das APIs

## Limpeza

```bash
npm run clean
# ou
rm -rf __pycache__ .pytest_cache venv
```
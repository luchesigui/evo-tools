# Análise de Telefone - Interseção de Clientes

Este projeto Python tem como objetivo principal padronizar números de telefone de duas fontes de dados (clientes e relatórios) e identificar quais telefones do relatório já existem na base de clientes.

## 🚀 Como Iniciar

Siga estes passos para configurar e executar o projeto em sua máquina local.

### TLDR;

1. Garanta que os arquivos estão na pasta data/{ano_atual};
   1. A base de clientes atuais deve ser o arquivo `clientes.csv`
   2. A base de oportunidades pode ser qualquer outro excel, mas lembre-se de atualizar a env `LEADS_FILE_NAME` do seu .env;
2. Rode o comando `make start`;

### Pré-requisitos

Certifique-se de ter o Python instalado em seu sistema. Recomenda-se o Python 3.7 ou superior.
Você pode baixá-lo em [python.org](https://www.python.org/downloads/). O `pip` ou `pip3` (gerenciador de pacotes do Python) geralmente vem junto com a instalação.

### 📦 Instalação

É **altamente recomendado** usar um ambiente virtual para isolar as dependências deste projeto de outras instalações Python no seu sistema.

1.  **Clone este repositório (se estiver usando Git):**

    ```bash
    git clone https://github.com/SeuUsuario/analise-telefones-python.git
    cd analise-telefones-python
    ```

    (Ajuste `https://github.com/SeuUsuario/analise-telefones-python.git` para o URL real do seu repositório no GitHub/GitLab/Bitbucket)

    **Ou, se você baixou os arquivos manualmente:**

    Navegue até a pasta raiz do projeto onde os arquivos `analise_telefones.py`, `requirements.txt` e o `.gitignore` estão localizados.

2.  **Crie um Ambiente Virtual:**

    ```bash
    python -m venv venv
    ```

3.  **Ative o Ambiente Virtual:**

        - **No Windows:**
          ```bash
          .\venv\Scripts\activate
          ```
        - **No macOS/Linux:**
          `bash

    source venv/bin/activate
    `      Você saberá que o ambiente está ativado quando`(venv)` aparecer no início da linha de comando do seu terminal.

4.  **Instale as Dependências:**

    Com o ambiente virtual ativado, instale todas as bibliotecas necessárias listadas no `requirements.txt`:

    ```bash
    pip install -r requirements.txt
    ```

### 📊 Preparação dos Dados

Este script espera dois arquivos de dados na **mesma pasta** onde o script `analise_telefones.py` está localizado:

- **`clientes.csv`**: Um arquivo CSV contendo uma coluna chamada `telefone`.

  - Exemplo de `clientes.csv`:
    ```csv
    idCliente,nome,contrato,telefone
    1,Cliente A,WELLHUB,5511987654321
    1,Cliente B,FREPASS,552198765432
    1,Cliente C,NaN,5531998765432
    ```

- **`meta-ads.xlsx`**: Um arquivo Excel contendo as colunas `Telefone`, `Primeiro nome` e `Sobrenome`.
  - Exemplo de `meta-ads.xlsx` (primeiras linhas):
    | Telefone | Primeiro nome | Sobrenome |
    | :------- | :------------ | :-------- |
    | 5511987654321 | João | Silva |
    | (21) 9876-5432 | Maria | Souza |
    | 5531998765432 | Pedro | Santos |

**Importante:** Verifique os nomes exatos das colunas e arquivos. O script é sensível a maiúsculas/minúsculas e erros de digitação.

### 🏃 Como Executar

1.  **Certifique-se de que seu ambiente virtual está ativado.** (Veja o passo 3 em "Instalação")
2.  **Certifique-se de que os arquivos de dados (`clientes.csv` e `meta-ads.xlsx`) estão na mesma pasta do script `analise_telefones.py`.**
3.  **No terminal, execute o script:**

    ```bash
    python analise_telefones.py
    ```

4.  **Depois de executado, desconecte do ambiente virtual digitando `deactivate` no terminal.**

### 💻 Resultado

O script processará os dados e exibirá no terminal uma tabela (DataFrame do pandas) com os "Nome", "Telefone" e "Contrato" de todos os clientes do `clientes.csv` que possuem um telefone padronizado correspondente na base `meta-ads.xlsx` e salvara a taxa de conversão em um arquivo de report dentro da pasta `reports/{ano_atual}`.

# evo-renovacoes-pendencias

Analisa membros ativos da API EVO, identifica contratos proximos do vencimento
e cruza com pendencias financeiras. Gera relatorios e exporta JSON/CSV.

## Estrutura

```
evo-renovacoes-pendencias/
├── src/
│   └── evo_renovacoes/
│       ├── __init__.py      # Exports publicos
│       ├── __main__.py      # python -m evo_renovacoes
│       ├── core.py          # Logica de API, analise e exportacao
│       └── cli.py           # Entry point com argparse
├── requirements.txt         # requests, python-dotenv
├── .env.example             # Template de configuracao
├── .gitignore
└── package.json
```

## Instalacao

```bash
cd ~/Dev/evo-tools/packages/evo-renovacoes-pendencias
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

Copie `.env.example` para `.env` e preenca as credenciais.

## Uso

```bash
# Renovacoes nos proximos 7 dias
./venv/bin/python -m src.evo_renovacoes --dias 7

# Exatamente 3 dias
./venv/bin/python -m src.evo_renovacoes --dias 3 --exato

# Pendencias financeiras
./venv/bin/python -m src.evo_renovacoes --pendencias

# Exportar em JSON e CSV
./venv/bin/python -m src.evo_renovacoes --dias 7 --json --csv

# Limitar membros (para testes)
./venv/bin/python -m src.evo_renovacoes --dias 5 --membros 100

# Sem consultar pendencias (mais rapido)
./venv/bin/python -m src.evo_renovacoes --dias 7 --sem-pendencia
```

## CLI Arguments

| Argumento        | Default | Descricao                                  |
|------------------|---------|--------------------------------------------|
| `--dias`         | 5       | Janela de dias (1, 3 ou 7)                 |
| `--exato`        | false   | Filtra match exato (nao janela)            |
| `--membros`      | todos   | Limite de membros para analisar            |
| `--pendencias`   | false   | Mostra apenas membros com pendencias       |
| `--sem-pendencia`| false   | Nao cruza com pendencias                   |
| `--json`         | false   | Exporta JSON                               |
| `--csv`          | false   | Exporta CSV                                |

## Como Modulo Python

```python
from evo_renovacoes import get_members_sample, analyze_renovations

members, _ = get_members_sample()
renewals = analyze_renovations(members, days_before=7)
for r in renewals:
    print(r["nome"], r["dias_ate_vencimento"])
```

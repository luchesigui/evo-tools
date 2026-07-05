"""Permite executar o pacote diretamente: python -m evo_renovacoes"""
import sys
from pathlib import Path

# Garante que src/ esta no path quando executado como modulo
sys.path.insert(0, str(Path(__file__).parent / "src"))

from evo_renovacoes.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

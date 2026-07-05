#!/usr/bin/env python3
"""Entry point principal - executa o CLI do pacote."""
import sys
from pathlib import Path

# Garante que src/ esta no path quando executado diretamente
sys.path.insert(0, str(Path(__file__).parent / "src"))

from evo_renovacoes.cli import main

if __name__ == "__main__":
    sys.exit(main())

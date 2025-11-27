# Guia de Arquivos

Resumo rápido do propósito de cada arquivo e pasta do projeto.

## Raiz
- `main.py` — ponto de entrada; delega para a CLI em `src/cli.py`.
- `requirements.txt` — dependências necessárias (numpy, scipy, matplotlib, networkx, pytest etc.).
- `README.md` — visão geral do projeto e instruções de uso da CLI.

## src/
- `__init__.py` — marca o pacote.
- `config.py` — valores padrão e dataclasses de configuração (solver, geração aleatória, I/O, plots).
- `data_io.py` — leitura de dados (interativo, JSON, CSV, aleatório) e exportação de resultados (matriz, resumo).
- `model.py` — validação de dimensões/valores, nomes padrão e balanceamento automático com nós fictícios.
- `solver.py` — montagem das restrições e chamada a `scipy.optimize.linprog` (HiGHS); captura de duais básicos.
- `visualization.py` — gráficos de barras empilhadas e grafo bipartido de fluxos.
- `cli.py` — parser de argumentos (argparse), logging e orquestração completa da solução.

## tests/
- `test_model_solver.py` — testes unitários: solução conhecida, balanceamento com nó fictício e validação de entrada.

## data/
- `exemplo.json` — exemplo de entrada em JSON (nomes, oferta, demanda, custos).
- `exemplo.csv` — exemplo de entrada em CSV (linhas supply/demand + custos por fábrica).

## results/
- Diretório padrão para saídas geradas pela CLI: `solution_matrix.csv`, `summary.json` e, se habilitado, `solution_bars.png`/`solution_network.png`.

## docs/
- `README_arquivos.md` — este arquivo; explica cada artefato.
- `README_estrutura.md` — visão da estrutura completa e como navegar.

# Otimizacao de Rotas de Distribuicao (Problema de Transporte)

Projeto em Python (3.10+) para resolver o problema classico de transporte via Programacao Linear usando scipy.optimize.linprog (metodo Simplex). O codigo foi modularizado para uso academico/profissional, com CLI, geracao aleatoria de instancias, balanceamento automatico, visualizacoes e exportacao de resultados.

## Arquitetura

- main.py -> apenas chama a CLI.
- src/
  - config.py -> valores padrao e dataclasses de configuracao.
  - data_io.py -> leitura interativa/arquivo/aleatoria e exportacao de resultados.
  - model.py -> validacao, nomes, balanceamento automatico com nos ficticios.
  - solver.py -> montagem das restricoes e chamada a linprog (Simplex).
  - visualization.py -> graficos de barras e grafo bipartido (NetworkX).
  - cli.py -> parsing de argumentos, orquestracao e logging.
- tests/ -> testes unitarios simples com pytest.
- data/ -> exemplos de entrada (exemplo.json, exemplo.csv).
- results/ -> diretorio padrao para saidas (CSV/JSON/plots).

## Instalacao

python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt

## Uso rapido (CLI)

# modo interativo
python main.py --mode interactive

# modo aleatorio (balanceado, reprodutivel)
python main.py --mode random --n-factories 3 --n-cds 4 --balanced yes --cost-min 1 --cost-max 50 --seed 42 --save-plots

# modo arquivo (JSON/CSV)
python main.py --mode file --input data/exemplo.json --save-plots --output-dir results01/

python main.py --mode file --input data/exemplo.json --save-plots --output-dir results02/

Opcoes uteis:
- --solver-method Simplex (default), --tol, --max-iter
- --save-plots / --show-plots
- --output-dir results/
- --verbose para logs detalhados

Execute python main.py -h para a ajuda completa com exemplos.

## Formatos de entrada

JSON recomendado:
{
  "factory_names": ["F1", "F2"],
  "customer_names": ["CD1", "CD2", "CD3"],
  "supply": [20, 15],
  "demand": [5, 15, 15],
  "costs": [[8, 6, 10], [9, 7, 4]]
}

CSV simples: primeira linha "supply,<valores>", segunda linha "demand,<valores>", demais linhas com custos por fabrica. Exemplo em data/exemplo.csv.

Quando sum(supply) != sum(demand), um no ficticio e adicionado automaticamente (fabrica ou CD) com custos zero para balancear o problema.

## Saidas
- results/solution_matrix.csv -> matriz de fluxos (origem x destino).
- results/summary.json -> status do solver, custo e metadados de balanceamento.
- results/solution_bars.png e results/solution_network.png (se --save-plots).

## Testes

pytest

Inclui:
- Instancia pequena com solucao conhecida (custo 190).
- Checagem de balanceamento com no ficticio.
- Validacao de entradas invalidas.

## Sensibilidade (ganhos duais)

Se o solver retornar marginais de igualdade (Simplex/linprog expoe em result.eqlin.marginals), eles sao capturados e podem ser usados futuramente para analises de precos-sombra.

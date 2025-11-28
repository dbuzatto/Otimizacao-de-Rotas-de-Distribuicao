# Estrutura do Projeto

Visão geral da organização e como os componentes se relacionam.

## Árvore resumida
```
.
├─ main.py                # Entrada; chama src.cli.run_cli
├─ requirements.txt       # Dependências
├─ README.md              # Guia principal de uso/CLI
├─ src/                   # Código-fonte modular
│  ├─ config.py           # Configurações padrão (solver, aleatório, I/O, plots)
│  ├─ data_io.py          # Entrada (interativo/arquivo/aleatório) e saída (CSV/JSON)
│  ├─ model.py            # Validação, nomes, balanceamento com nós fictícios
│  ├─ solver.py           # Formulação e chamada a linprog (Simplex)
│  ├─ visualization.py    # Gráficos (barras, grafo bipartido)
│  ├─ cli.py              # Argparse + orquestração completa
│  └─ __init__.py
├─ tests/                 # Testes unitários
│  └─ test_model_solver.py
├─ data/                  # Exemplos de entrada
│  ├─ exemplo.json
│  └─ exemplo.csv
├─ results/               # Saídas geradas (matriz, resumo, plots)
└─ docs/                  # Documentação adicional
   ├─ README_arquivos.md  # Descrição de cada arquivo
   └─ README_estrutura.md # Este documento
```

## Fluxo de execução
1. Usuário chama `python main.py ...` → delega para `src/cli.py`.
2. CLI lê argumentos, carrega dados via `data_io` (interativo, arquivo ou aleatório).
3. `model.validate_data` garante dimensões/valores; `model.balance_problem` adiciona nós fictícios se necessário.
4. `solver.solve_transportation_problem` monta as restrições e usa `linprog` (Simplex) para obter a solução.
5. Resultados são exibidos na CLI, exportados para CSV/JSON e, opcionalmente, plotados via `visualization`.

## Onde modificar
- Ajustar defaults de geração/solver/saída: `src/config.py`.
- Novas fontes de dados ou formatos: `src/data_io.py`.
- Regras de validação/balanceamento ou nomes de nós: `src/model.py`.
- Trocar solver ou adicionar análises (duais/sensibilidade): `src/solver.py`.
- Customizar gráficos: `src/visualization.py`.
- Novos modos/flags de CLI: `src/cli.py`.

## Testes
Executar `pytest` para validar modelagem, balanceamento e solver em instâncias pequenas.

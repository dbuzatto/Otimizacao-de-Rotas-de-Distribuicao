# Otimização de Rotas de Distribuição

Este repositório implementa um otimizador de transporte (problema de transporte) em Python que calcula o plano de distribuição de menor custo entre Fábricas e Centros de Distribuição (CDs). O solver usa programação linear (Simplex/Highs via `scipy.optimize.linprog`) e gera visualizações (barras e grafo de rede) das rotas ótimas.

**Principais funcionalidades**
- Modelagem do problema de transporte (oferta x demanda)
- Balanceamento automático com nós fictícios (quando oferta ≠ demanda)
- Modo de entrada manual e geração aleatória de instâncias (balanceado ou não)
- Visualizações: gráfico de barras por CD e grafo de rede com quantidades e custos

## Arquivo principal
- `main.py`: Programa principal que solicita entradas (ou gera aleatórias), balanceia o problema adicionando nós fictícios quando necessário, resolve com `linprog` e plota resultados com `matplotlib` e `networkx`.

## Requisitos / Dependências
Instale as dependências listadas no `requirements.txt` (recomendado criar e usar um ambiente virtual):

No Windows (cmd):

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Dependências principais usadas pelo projeto (extraídas de `requirements.txt`):

- `numpy`
- `scipy`
- `matplotlib`
- `networkx`

> Observação: o arquivo `requirements.txt` no repositório contém versões compatíveis; usar `pip install -r requirements.txt` garante que você terá as mesmas versões testadas.

## Como usar
1. Abra um terminal (cmd) no diretório do projeto.
2. Ative seu ambiente virtual (opcional, recomendado).
3. Execute:

```cmd
python main.py
```

O programa pedirá que você escolha o modo de entrada:
- `1` — Inserir dados manualmente (ofertas, demandas, custos)
- `2` — Gerar dados aleatórios (você escolhe número de fábricas, CDs e se deseja balancear)

No modo aleatório o programa pergunta se deseja gerar um problema balanceado (`S`/`N`). Quando os totais de oferta e demanda divergirem, o programa adiciona automaticamente um nó fictício (CD fictício para absorver sobra ou Fábrica fictícia para suprir falta) com custo zero para permitir a resolução por `linprog`.

## Saída
- Impressão do custo total mínimo (valor objetivo do solver)
- Matriz com as quantidades transportadas entre cada par (Fábrica → CD), incluindo rotas fictícias quando aplicável
- Dois gráficos interativos (janela matplotlib): gráfico de barras por CD e grafo de rede com etiquetas de quantidade e custo por aresta

## Estrutura mínima do repositório
- `main.py` — código principal
- `requirements.txt` — dependências
- `README.md` — este arquivo
# Otimização de Rotas de Distribuição

Programa Python que otimiza o custo de transporte entre centros de distribuição (CDs) e lojas usando o método Simplex.

## Requisitos

```
matplotlib
scipy
```

## Como Usar

1. Execute o arquivo `main.py`
2. Informe o número de CDs e lojas
3. Escolha o modo de entrada:
   - `M` para inserir dados manualmente
   - `R` para gerar dados aleatórios

## Funcionalidades

- Calcula o menor custo possível de distribuição
- Balanceia automaticamente oferta e demanda
- Gera visualização gráfica das rotas
- Mostra quantidade de produtos enviados entre cada CD e loja

## Saída

- Custo total mínimo da distribuição
- Lista detalhada de entregas (CD → Loja)
- Gráfico mostrando:
  - CDs (pontos azuis)
  - Lojas (pontos laranja)
  - Rotas de entrega (linhas cinza)


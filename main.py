import random
import matplotlib.pyplot as plt
from scipy.optimize import linprog

# Entradas básicas
num_cds = int(input("Quantos centros de distribuição (CDs)? "))
num_lojas = int(input("Quantas lojas? "))

modo = input("Deseja inserir os valores manualmente (M) ou gerar aleatoriamente (R)? ").strip().upper()

custos, ofertas, demandas = [], [], []

if modo == "M":
    for i in range(num_cds):
        linha = list(map(float, input(f"Custos do CD{i+1} → lojas ({num_lojas} valores): ").split()))
        custos.append(linha)
    ofertas = list(map(float, input(f"Ofertas dos CDs ({num_cds} valores): ").split()))
    demandas = list(map(float, input(f"Demandas das lojas ({num_lojas} valores): ").split()))
else:
    # Geração aleatória sem zeros
    custos = [[random.randint(1, 10) for _ in range(num_lojas)] for _ in range(num_cds)]
    ofertas = [random.randint(1, 15) for _ in range(num_cds)]
    demandas = [random.randint(1, 10) for _ in range(num_lojas)]

# Balanceia automaticamente oferta e demanda
total_oferta = sum(ofertas)
total_demanda = sum(demandas)

if total_oferta > total_demanda:
    demandas.append(total_oferta - total_demanda)
    for linha in custos:
        linha.append(1)  # custo mínimo de 1 real para o destino fictício
    num_lojas += 1
elif total_demanda > total_oferta:
    ofertas.append(total_demanda - total_oferta)
    custos.append([1] * num_lojas)
    num_cds += 1

# Monta o problema
c = [c for linha in custos for c in linha]
A_eq, b_eq = [], []

for i in range(num_cds):
    linha = [0]*(num_cds*num_lojas)
    for j in range(num_lojas):
        linha[i*num_lojas + j] = 1
    A_eq.append(linha)
    b_eq.append(ofertas[i])

for j in range(num_lojas):
    linha = [0]*(num_cds*num_lojas)
    for i in range(num_cds):
        linha[i*num_lojas + j] = 1
    A_eq.append(linha)
    b_eq.append(demandas[j])

x_bounds = [(0, None)]*(num_cds*num_lojas)
res = linprog(c=c, A_eq=A_eq, b_eq=b_eq, bounds=x_bounds, method='highs')

if not res.success:
    print("Não foi possível resolver.")
    exit()

x = res.x.reshape((num_cds, num_lojas))
print(f"\nCusto mínimo total: R$ {res.fun:.2f}\n")

for i in range(num_cds):
    for j in range(num_lojas):
        if x[i, j] > 0:
            print(f"CD{i+1} → Loja{j+1}: {x[i,j]:.0f} unidades (R${custos[i][j]})")

# ======== Mapa lógico ========
plt.figure(figsize=(10, 6))

cd_x = [0] * num_cds
cd_y = list(range(num_cds))
loja_x = [10] * num_lojas
loja_y = list(range(num_lojas))

plt.scatter(cd_x, cd_y, color='blue', s=150, label='CDs')
plt.scatter(loja_x, loja_y, color='orange', s=150, label='Lojas')

for i in range(num_cds):
    for j in range(num_lojas):
        if x[i, j] > 0:
            plt.plot([cd_x[i], loja_x[j]], [cd_y[i], loja_y[j]],
                     linewidth=max(1, x[i, j] / 2),
                     alpha=0.6, color='gray')
            plt.text((cd_x[i]+loja_x[j])/2, (cd_y[i]+loja_y[j])/2,
                     f"{x[i,j]:.0f}", fontsize=7, ha='center', va='center')

for i in range(num_cds):
    plt.text(cd_x[i]-0.5, cd_y[i], f"CD{i+1}", ha='right', va='center', fontsize=9, color='blue')
for j in range(num_lojas):
    plt.text(loja_x[j]+0.5, loja_y[j], f"L{j+1}", ha='left', va='center', fontsize=9, color='orange')

plt.title("Mapa de Transporte (Fluxo entre CDs e Lojas)")
plt.axis("off")
plt.legend()
plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)
plt.show()
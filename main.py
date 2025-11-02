import numpy as np
from scipy.optimize import linprog
import matplotlib.pyplot as plt
import networkx as nx

# --- Funções Auxiliares de Entrada ---

def obter_inteiro_positivo(prompt, minimo=1):
    """Solicita um inteiro positivo ao usuário."""
    while True:
        try:
            valor_str = input(prompt)
            valor = int(valor_str)
            if valor < minimo:
                print(f"Valor inválido. Deve ser um inteiro de no mínimo {minimo}.")
            else:
                return valor
        except ValueError:
            print("Entrada inválida. Por favor, insira um número inteiro.")

def obter_float_positivo(prompt, minimo=0.0):
    """Solicita um número (float) positivo ao usuário."""
    while True:
        try:
            valor_str = input(prompt)
            valor = float(valor_str)
            if valor < minimo:
                print(f"Valor inválido. Deve ser um número de no mínimo {minimo}.")
            else:
                return valor
        except ValueError:
            print("Entrada inválida. Por favor, insira um número.")

def obter_sim_nao(prompt):
    """Solicita uma resposta 'S' ou 'N'."""
    while True:
        resposta = input(prompt).strip().lower()
        if resposta in ['s', 'sim']:
            return True
        elif resposta in ['n', 'nao', 'não']:
            return False
        else:
            print("Resposta inválida. Por favor, digite 'S' (Sim) ou 'N' (Não).")

# --- Funções de Geração de Dados ---

def obter_dados_manuais():
    """Obtém todos os dados (fábricas, CDs, ofertas, demandas, custos) manualmente."""
    print("\n--- Modo de Entrada Manual ---")
    
    n_fabricas = obter_inteiro_positivo("Digite o número de Fábricas: ")
    n_cds = obter_inteiro_positivo("Digite o número de Centros de Distribuição (CDs): ")
    
    b_ofertas = np.zeros(n_fabricas)
    b_demandas = np.zeros(n_cds)
    
    print("\n--- Inserir Ofertas (Disponibilidade) ---")
    for i in range(n_fabricas):
        b_ofertas[i] = obter_float_positivo(f"Oferta da Fábrica {i+1}: ")
        
    print("\n--- Inserir Demandas (Necessidade) ---")
    for j in range(n_cds):
        b_demandas[j] = obter_float_positivo(f"Demanda do CD {j+1}: ")

    total_oferta = np.sum(b_ofertas)
    total_demanda = np.sum(b_demandas)
    print(f"\nEntrada Concluída. (Total Oferta: {total_oferta} | Total Demanda: {total_demanda})")
    if not np.isclose(total_oferta, total_demanda):
        print("AVISO: Problema não-balanceado detectado. O otimizador criará rotas fictícias.")

    print("\n--- Inserir Custos de Transporte ---")
    c_custos = np.zeros(n_fabricas * n_cds)
    k = 0 
    for i in range(n_fabricas):
        for j in range(n_cds):
            c_custos[k] = obter_float_positivo(f"Custo (Fábrica {i+1} -> CD {j+1}): ")
            k += 1
            
    return c_custos, b_ofertas, b_demandas, n_fabricas, n_cds

def gerar_problema_transporte(n_fabricas, n_cds, balanceado=False):
    """
    Gera um problema de transporte aleatório.   
   
    - Se 'balanceado=True', garante que total_oferta == total_demanda.
    - Se 'balanceado=False', garante que a diferença não exceda 20%.
    """
    print(f"\n--- Modo de Geração Aleatória ({'Balanceado' if balanceado else 'Não-Balanceado'}) ---")
    
    # 1. Gerar Custos (sem alteração)
    num_variaveis = n_fabricas * n_cds
    c_transporte = np.random.randint(1, 11, size=num_variaveis)
    
    # 2. Gerar Ofertas
    # Gera valores base para as ofertas
    ofertas = np.random.randint(400, 1101, size=n_fabricas)
    total_oferta = np.sum(ofertas)
    
    total_demanda_alvo = 0
    
    if balanceado:
        # Se balanceado, a demanda alvo é exatamente a oferta total
        total_demanda_alvo = total_oferta
        print("Modo Balanceado: Total Oferta e Total Demanda serão idênticos.")
        
    else:
        # Se não-balanceado, calcula limites de +/- 20%
        # Garante que a diferença não seja maior que 20%
        limite_inferior = total_oferta * 0.80
        limite_superior = total_oferta * 1.20
        
        # Escolhe um total de demanda aleatório dentro dessa faixa
        total_demanda_alvo = np.random.randint(int(limite_inferior), int(limite_superior))
        print("Modo Não-Balanceado: Diferença entre totais controlada em até 20%.")

    # 3. Gerar Demandas com base no total_demanda_alvo
    # Gera proporções aleatórias
    demandas_proporcoes = np.random.rand(n_cds)
    # Normaliza as proporções (para que somem 1)
    demandas_proporcoes /= np.sum(demandas_proporcoes)
    
    # Distribui o total_demanda_alvo de acordo com as proporções
    demandas = demandas_proporcoes * total_demanda_alvo
    
    # Arredonda (para baixo) e ajusta o último valor para garantir a soma exata
    demandas = np.floor(demandas)
    ajuste = total_demanda_alvo - np.sum(demandas)
    demandas[-1] += ajuste # Adiciona o 'resto' do arredondamento ao último CD
    
    # Garante que nenhum valor é zero (caso raro)
    demandas[demandas < 1] = 1
    # Reajusta o primeiro valor se a correção acima quebrou a soma
    ajuste_final = total_demanda_alvo - np.sum(demandas)
    demandas[0] += ajuste_final

    total_demanda = np.sum(demandas)

    print(f"\nDimensões: {n_fabricas} Fábricas -> {n_cds} CDs")
    print(f"Oferta Total: {total_oferta:.0f} | Demanda Total: {total_demanda:.0f}")
    
    if not np.isclose(total_oferta, total_demanda):
        print("AVISO: Problema não-balanceado. O otimizador lidará com isso.")
    else:
         print("INFO: Problema gerado está perfeitamente balanceado.")
        
    return c_transporte, ofertas, demandas, n_fabricas, n_cds

# --- Funções de Otimização  ---

def construir_matrizes_restricao_eq(n_fabricas, n_cds, num_variaveis):
    """Constrói a matriz A_eq para as restrições de igualdade."""
    num_restricoes = n_fabricas + n_cds
    A_eq = np.zeros((num_restricoes, num_variaveis))
    
    # Restrições de Oferta (linhas de fábrica)
    for i in range(n_fabricas):
        inicio_col = i * n_cds
        fim_col = (i + 1) * n_cds
        A_eq[i, inicio_col:fim_col] = 1
        
    # Restrições de Demanda (linhas de CD)
    for j in range(n_cds):
        linha_matriz = n_fabricas + j
        colunas = np.arange(j, num_variaveis, n_cds)
        A_eq[linha_matriz, colunas] = 1
        
    return A_eq

# --- Funções de Plotagem ---

def plotar_solucao(solucao, n_fabricas, n_cds, n_fab_orig, n_cds_orig, cd_ficticio, fabrica_ficticia):
    """Gera um gráfico de barras da solução."""
    
    nomes_cds = [f"CD {j+1}" for j in range(n_cds_orig)]
    if cd_ficticio:
        nomes_cds.append("SOBRA (Fictício)")
        
    nomes_fabricas = [f"Fábrica {i+1}" for i in range(n_fab_orig)]
    if fabrica_ficticia:
        nomes_fabricas.append("FALTA (Fictícia)")
    
    posicoes_x = np.arange(n_cds)
    largura_barra = 0.8 / n_fabricas
    
    fig, ax = plt.subplots(figsize=(max(12, n_cds * 2), 7))
    
    # Cria as barras para cada fábrica
    for i in range(n_fabricas):
        offset = largura_barra * (i - (n_fabricas - 1) / 2)
        dados_fabrica = solucao[i, :]
        barras = ax.bar(posicoes_x + offset, dados_fabrica, largura_barra, label=nomes_fabricas[i])
        
        # Adiciona rótulos apenas para valores maiores que zero
        rotulos = [f'{v:.0f}' if v > 0.01 else '' for v in dados_fabrica]
        ax.bar_label(barras, fmt='%.0f', padding=3, fontsize=9, labels=rotulos)
        
    ax.set_title(f'Plano de Distribuição Otimizado ({n_fab_orig}x{n_cds_orig}) - Barras')
    ax.set_ylabel('Unidades Transportadas')
    ax.set_xlabel('Centros de Distribuição')
    
    ax.set_xticks(posicoes_x)
    ax.set_xticklabels(nomes_cds)
    ax.legend(title="Origem (Fábricas)")
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_ylim(top=ax.get_ylim()[1] * 1.1) # Ajusta limite superior Y
    
    fig.tight_layout()

def plotar_grafo_rede(solucao, n_fab_orig, n_cds_orig, ofertas_orig, demandas_orig, custos_orig, cd_ficticio, fabrica_ficticia):
    """Gera um gráfico de rede (grafos) bipartido da solução."""
    
    G = nx.DiGraph()
    
    # Reformata os custos originais (vetor) para uma matriz 2D
    custos_matriz = custos_orig.reshape((n_fab_orig, n_cds_orig))
    
    # 1. Definir nomes de nós
    nomes_fabricas = [f"Fábrica {i+1}" for i in range(n_fab_orig)]
    nomes_cds = [f"CD {j+1}" for j in range(n_cds_orig)]
    
    custom_labels = {}
    cores_fabricas = [] # Lista de cores SÓ para fábricas
    cores_cds = []      # Lista de cores SÓ para CDs
    
    # 2. Processar Fábricas Originais
    for i, nome in enumerate(nomes_fabricas):
        custom_labels[nome] = f"{nome}\n(Oferta: {ofertas_orig[i]:.0f})"
        cores_fabricas.append("skyblue") # Cor Azul
    
    # 3. Processar CDs Originais
    for j, nome in enumerate(nomes_cds):
        custom_labels[nome] = f"{nome}\n(Demanda: {demandas_orig[j]:.0f})"
        cores_cds.append("lightgreen") # Cor Verde
    
    # 4. Processar Nós Fictícios (se houver)
    if fabrica_ficticia:
        nome_ficticio = "FALTA (Fábrica Fict.)"
        nomes_fabricas.append(nome_ficticio) # Adiciona à lista de nomes
        falta_total = np.sum(solucao[-1, :n_cds_orig]) # Soma o que a Fab. Fictícia envia
        custom_labels[nome_ficticio] = f"{nome_ficticio}\n(Total: {falta_total:.0f})"
        cores_fabricas.append("lightcoral") # Cor Vermelha

    if cd_ficticio:
        nome_ficticio = "SOBRA (CD Fictício)"
        nomes_cds.append(nome_ficticio) # Adiciona à lista de nomes
        sobra_total = np.sum(solucao[:n_fab_orig, -1]) # Soma o que o CD Fictício recebe
        custom_labels[nome_ficticio] = f"{nome_ficticio}\n(Total: {sobra_total:.0f})"
        cores_cds.append("silver") # Cor Cinza

    # 5. Adicionar nós ao grafo (na ordem correta)
    G.add_nodes_from(nomes_fabricas, bipartite=0) # Lado esquerdo
    G.add_nodes_from(nomes_cds, bipartite=1)      # Lado direito
    
    # 6. Criar lista de cores final NA ORDEM CORRETA
    node_colors = cores_fabricas + cores_cds 
    
    # 7. Adicionar Arestas (Setas) e Rótulos
    edge_labels = {}
    n_fabricas_total, n_cds_total = solucao.shape

    for i in range(n_fabricas_total):
        for j in range(n_cds_total):
            quantidade = solucao[i, j]
            if quantidade > 0.01: # Apenas desenha rotas usadas
                origem = nomes_fabricas[i]
                destino = nomes_cds[j]
                G.add_edge(origem, destino, weight=quantidade)
                
                label_qtd = f"Qtd: {quantidade:.0f}"
                label_custo = ""
                
                # Verifica se a rota é real (não fictícia)
                is_real_fabrica = (i < n_fab_orig)
                is_real_cd = (j < n_cds_orig)
                
                if is_real_fabrica and is_real_cd:
                    custo_rota = custos_matriz[i, j]
                    label_custo = f"Custo: R$ {custo_rota:.2f}"
                else:
                    label_custo = "Custo: R$ 0.00" # Rota fictícia
                
                edge_labels[(origem, destino)] = f"{label_qtd}\n{label_custo}"

    # 8. Desenhar o Grafo
    pos = nx.bipartite_layout(G, nomes_fabricas)
    
    plt.figure(figsize=(16, max(9, n_fabricas_total, n_cds_total) * 1.6))
    
    nx.draw(G, 
            pos, 
            with_labels=True,
            labels=custom_labels,
            node_color=node_colors, # Aplica a lista de cores correta
            node_size=5500,
            font_size=9,
            font_weight='bold', 
            arrows=True,
            arrowstyle='->',
            arrowsize=20
           )
    
    # Desenha os rótulos das arestas (custo/qtd)
    nx.draw_networkx_edge_labels(G, 
                                 pos, 
                                 edge_labels=edge_labels,
                                 font_color='red',
                                 font_size=8,
                                 font_weight='bold',
                                 label_pos=0.2, # Posição do rótulo na seta
                                 bbox=dict(facecolor='white', alpha=0.4, pad=0.1, edgecolor='none')
                                )
    
    plt.title(f'Fluxo de Distribuição Otimizado ({n_fab_orig}x{n_cds_orig}) - Rede')

# --- Execução Principal ---

print("Bem-vindo ao Otimizador de Transporte")
print("-------------------------------------")
print("[1] Inserir dados manualmente")
print("[2] Gerar dados aleatoriamente")

choice = ""
while choice not in ['1', '2']:
    choice = input("Escolha o modo de entrada (1 ou 2): ")

c_custos_orig, b_ofertas_orig, b_demandas_orig, n_fab_orig, n_cds_orig = (None,) * 5

if choice == '1':
    # Modo Manual
    c_custos_orig, b_ofertas_orig, b_demandas_orig, n_fab_orig, n_cds_orig = obter_dados_manuais()
    
elif choice == '2':
    # --- BLOCO MODIFICADO ---
    # Modo Aleatório
    n_fab_rand = obter_inteiro_positivo("Digite o número de Fábricas: ")
    n_cds_rand = obter_inteiro_positivo("Digite o número de CDs: ")
    
    # Pergunta nova: Balanceado ou Não?
    is_balanceado = obter_sim_nao("Deseja gerar um problema balanceado (S/N)? ")
    
    # Chama a função de geração atualizada
    c_custos_orig, b_ofertas_orig, b_demandas_orig, n_fab_orig, n_cds_orig = \
        gerar_problema_transporte(n_fab_rand, n_cds_rand, balanceado=is_balanceado)

# --- Lógica de Balanceamento (Nó Fictício) ---
# Esta seção agora lida com dados manuais ou aleatórios não-balanceados
c_custos = np.copy(c_custos_orig)
b_ofertas = np.copy(b_ofertas_orig)
b_demandas = np.copy(b_demandas_orig)
n_fabricas = n_fab_orig
n_cds = n_cds_orig

fabrica_ficticia = False
cd_ficticio = False

total_oferta = np.sum(b_ofertas)
total_demanda = np.sum(b_demandas)

# Verifica se o balanceamento é realmente necessário
if np.isclose(total_oferta, total_demanda):
    print("\nINFO: Problema está balanceado. Nenhum nó fictício necessário.")
    
elif total_oferta > total_demanda:
    # Caso de SOBRA (Oferta > Demanda)
    print("\nDetectada SOBRA de oferta. Criando um 'CD Fictício' para absorver o excesso.")
    cd_ficticio = True
    sobra = total_oferta - total_demanda
    b_demandas = np.append(b_demandas, sobra)
    n_cds += 1
    
    # Adiciona custos zero para o CD fictício
    c_custos_matriz = c_custos.reshape((n_fab_orig, n_cds_orig))
    coluna_zeros = np.zeros((n_fab_orig, 1))
    c_custos_matriz = np.hstack((c_custos_matriz, coluna_zeros))
    c_custos = c_custos_matriz.flatten()
    
elif total_demanda > total_oferta:
    # Caso de FALTA (Demanda > Oferta)
    print("\nDetectada FALTA de oferta (demanda maior). Criando 'Fábrica Fictícia' para suprir a falta.")
    fabrica_ficticia = True
    falta = total_demanda - total_oferta
    b_ofertas = np.append(b_ofertas, falta)
    n_fabricas += 1
    
    # Adiciona custos zero da Fábrica fictícia
    c_custos_matriz = c_custos.reshape((n_fab_orig, n_cds_orig))
    linha_zeros = np.zeros((1, n_cds_orig))
    c_custos_matriz = np.vstack((c_custos_matriz, linha_zeros))
    c_custos = c_custos_matriz.flatten()

# --- Otimização ---
n_vars = n_fabricas * n_cds
A_eq_matriz = construir_matrizes_restricao_eq(n_fabricas, n_cds, n_vars)
b_eq_limites = np.concatenate([b_ofertas, b_demandas])
bounds_variaveis = [(0, None) for _ in range(n_vars)] # Limites (>= 0)

print("\nCalculando a solução ótima (problema balanceado)...")
resultado = linprog(c_custos,
                    A_eq=A_eq_matriz,
                    b_eq=b_eq_limites,
                    bounds=bounds_variaveis,
                    method='highs') # 'highs' é o método padrão e eficiente

# --- Exibir resultados e Gráficos ---
if resultado.success:
    print("--- Plano de Transporte Ótimo Encontrado ---")
    # O custo (resultado.fun) já ignora os custos fictícios (que são zero)
    print(f"Custo Total Mínimo (Real): R$ {resultado.fun:.2f}")
    
    # Formata a solução (vetor) de volta para uma matriz 2D
    solucao_matriz = resultado.x.reshape(n_fabricas, n_cds)
    # Arredonda valores (solver pode retornar ex: 49.9999)2
    solucao_matriz = np.round(solucao_matriz, decimals=0)
    
    print("\nPlano de Distribuição Completo (Incluindo rotas fictícias):")
    print(solucao_matriz)
    
    print("\nGerando gráfico de barras...")
    plotar_solucao(solucao_matriz, n_fabricas, n_cds, n_fab_orig, n_cds_orig, cd_ficticio, fabrica_ficticia)
    
    print("Gerando gráfico de rede (grafos)...")
    # --- CHAMADA MODIFICADA ---
    plotar_grafo_rede(solucao_matriz, n_fab_orig, n_cds_orig, b_ofertas_orig, b_demandas_orig, c_custos_orig, cd_ficticio, fabrica_ficticia)
    
    print("Exibindo gráficos. (Pode haver duas janelas separadas)")
    plt.show() 
    
else:
    print("\n--- Falha ao Otimizar ---")
    print(f"Mensagem: {resultado.message}")

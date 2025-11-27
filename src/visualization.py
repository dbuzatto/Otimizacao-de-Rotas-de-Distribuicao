from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


def plot_bar_chart(
    flow: np.ndarray,
    factory_names,
    customer_names,
    show: bool = False,
    save_path: Optional[Path] = None,
):
    # Barras empilhadas mostrando quanto cada fabrica envia a cada cliente
    customers = np.arange(flow.shape[1])
    fig, ax = plt.subplots(figsize=(max(8, len(customers) * 1.4), 6))
    bottom = np.zeros_like(customers, dtype=float)
    for i, factory in enumerate(factory_names):
        ax.bar(customers, flow[i], bottom=bottom, label=factory)
        bottom = bottom + flow[i]
    ax.set_xticks(customers)
    ax.set_xticklabels(customer_names, rotation=0)
    ax.set_ylabel("Fluxo enviado")
    ax.set_title("Fluxo por CD (barras empilhadas)")
    ax.legend(title="Fábricas")
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    fig.tight_layout()
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_network(
    flow: np.ndarray,
    costs: np.ndarray,
    factory_names,
    customer_names,
    show: bool = False,
    save_path: Optional[Path] = None,
):
    # Grafo bipartido com arestas somente para fluxos > 0
    G = nx.DiGraph()
    factories = list(factory_names)
    customers = list(customer_names)
    G.add_nodes_from(factories, bipartite=0)
    G.add_nodes_from(customers, bipartite=1)

    for i, f in enumerate(factories):
        for j, c in enumerate(customers):
            val = flow[i, j]
            if val > 1e-9:
                cost = costs[i, j] if i < costs.shape[0] and j < costs.shape[1] else 0.0
                G.add_edge(f, c, weight=val, cost=cost)

    pos = nx.bipartite_layout(G, factories)
    fig, ax = plt.subplots(figsize=(max(10, len(G.nodes) * 1.2), 7))
    node_colors = ["skyblue" if n in factories else "lightgreen" for n in G.nodes]
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_color=node_colors,
        node_size=2000,
        arrows=True,
        ax=ax,
    )

    labels = {}
    for u, v, data in G.edges(data=True):
        labels[(u, v)] = f"{data['weight']:.1f} @ {data['cost']:.1f}"
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, ax=ax, font_size=8)
    ax.set_title("Grafo bipartido de fluxos")
    fig.tight_layout()

    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)

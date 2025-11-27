from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
import numpy as np

from .config import RandomProblemConfig
from .model import TransportationData, validate_data

LOGGER = logging.getLogger(__name__)


def _prompt_vector(label: str, length: int) -> np.ndarray:
    values = []
    for idx in range(length):
        while True:
            raw = input(f"{label} {idx + 1}: ").strip()
            try:
                num = float(raw)
            except ValueError:
                print("Valor invalido. Digite um numero.")
                continue
            if num < 0:
                print("Valor precisa ser nao-negativo.")
                continue
            values.append(num)
            break
    return np.asarray(values, dtype=float)


def prompt_interactive_data() -> TransportationData:
    # Coleta dados via perguntas no terminal
    n_factories = int(input("Quantas fabricas? ").strip())
    n_customers = int(input("Quantos CDs? ").strip())
    supply = _prompt_vector("Oferta da Fabrica", n_factories)
    demand = _prompt_vector("Demanda do CD", n_customers)

    costs = np.zeros((n_factories, n_customers))
    for i in range(n_factories):
        for j in range(n_customers):
            while True:
                raw = input(f"Custo F{i + 1} -> C{j + 1}: ").strip()
                try:
                    costs[i, j] = float(raw)
                    break
                except ValueError:
                    print("Valor invalido. Digite um numero.")

    cap_answer = input("Deseja inserir capacidades por rota? (s/n): ").strip().lower()
    capacities = None
    if cap_answer in {"s", "sim"}:
        capacities = np.zeros_like(costs)
        for i in range(n_factories):
            for j in range(n_customers):
                while True:
                    raw = input(f"Capacidade maxima F{i + 1} -> C{j + 1} (vazio=infinito): ").strip()
                    if raw == "":
                        capacities[i, j] = np.inf
                        break
                    try:
                        capacities[i, j] = float(raw)
                        break
                    except ValueError:
                        print("Valor invalido. Digite um numero ou deixe em branco.")
    data = TransportationData(costs=costs, supply=supply, demand=demand, capacities=capacities)
    return validate_data(data)


def generate_random_data(cfg: RandomProblemConfig) -> TransportationData:
    # Geracao pseudoaleatoria de instancia, opcionalmente balanceada
    rng = np.random.default_rng(cfg.seed)
    supply = rng.integers(cfg.supply_min, cfg.supply_max + 1, size=cfg.n_factories)
    demand = rng.integers(cfg.demand_min, cfg.demand_max + 1, size=cfg.n_customers)
    costs = rng.integers(cfg.cost_min, cfg.cost_max + 1, size=(cfg.n_factories, cfg.n_customers))

    if cfg.balanced:
        total_supply = float(np.sum(supply))
        proportions = rng.random(cfg.n_customers)
        proportions /= proportions.sum()
        demand = np.floor(proportions * total_supply)
        demand[-1] += total_supply - demand.sum()

    data = TransportationData(costs=costs, supply=supply, demand=demand)
    LOGGER.info("Instancia aleatoria gerada: supply=%s demand=%s", supply, demand)
    return validate_data(data)


def load_from_json(path: Path) -> TransportationData:
    # Carrega formato JSON documentado (supply/demand/costs)
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    data = TransportationData(
        costs=payload["costs"],
        supply=payload["supply"],
        demand=payload["demand"],
        capacities=payload.get("capacities"),
        factory_names=payload.get("factory_names"),
        customer_names=payload.get("customer_names"),
    )
    return validate_data(data)


def load_from_csv(path: Path) -> TransportationData:
    # CSV simples: linha supply, linha demand, depois custos por fabrica
    rows = list(csv.reader(Path(path).read_text(encoding="utf-8").splitlines()))
    if len(rows) < 3:
        raise ValueError("CSV precisa ter pelo menos supply, demand e uma linha de custos")
    if not rows[0] or rows[0][0].lower() != "supply":
        raise ValueError("Primeira linha deve comecar com 'supply'")
    if not rows[1] or rows[1][0].lower() != "demand":
        raise ValueError("Segunda linha deve comecar com 'demand'")

    supply = np.asarray([float(x) for x in rows[0][1:] if x != ""], dtype=float)
    demand = np.asarray([float(x) for x in rows[1][1:] if x != ""], dtype=float)

    costs = []
    for row in rows[2:]:
        if not row:
            continue
        costs.append([float(x) for x in row[1 : 1 + demand.size]])
    costs = np.asarray(costs, dtype=float)

    return validate_data(TransportationData(costs=costs, supply=supply, demand=demand))


def load_instance(path: Path) -> TransportationData:
    # Despacha leitura conforme a extensao
    path = Path(path)
    if path.suffix.lower() == ".json":
        return load_from_json(path)
    if path.suffix.lower() == ".csv":
        return load_from_csv(path)
    raise ValueError("Formato de arquivo nao suportado. Use JSON ou CSV.")


def save_solution_matrix(path: Path, flow: np.ndarray, factory_names, customer_names) -> Path:
    # Exporta matriz de fluxos em CSV legivel
    path.parent.mkdir(parents=True, exist_ok=True)
    header = ",".join([""] + list(customer_names))
    rows = [",".join([factory_names[i]] + [f"{val:.4f}" for val in flow[i]]) for i in range(flow.shape[0])]
    path.write_text("\n".join([header] + rows), encoding="utf-8")
    return path


def save_summary(path: Path, result, metadata) -> Path:
    # Salva resumo JSON com status, custo e metadados de balanceamento
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "success": result.success,
        "status": result.status,
        "objective_value": result.objective_value,
        "message": result.message,
        "dummy_factory": metadata.dummy_factory,
        "dummy_customer": metadata.dummy_customer,
        "added_amount": metadata.added_amount,
    }
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return path

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np


def _ensure_float_array(values: Sequence[float], name: str) -> np.ndarray:
    try:
        arr = np.asarray(values, dtype=float)
    except Exception as exc:  
        raise ValueError(f"{name} must be convertible to a numeric array") from exc
    if arr.ndim != 1:
        raise ValueError(f"{name} must be a 1D array")
    return arr


def _ensure_matrix(values: Sequence[Sequence[float]], name: str) -> np.ndarray:
    try:
        arr = np.asarray(values, dtype=float)
    except Exception as exc:  
        raise ValueError(f"{name} must be convertible to a numeric matrix") from exc
    if arr.ndim != 2:
        raise ValueError(f"{name} must be a 2D matrix")
    return arr


def _default_names(prefix: str, count: int) -> List[str]:
    return [f"{prefix}{i+1}" for i in range(count)]


@dataclass
class TransportationData:
    costs: np.ndarray
    supply: np.ndarray
    demand: np.ndarray
    capacities: Optional[np.ndarray] = None
    factory_names: Optional[List[str]] = None
    customer_names: Optional[List[str]] = None

    def with_defaults(self) -> "TransportationData":
        factories = self.factory_names or _default_names("F", len(self.supply))
        customers = self.customer_names or _default_names("C", len(self.demand))
        return TransportationData(
            costs=self.costs,
            supply=self.supply,
            demand=self.demand,
            capacities=self.capacities,
            factory_names=factories,
            customer_names=customers,
        )


@dataclass
class BalanceMetadata:
    dummy_factory: bool
    dummy_customer: bool
    factory_names: List[str]
    customer_names: List[str]
    added_amount: float = 0.0


def validate_data(data: TransportationData) -> TransportationData:
    # Normaliza arrays e garante dimensões consistentes
    supply = _ensure_float_array(data.supply, "supply")
    demand = _ensure_float_array(data.demand, "demand")
    costs = _ensure_matrix(data.costs, "costs")

    if (supply < 0).any():
        raise ValueError("supply must be non-negative")
    if (demand < 0).any():
        raise ValueError("demand must be non-negative")
    if costs.shape != (supply.size, demand.size):
        raise ValueError(
            f"cost matrix shape {costs.shape} does not match "
            f"supply ({supply.size}) x demand ({demand.size})"
        )

    capacities = None
    if data.capacities is not None:
        capacities = _ensure_matrix(data.capacities, "capacities")
        if capacities.shape != costs.shape:
            raise ValueError("capacities must have the same shape as costs")
        if (capacities < 0).any():
            raise ValueError("capacities must be non-negative")

    factories = data.factory_names or _default_names("F", supply.size)
    customers = data.customer_names or _default_names("C", demand.size)
    if len(factories) != supply.size:
        raise ValueError("factory_names length must match supply size")
    if len(customers) != demand.size:
        raise ValueError("customer_names length must match demand size")

    return TransportationData(
        costs=costs,
        supply=supply,
        demand=demand,
        capacities=capacities,
        factory_names=factories,
        customer_names=customers,
    )


def balance_problem(data: TransportationData) -> Tuple[TransportationData, BalanceMetadata]:
    # Adiciona fábrica ou cliente fictício quando as somas divergem
    supply_total = float(np.sum(data.supply))
    demand_total = float(np.sum(data.demand))
    costs = data.costs.copy()
    capacities = data.capacities.copy() if data.capacities is not None else None
    factory_names = list(data.factory_names or _default_names("F", len(data.supply)))
    customer_names = list(data.customer_names or _default_names("C", len(data.demand)))

    dummy_factory = False
    dummy_customer = False
    added_amount = 0.0

    if np.isclose(supply_total, demand_total):
        return data, BalanceMetadata(
            dummy_factory=False,
            dummy_customer=False,
            factory_names=factory_names,
            customer_names=customer_names,
            added_amount=0.0,
        )

    if supply_total < demand_total:
        added_amount = demand_total - supply_total
        dummy_factory = True
        factory_names.append("Dummy Factory")
        supply = np.append(data.supply, added_amount)
        demand = data.demand.copy()
        costs = np.vstack([costs, np.zeros((1, costs.shape[1]))])
        if capacities is not None:
            capacities = np.vstack([capacities, np.full((1, capacities.shape[1]), np.inf)])
    else:
        added_amount = supply_total - demand_total
        dummy_customer = True
        customer_names.append("Dummy Customer")
        supply = data.supply.copy()
        demand = np.append(data.demand, added_amount)
        costs = np.hstack([costs, np.zeros((costs.shape[0], 1))])
        if capacities is not None:
            capacities = np.hstack([capacities, np.full((capacities.shape[0], 1), np.inf)])

    balanced = TransportationData(
        costs=costs,
        supply=supply,
        demand=demand,
        capacities=capacities,
        factory_names=factory_names,
        customer_names=customer_names,
    )
    return balanced, BalanceMetadata(
        dummy_factory=dummy_factory,
        dummy_customer=dummy_customer,
        factory_names=factory_names,
        customer_names=customer_names,
        added_amount=added_amount,
    )

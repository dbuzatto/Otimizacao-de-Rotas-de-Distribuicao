from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import linprog

@dataclass
class SolutionResult:
    success: bool
    status: int
    objective_value: Optional[float]
    flow: Optional[np.ndarray]
    message: str
    dual_supply: Optional[np.ndarray] = None
    dual_demand: Optional[np.ndarray] = None


def _build_constraints(
    costs: np.ndarray,
    supply: np.ndarray,
    demand: np.ndarray,
    capacities: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Optional[np.ndarray], Optional[np.ndarray], List[Tuple[float, Optional[float]]]]:
    m, n = costs.shape
    c = costs.flatten()

    A_eq = []
    b_eq = []
    for i in range(m):
        # Cada linha garante que a oferta da fábrica i seja totalmente enviada
        row = np.zeros(m * n)
        row[i * n : (i + 1) * n] = 1
        A_eq.append(row)
        b_eq.append(supply[i])

    for j in range(n):
        # Cada linha garante que a demanda do cliente j seja atendida
        row = np.zeros(m * n)
        row[j::n] = 1
        A_eq.append(row)
        b_eq.append(demand[j])

    A_ub = []
    b_ub = []
    if capacities is not None:
        for i in range(m):
            for j in range(n):
                cap = capacities[i, j]
                if np.isfinite(cap):
                    # Capacidade máxima por arco (inequação)
                    row = np.zeros(m * n)
                    row[i * n + j] = 1
                    A_ub.append(row)
                    b_ub.append(cap)

    bounds = [(0, None) for _ in range(m * n)]
    return c, np.array(A_eq), np.array(b_eq), (np.array(A_ub) if A_ub else None), (np.array(b_ub) if b_ub else None), bounds


def _extract_duals(result, supply_size: int, demand_size: int) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    if not hasattr(result, "eqlin") or result.eqlin is None:
        return None, None
    marginals = getattr(result.eqlin, "marginals", None)
    if marginals is None:
        return None, None
    marginals = np.asarray(marginals)
    if marginals.size != supply_size + demand_size:
        return None, None
    return marginals[:supply_size], marginals[supply_size:]


def solve_transportation_problem(
    costs: Sequence[Sequence[float]],
    supply: Sequence[float],
    demand: Sequence[float],
    capacities: Optional[Sequence[Sequence[float]]] = None,
    solver_method: str = "highs",
    max_iter: Optional[int] = None,
    tol: float = 1e-9,
) -> SolutionResult:
    costs_arr = np.asarray(costs, dtype=float)
    supply_arr = np.asarray(supply, dtype=float)
    demand_arr = np.asarray(demand, dtype=float)
    capacities_arr = None if capacities is None else np.asarray(capacities, dtype=float)

    # Constrói vetores/matrizes para linprog (A_eq, A_ub, bounds)
    c, A_eq, b_eq, A_ub, b_ub, bounds = _build_constraints(costs_arr, supply_arr, demand_arr, capacities_arr)
    options = {"tol": tol}
    if max_iter is not None:
        options["maxiter"] = max_iter

    result = linprog(
        c,
        A_ub=A_ub,
        b_ub=b_ub,
        A_eq=A_eq,
        b_eq=b_eq,
        bounds=bounds,
        method=solver_method,
        options=options,
    )

    flow = result.x.reshape(costs_arr.shape) if result.success and result.x is not None else None
    dual_supply, dual_demand = _extract_duals(result, supply_arr.size, demand_arr.size)
    objective_value = float(result.fun) if result.success and result.fun is not None else None

    return SolutionResult(
        success=bool(result.success),
        status=int(result.status),
        objective_value=objective_value,
        flow=flow,
        message=result.message,
        dual_supply=dual_supply,
        dual_demand=dual_demand,
    )

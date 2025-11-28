from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional
import numpy as np

from . import data_io
from .config import DEFAULT_IO_CONFIG, DEFAULT_RANDOM_CONFIG, DEFAULT_SOLVER_CONFIG, RandomProblemConfig, SolverConfig
from .model import balance_problem, validate_data
from .solver import solve_transportation_problem
from .visualization import plot_bar_chart, plot_network

LOGGER = logging.getLogger(__name__)


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s - %(name)s - %(message)s")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Problema de transporte via programacao linear (Simplex)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--mode", choices=["interactive", "file", "random"], required=True)
    parser.add_argument("--input", type=Path, help="Arquivo JSON ou CSV (modo file).")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_IO_CONFIG.output_dir, help="Diretorio para salvar resultados.")
    parser.add_argument("--save-plots", action="store_true", help="Salvar figuras em disco.")
    parser.add_argument("--show-plots", action="store_true", help="Exibir figuras interativamente.")
    parser.add_argument("--solver-method", default=DEFAULT_SOLVER_CONFIG.method, help="Metodo do scipy.optimize.linprog.")
    parser.add_argument("--max-iter", type=int, default=DEFAULT_SOLVER_CONFIG.max_iter, help="Iteracoes maximas do solver.")
    parser.add_argument("--tol", type=float, default=DEFAULT_SOLVER_CONFIG.tol, help="Tolerancia do solver.")
    parser.add_argument("--verbose", action="store_true", help="Logs detalhados.")
    # Opcoes para modo aleatorio
    parser.add_argument("--n-factories", type=int, default=DEFAULT_RANDOM_CONFIG.n_factories)
    parser.add_argument("--n-cds", type=int, default=DEFAULT_RANDOM_CONFIG.n_customers)
    parser.add_argument("--balanced", choices=["yes", "no"], default="yes")
    parser.add_argument("--cost-min", type=int, default=DEFAULT_RANDOM_CONFIG.cost_min)
    parser.add_argument("--cost-max", type=int, default=DEFAULT_RANDOM_CONFIG.cost_max)
    parser.add_argument("--supply-min", type=int, default=DEFAULT_RANDOM_CONFIG.supply_min)
    parser.add_argument("--supply-max", type=int, default=DEFAULT_RANDOM_CONFIG.supply_max)
    parser.add_argument("--demand-min", type=int, default=DEFAULT_RANDOM_CONFIG.demand_min)
    parser.add_argument("--demand-max", type=int, default=DEFAULT_RANDOM_CONFIG.demand_max)
    parser.add_argument("--seed", type=int, default=DEFAULT_RANDOM_CONFIG.seed)
    return parser.parse_args()


def _load_data(args: argparse.Namespace):
    # Decide a fonte dos dados conforme o modo solicitado
    if args.mode == "interactive":
        return data_io.prompt_interactive_data()
    if args.mode == "file":
        if not args.input:
            raise ValueError("Forneca --input no modo file.")
        return data_io.load_instance(args.input)
    random_cfg = RandomProblemConfig(
        n_factories=args.n_factories,
        n_customers=args.n_cds,
        cost_min=args.cost_min,
        cost_max=args.cost_max,
        supply_min=args.supply_min,
        supply_max=args.supply_max,
        demand_min=args.demand_min,
        demand_max=args.demand_max,
        balanced=args.balanced.lower() == "yes",
        seed=args.seed,
    )
    return data_io.generate_random_data(random_cfg)


def _report_solution(flow: np.ndarray, objective: float, factory_names, customer_names) -> None:
    print(f"Custo total minimo: {objective:.4f}")
    print("Matriz de fluxos (origem -> destino):")
    header = ["origem/destino"] + list(customer_names)
    col_widths = [max(len(h), 8) for h in header]
    fmt = " ".join([f"{{:<{w}}}" for w in col_widths])
    print(fmt.format(*header))
    for i, fname in enumerate(factory_names):
        row = [fname] + [f"{flow[i, j]:.2f}" for j in range(flow.shape[1])]
        print(fmt.format(*row))
    print("")


def _check_balance(flow: np.ndarray, supply: np.ndarray, demand: np.ndarray) -> bool:
    # Confere se todas as ofertas e demandas (incluindo ficticias) foram atendidas
    return np.allclose(flow.sum(axis=1), supply) and np.allclose(flow.sum(axis=0), demand)


def run_cli(namespace: Optional[argparse.Namespace] = None) -> int:
    args = namespace or _parse_args()
    _setup_logging(args.verbose)

    try:
        raw_data = _load_data(args)
        data = validate_data(raw_data)
    except Exception as exc:
        LOGGER.exception("Falha na leitura/validacao dos dados.")
        print(f"Erro ao carregar dados: {exc}")
        return 1

    # Balanceia oferta/demanda adicionando nos ficticios quando necessario
    balanced_data, metadata = balance_problem(data)
    LOGGER.info(
        "Balanceamento: dummy_factory=%s dummy_customer=%s added=%.2f",
        metadata.dummy_factory,
        metadata.dummy_customer,
        metadata.added_amount,
    )

    # Resolve o PL com linprog/Simplex
    solver_cfg = SolverConfig(method=args.solver_method, max_iter=args.max_iter, tol=args.tol)
    result = solve_transportation_problem(
        costs=balanced_data.costs,
        supply=balanced_data.supply,
        demand=balanced_data.demand,
        capacities=balanced_data.capacities,
        solver_method=solver_cfg.method,
        max_iter=solver_cfg.max_iter,
        tol=solver_cfg.tol,
    )

    if not result.success or result.flow is None or result.objective_value is None:
        print("O solver nao encontrou solucao otima.")
        print(f"Status: {result.status} - {result.message}")
        return 2

    _report_solution(result.flow, result.objective_value, balanced_data.factory_names, balanced_data.customer_names)
    print(f"Checagem de balanceamento (incluindo ficticios): {'OK' if _check_balance(result.flow, balanced_data.supply, balanced_data.demand) else 'Falhou'}")

    # Exporta resultados
    output_dir = Path(args.output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    data_io.save_solution_matrix(output_dir / "solution_matrix.csv", result.flow, balanced_data.factory_names, balanced_data.customer_names)
    data_io.save_summary(output_dir / "summary.json", result, metadata)

    # Plots opcionais
    if args.save_plots or args.show_plots:
        plot_bar_chart(
            flow=result.flow,
            factory_names=balanced_data.factory_names,
            customer_names=balanced_data.customer_names,
            show=args.show_plots,
            save_path=(output_dir / "solution_bars.png") if args.save_plots else None,
        )
        plot_network(
            flow=result.flow,
            costs=balanced_data.costs,
            factory_names=balanced_data.factory_names,
            customer_names=balanced_data.customer_names,
            show=args.show_plots,
            save_path=(output_dir / "solution_network.png") if args.save_plots else None,
        )

    return 0

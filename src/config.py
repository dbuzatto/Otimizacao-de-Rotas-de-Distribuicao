from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class RandomProblemConfig:
    n_factories: int = 3
    n_customers: int = 4
    cost_min: int = 1
    cost_max: int = 50
    supply_min: int = 20
    supply_max: int = 80
    demand_min: int = 15
    demand_max: int = 70
    balanced: bool = True
    seed: Optional[int] = None


@dataclass
class SolverConfig:
    method: str = "highs"
    tol: float = 1e-9
    max_iter: Optional[int] = None


@dataclass
class PlotConfig:
    show_plots: bool = False
    save_plots: bool = False
    output_dir: Path = Path("results")


@dataclass
class IOConfig:
    output_dir: Path = Path("results")
    save_summary: bool = True
    save_solution_matrix: bool = True


DEFAULT_RANDOM_CONFIG = RandomProblemConfig()
DEFAULT_SOLVER_CONFIG = SolverConfig()
DEFAULT_PLOT_CONFIG = PlotConfig()
DEFAULT_IO_CONFIG = IOConfig()

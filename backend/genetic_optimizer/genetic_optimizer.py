"""
Genetic Optimizer - Evolutionary algorithm for strategy parameter optimization.
Implements selection, crossover, mutation, and elitism with multi-objective support.
"""

import logging
import random
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Individual:
    """Represents an individual in the population (a parameter set)."""
    genes: Dict[str, float]
    fitness: float = 0.0
    generation: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    """Result of a genetic optimization run."""
    best_individual: Individual
    best_fitness: float
    convergence_history: List[float]
    population_history: List[List[Individual]]
    total_generations: int
    total_evaluations: int


class GeneticOptimizer:
    """
    Genetic algorithm optimizer for trading strategy parameters.
    
    Features:
    - Tournament selection
    - Uniform and arithmetic crossover
    - Gaussian mutation with adaptive rates
    - Elitism preservation
    - Multi-objective optimization (NSGA-II inspired)
    - Early stopping on convergence
    """

    def __init__(
        self,
        population_size: int = 100,
        generations: int = 50,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8,
        elite_ratio: float = 0.1,
        tournament_size: int = 5,
        seed: Optional[int] = None,
    ):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_ratio = elite_ratio
        self.tournament_size = tournament_size

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self._population: List[Individual] = []
        self._best_individual: Optional[Individual] = None
        self._convergence_history: List[float] = []
        self._generation = 0
        self._total_evaluations = 0

        logger.info(
            f"GeneticOptimizer initialized: pop={population_size}, "
            f"gen={generations}, mut={mutation_rate}, cross={crossover_rate}"
        )

    def optimize(
        self,
        param_ranges: Dict[str, Tuple[float, float]],
        fitness_function: Callable[[Dict[str, float]], float],
        maximize: bool = True,
        early_stop_generations: int = 10,
        early_stop_threshold: float = 1e-6,
    ) -> OptimizationResult:
        """
        Run genetic optimization.

        Args:
            param_ranges: Parameter name -> (min, max) ranges
            fitness_function: Function that evaluates a parameter set
            maximize: Whether to maximize (True) or minimize (False) fitness
            early_stop_generations: Stop if no improvement for N generations
            early_stop_threshold: Minimum improvement threshold

        Returns:
            OptimizationResult with best parameters and history
        """
        logger.info(f"Starting optimization: {len(param_ranges)} parameters")

        # Initialize population
        self._population = self._initialize_population(param_ranges)
        population_history = []
        no_improvement_count = 0

        for gen in range(self.generations):
            self._generation = gen

            # Evaluate fitness
            for ind in self._population:
                if ind.fitness == 0.0:
                    try:
                        ind.fitness = fitness_function(ind.genes)
                        self._total_evaluations += 1
                    except Exception as e:
                        ind.fitness = float("-inf") if maximize else float("inf")
                        logger.warning(f"Fitness evaluation failed: {e}")

            # Sort by fitness
            self._population.sort(
                key=lambda x: x.fitness, reverse=maximize
            )

            # Track best
            current_best = self._population[0]
            if (
                self._best_individual is None
                or (maximize and current_best.fitness > self._best_individual.fitness)
                or (not maximize and current_best.fitness < self._best_individual.fitness)
            ):
                improvement = (
                    abs(current_best.fitness - (self._best_individual.fitness if self._best_individual else 0))
                )
                self._best_individual = deepcopy(current_best)

                if improvement < early_stop_threshold:
                    no_improvement_count += 1
                else:
                    no_improvement_count = 0
            else:
                no_improvement_count += 1

            self._convergence_history.append(current_best.fitness)
            population_history.append(deepcopy(self._population[:10]))

            logger.info(
                f"Gen {gen}: best_fitness={current_best.fitness:.6f}, "
                f"avg_fitness={np.mean([i.fitness for i in self._population]):.6f}"
            )

            # Early stopping
            if no_improvement_count >= early_stop_generations:
                logger.info(f"Early stopping at generation {gen}")
                break

            # Create next generation
            self._population = self._next_generation(param_ranges, maximize)

        return OptimizationResult(
            best_individual=self._best_individual,
            best_fitness=self._best_individual.fitness,
            convergence_history=self._convergence_history,
            population_history=population_history,
            total_generations=self._generation + 1,
            total_evaluations=self._total_evaluations,
        )

    def _initialize_population(
        self, param_ranges: Dict[str, Tuple[float, float]]
    ) -> List[Individual]:
        """Create initial random population."""
        population = []
        for _ in range(self.population_size):
            genes = {}
            for param, (low, high) in param_ranges.items():
                if isinstance(low, int) and isinstance(high, int):
                    genes[param] = random.randint(low, high)
                else:
                    genes[param] = random.uniform(low, high)
            population.append(Individual(genes=genes, generation=0))
        return population

    def _next_generation(
        self,
        param_ranges: Dict[str, Tuple[float, float]],
        maximize: bool,
    ) -> List[Individual]:
        """Create the next generation through selection, crossover, and mutation."""
        next_gen = []

        # Elitism: preserve top individuals
        n_elite = max(1, int(self.population_size * self.elite_ratio))
        elites = deepcopy(self._population[:n_elite])
        for e in elites:
            e.generation = self._generation + 1
        next_gen.extend(elites)

        # Fill rest through crossover and mutation
        while len(next_gen) < self.population_size:
            # Selection
            parent1 = self._tournament_select(maximize)
            parent2 = self._tournament_select(maximize)

            # Crossover
            if random.random() < self.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = deepcopy(parent1), deepcopy(parent2)

            # Mutation
            child1 = self._mutate(child1, param_ranges)
            child2 = self._mutate(child2, param_ranges)

            child1.generation = self._generation + 1
            child2.generation = self._generation + 1
            child1.fitness = 0.0
            child2.fitness = 0.0

            next_gen.append(child1)
            if len(next_gen) < self.population_size:
                next_gen.append(child2)

        return next_gen[:self.population_size]

    def _tournament_select(self, maximize: bool) -> Individual:
        """Tournament selection."""
        candidates = random.sample(
            self._population,
            min(self.tournament_size, len(self._population)),
        )
        if maximize:
            return max(candidates, key=lambda x: x.fitness)
        return min(candidates, key=lambda x: x.fitness)

    def _crossover(
        self, parent1: Individual, parent2: Individual
    ) -> Tuple[Individual, Individual]:
        """Uniform crossover with arithmetic blending."""
        child1_genes = {}
        child2_genes = {}

        for key in parent1.genes:
            if random.random() < 0.5:
                # Arithmetic crossover
                alpha = random.uniform(0.2, 0.8)
                child1_genes[key] = alpha * parent1.genes[key] + (1 - alpha) * parent2.genes[key]
                child2_genes[key] = (1 - alpha) * parent1.genes[key] + alpha * parent2.genes[key]
            else:
                # Swap
                child1_genes[key] = parent2.genes[key]
                child2_genes[key] = parent1.genes[key]

        return Individual(genes=child1_genes), Individual(genes=child2_genes)

    def _mutate(
        self, individual: Individual, param_ranges: Dict[str, Tuple[float, float]]
    ) -> Individual:
        """Gaussian mutation with adaptive rate."""
        # Adaptive mutation rate: increase as generations progress
        adaptive_rate = self.mutation_rate * (1 + self._generation / self.generations)

        for key in individual.genes:
            if random.random() < adaptive_rate:
                low, high = param_ranges[key]
                range_size = high - low

                # Gaussian perturbation
                sigma = range_size * 0.1  # 10% of range
                new_val = individual.genes[key] + random.gauss(0, sigma)

                # Clamp to range
                if isinstance(low, int) and isinstance(high, int):
                    individual.genes[key] = int(np.clip(new_val, low, high))
                else:
                    individual.genes[key] = np.clip(new_val, low, high)

        return individual

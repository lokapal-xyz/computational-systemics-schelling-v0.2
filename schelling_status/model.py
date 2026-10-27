"""Schelling model driven by Operational Status.

Each step activates agents in random order. An agent carries two fixed
StatusEntry objects in v0.2, one for ``type`` and one for ``mark``. The
type-only path carries the single ``type`` entry, on the same random stream
as v0.1.

Operational Status:

- Fronterization is the attribute value on a StatusEntry (0 or 1).
- Permeability is that entry's threshold in [0, 1].
- Receptivity fires when any entry's local similarity is strictly below
  its own Permeability.
- Proceptivity moves the agent to one random empty cell when Receptivity
  fires.
"""

from __future__ import annotations

import numbers

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import Cell, OrthogonalMooreGrid

from schelling_status.agent import SchellingAgent
from schelling_status.status import StatusEntry


class SchellingModel(Model):
    """Grid of agents with two fixed binary criteria.

    Defaults follow the v0.2 spec: 50×50, vacancy 0.15, equal groups on
    ``type`` and on ``mark``, Moore neighborhood, non-toroidal, each
    Permeability 0.4, up to 150 steps.

    The constructor is keyword-only. The dashboard aliases are ``width``,
    ``height``, and ``density`` (1 − vacancy rate). ``type_share`` and
    ``mark_share`` are the fraction of agents with Fronterization 1 on that
    criterion. Omit a share for equal groups.

    There is no single ``permeability`` argument. Pass ``permeability_type``
    and ``permeability_mark``. ``n_types`` and ``minority_fraction`` are
    rejected. v0.2 is binary, and ``type_share`` replaces the v0.1 minority
    fraction.

    Logged after the initial grid (step 0) and after every step:

    - dissatisfied: agents whose Receptivity fires (any entry)
    - dissatisfied_type, dissatisfied_mark: breaches of that entry
    - dissatisfied_both: agents counted in both breach columns
    - moves: agents who relocated during that step (0 at step 0)
    - segregation_type, segregation_mark: mean of defined ratios on that
      criterion

    The type-only path (``include_mark=False``) logs the v0.1 columns
    instead. ``segregation_index`` on that path is the type mean.

    The run stops early when dissatisfied reaches 0. ``step`` does not
    enforce the step cap. ``run.py`` does.
    """

    def __init__(
        self,
        *,
        grid_width: int | None = None,
        grid_height: int | None = None,
        width: int | None = None,
        height: int | None = None,
        vacancy_rate: float | None = None,
        density: float | None = None,
        permeability_type: float = 0.4,
        permeability_mark: float = 0.4,
        type_share: float | None = None,
        mark_share: float | None = None,
        include_mark: bool = True,
        steps: int = 150,
        seed: int | str | None = None,
        permeability: float | None = None,
        n_types: int | None = None,
        minority_fraction: float | None = None,
    ) -> None:
        """Build a random grid and record the initial metrics.

        Args:
            grid_width: Cells along x. CLI name. Default 50.
            grid_height: Cells along y. CLI name. Default 50.
            width: Dashboard name for grid_width.
            height: Dashboard name for grid_height.
            vacancy_rate: Fraction of cells left empty, in [0, 1). Default 0.15.
            density: Fraction of cells occupied, in (0, 1]. Dashboard name.
            permeability_type: Threshold stored on the type entry, in [0, 1].
            permeability_mark: Threshold stored on the mark entry, in [0, 1].
                Ignored when include_mark is false.
            type_share: Fraction with type Fronterization 1. None means
                equal groups, with value 0 receiving the extra agent when
                the count is odd.
            mark_share: Fraction with mark Fronterization 1. None means
                equal groups. Ignored when include_mark is false.
            include_mark: False is the type-only path. One entry, named type,
                and no mark draw, so the random stream matches v0.1.
            steps: Maximum sweeps for the CLI runner. The dashboard plays
                until nobody is dissatisfied.
            seed: RNG seed. Integers and numeric strings are accepted.
                None draws a fresh seed.
            permeability: Rejected. Name the criterion.
            n_types: Rejected. v0.2 is binary.
            minority_fraction: Rejected. Pass type_share.
        """
        if permeability is not None:
            raise TypeError(
                "permeability is not a v0.2 argument; "
                "pass permeability_type and permeability_mark"
            )
        if n_types is not None:
            raise TypeError("n_types is not a v0.2 argument; fronterization is binary")
        if minority_fraction is not None:
            raise TypeError(
                "minority_fraction is not a v0.2 argument; pass type_share"
            )
        if not isinstance(include_mark, bool):
            raise TypeError("include_mark must be a bool")

        super().__init__(rng=_coerce_seed(seed))
        self.grid_width = _positive_int(
            "width", _one_of("width", width, "grid_width", grid_width, 50)
        )
        self.grid_height = _positive_int(
            "height", _one_of("height", height, "grid_height", grid_height, 50)
        )
        self.density, self.vacancy_rate = _density_and_vacancy(density, vacancy_rate)
        self.permeability_type = _unit_interval(
            "permeability_type", permeability_type, upper_inclusive=True
        )
        self.permeability_mark = _unit_interval(
            "permeability_mark", permeability_mark, upper_inclusive=True
        )
        self.type_share = _optional_share("type_share", type_share)
        self.mark_share = _optional_share("mark_share", mark_share)
        self.include_mark = include_mark
        self.max_steps = _positive_int("steps", steps)

        self.grid = OrthogonalMooreGrid(
            (self.grid_width, self.grid_height),
            torus=False,
            capacity=1,
            random=self.random,
        )
        self._place_agents()

        self.moves = 0
        self.dissatisfied = 0
        self.dissatisfied_type = 0
        self.dissatisfied_mark = 0
        self.dissatisfied_both = 0
        self.segregation_type = 0.0
        self.segregation_mark = 0.0
        if self.include_mark:
            reporters = {
                "dissatisfied": "dissatisfied",
                "dissatisfied_type": "dissatisfied_type",
                "dissatisfied_mark": "dissatisfied_mark",
                "dissatisfied_both": "dissatisfied_both",
                "moves": "moves",
                "segregation_type": "segregation_type",
                "segregation_mark": "segregation_mark",
            }
        else:
            # Same columns as v0.1. segregation_index is the type mean.
            self.segregation_index = 0.0
            reporters = {
                "dissatisfied": "dissatisfied",
                "moves": "moves",
                "segregation_index": "segregation_index",
            }
        self.datacollector = DataCollector(model_reporters=reporters)
        self._record_state()

    def _place_agents(self) -> None:
        """Fill the grid and assign Fronterization.

        Occupied cells are chosen first. Type values are drawn and shuffled,
        then mark values, with a separate shuffle. The type-only path stops
        after the type shuffle so it consumes randomness in the v0.1 order.
        """
        n_cells = self.grid_width * self.grid_height
        n_agents = round(n_cells * (1.0 - self.vacancy_rate))
        if n_agents < 1:
            raise ValueError("vacancy_rate leaves no agents on the grid")
        if n_agents > n_cells:
            raise ValueError("agent count exceeds the number of cells")

        cells = list(self.grid.all_cells)
        chosen = self.random.sample(cells, n_agents)
        type_values = _share_values(n_agents, self.type_share)
        self.random.shuffle(type_values)

        mark_values: list[int] | None = None
        if self.include_mark:
            mark_values = _share_values(n_agents, self.mark_share)
            self.random.shuffle(mark_values)

        for index, cell in enumerate(chosen):
            entries = [
                StatusEntry(
                    criterion="type",
                    fronterization=type_values[index],
                    permeability=self.permeability_type,
                    mutable=False,
                )
            ]
            if mark_values is not None:
                entries.append(
                    StatusEntry(
                        criterion="mark",
                        fronterization=mark_values[index],
                        permeability=self.permeability_mark,
                        mutable=False,
                    )
                )
            SchellingAgent(self, cell, entries)

    def random_empty_cell(self) -> Cell | None:
        """Return a random empty cell, or None when the grid is full."""
        try:
            cell = self.grid.select_random_empty_cell()
        except IndexError:
            return None
        if not cell.is_empty:
            return None
        return cell

    def _mean_similarity(self, criterion: str) -> float:
        """Mean of defined local-similarity ratios on one criterion.

        Agents with no occupied neighbors are omitted. Returns 0.0 when no
        agent has a defined ratio on this criterion.
        """
        ratios: list[float] = []
        for agent in self.agents:
            for entry in agent.statuses:
                if entry.criterion != criterion:
                    continue
                ratio = agent.local_similarity(entry)
                if ratio is not None:
                    ratios.append(ratio)
                break
        if not ratios:
            return 0.0
        return sum(ratios) / len(ratios)

    def _count_breaches(self, criterion: str) -> int:
        """Agents whose ratio on ``criterion`` is defined and strictly below its Permeability."""
        count = 0
        for agent in self.agents:
            for entry in agent.statuses:
                if entry.criterion != criterion:
                    continue
                ratio = agent.local_similarity(entry)
                if ratio is not None and ratio < entry.permeability:
                    count += 1
                break
        return count

    def _count_breaches_both(self) -> int:
        """Agents breached on type and on mark. Each is still one dissatisfied agent."""
        count = 0
        for agent in self.agents:
            type_hit = False
            mark_hit = False
            for entry in agent.statuses:
                ratio = agent.local_similarity(entry)
                hit = ratio is not None and ratio < entry.permeability
                if entry.criterion == "type":
                    type_hit = hit
                elif entry.criterion == "mark":
                    mark_hit = hit
            if type_hit and mark_hit:
                count += 1
        return count

    def count_dissatisfied(self) -> int:
        """Agents for whom Receptivity currently fires."""
        return sum(1 for agent in self.agents if agent.receptivity())

    def fronterization_grid(self, criterion: str = "type") -> list[list[object]]:
        """Configuration as rows of Fronterization values.

        Pass ``"type"`` or ``"mark"``. Row index is y, column index is x.
        An empty cell is None.
        """
        grid: list[list[object]] = [
            [None for _ in range(self.grid_width)] for _ in range(self.grid_height)
        ]
        for agent in self.agents:
            x, y = agent.position
            grid[y][x] = agent.fronterization_on(criterion)
        return grid

    def _record_state(self) -> None:
        """Snapshot breach counts and both segregation indexes, then store the row."""
        self.dissatisfied = self.count_dissatisfied()
        self.dissatisfied_type = self._count_breaches("type")
        self.segregation_type = self._mean_similarity("type")
        if self.include_mark:
            self.dissatisfied_mark = self._count_breaches("mark")
            self.dissatisfied_both = self._count_breaches_both()
            self.segregation_mark = self._mean_similarity("mark")
        else:
            self.dissatisfied_mark = 0
            self.dissatisfied_both = 0
            self.segregation_mark = 0.0
            self.segregation_index = self.segregation_type
        self.datacollector.collect(self)
        if self.dissatisfied == 0:
            self.running = False

    def step(self) -> None:
        """Run one random-sequential sweep and log the resulting grid.

        The loop body is ``activate`` on each agent. That method walks the
        status list, so the two criteria do not change this step.
        """
        self.moves = 0
        self.agents.shuffle_do("activate")
        self._record_state()


def _one_of(name_a: str, value_a, name_b: str, value_b, default):
    """Return the single provided alias, or the default when both are absent."""
    if value_a is not None and value_b is not None:
        raise ValueError(f"pass {name_a} or {name_b}, not both")
    if value_a is not None:
        return value_a
    if value_b is not None:
        return value_b
    return default


def _density_and_vacancy(
    density: float | None, vacancy_rate: float | None
) -> tuple[float, float]:
    """Resolve occupancy. Density is the share of filled cells."""
    if density is not None and vacancy_rate is not None:
        raise ValueError("pass density or vacancy_rate, not both")
    if density is not None:
        density = _unit_interval("density", density, upper_inclusive=True)
        if density <= 0.0:
            raise ValueError("density must be in (0, 1]")
        return density, 1.0 - density
    if vacancy_rate is None:
        vacancy_rate = 0.15
    vacancy_rate = _unit_interval("vacancy_rate", vacancy_rate, upper_inclusive=False)
    return 1.0 - vacancy_rate, vacancy_rate


def _coerce_seed(value: int | str | None) -> int | None:
    """Accept an int seed or the numeric string Solara's text input produces."""
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("seed must be an integer")
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return None
        try:
            return int(text)
        except ValueError as exc:
            raise ValueError("seed must be an integer") from exc
    if isinstance(value, numbers.Integral):
        return int(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    raise TypeError("seed must be an integer")


def _positive_int(name: str, value: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer >= 1")
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, numbers.Integral) and not isinstance(value, int):
        value = int(value)
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be an integer >= 1")
    return value


def _unit_interval(name: str, value: float, *, upper_inclusive: bool) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number")
    value = float(value)
    too_high = value > 1.0 if upper_inclusive else value >= 1.0
    if value < 0.0 or too_high:
        bound = "[0, 1]" if upper_inclusive else "[0, 1)"
        raise ValueError(f"{name} must be in {bound}")
    return value


def _optional_share(name: str, value: float | None) -> float | None:
    if value is None:
        return None
    return _unit_interval(name, value, upper_inclusive=True)


def _share_values(n_agents: int, share: float | None) -> list[int]:
    """Fronterization values for one criterion, before the shuffle.

    None splits the agents as equally as the count allows. Value 0 receives
    the extra agent when the count is odd. A share is the fraction with
    value 1: round(n_agents * share) agents get 1, and the rest get 0.
    """
    if share is None:
        return _balanced_values(n_agents, 2)
    n_ones = round(n_agents * share)
    n_ones = min(max(n_ones, 0), n_agents)
    return [1] * n_ones + [0] * (n_agents - n_ones)


def _balanced_values(n_agents: int, n_types: int) -> list[int]:
    """Split agents into groups as equal as the count allows."""
    base, extra = divmod(n_agents, n_types)
    values: list[int] = []
    for type_id in range(n_types):
        count = base + (1 if type_id < extra else 0)
        values.extend([type_id] * count)
    return values

"""Schelling agent whose move rule is Operational Status.

The step loop never assumes how many status entries an agent carries.
Receptivity checks every entry. Proceptivity runs if any entry is breached.
v0.2 gives each agent a type entry and a mark entry. The type-only path
gives each agent the type entry alone. activate() is the same either way.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mesa.discrete_space import CellAgent

from schelling_status.status import StatusEntry

if TYPE_CHECKING:
    from schelling_status.model import SchellingModel


class SchellingAgent(CellAgent):
    """An agent on the grid with a list of StatusEntry objects.

    v0.2 puts two fixed binary entries in that list: criterion "type" and
    criterion "mark", each value 0 or 1. The type-only path puts one entry,
    criterion "type". activate() does not change with the length of the list.
    """

    def __init__(self, model: SchellingModel, cell, statuses: list[StatusEntry]) -> None:
        """Place the agent on `cell` with its status list.

        Args:
            model: The owning SchellingModel.
            cell: Grid cell to occupy. Capacity is one agent.
            statuses: One or more StatusEntry objects. Copied into a list.
        """
        if not statuses:
            raise ValueError("an agent needs at least one StatusEntry")
        super().__init__(model)
        self.model: SchellingModel = model
        # Position is the cell coordinate. Mesa's unique_id is the agent id.
        self.statuses: list[StatusEntry] = list(statuses)
        self.cell = cell

    @property
    def id(self) -> int:
        """Agent id. Mesa assigns unique_id, starting at 1."""
        return self.unique_id

    @property
    def position(self) -> tuple[int, ...]:
        """Grid coordinate (x, y)."""
        return self.cell.coordinate

    def fronterization_on(self, criterion: str):
        """Return this agent's Fronterization for `criterion`.

        Raises:
            KeyError: The agent has no entry with that criterion.
        """
        for entry in self.statuses:
            if entry.criterion == criterion:
                return entry.fronterization
        raise KeyError(criterion)

    def occupied_neighbors(self) -> list[SchellingAgent]:
        """Agents in the Moore neighborhood.

        Empty cells are omitted. They do not enter the similarity ratio.
        """
        return list(self.cell.neighborhood.agents)

    def local_similarity(self, entry: StatusEntry) -> float | None:
        """Fraction of occupied neighbors with the same Fronterization.

        Similarity is an exact match on `entry.criterion`. Empty cells are
        ignored. The ratio is undefined when the agent has no occupied
        neighbors, and this returns None. Receptivity treats None as
        satisfied rather than as a breach.
        """
        neighbors = self.occupied_neighbors()
        if not neighbors:
            return None
        matches = 0
        for neighbor in neighbors:
            try:
                other = neighbor.fronterization_on(entry.criterion)
            except KeyError:
                continue
            if other == entry.fronterization:
                matches += 1
        return matches / len(neighbors)

    def similarity_ratios(self) -> list[float]:
        """Defined local-similarity ratios, one per status entry with neighbors."""
        ratios: list[float] = []
        for entry in self.statuses:
            ratio = self.local_similarity(entry)
            if ratio is not None:
                ratios.append(ratio)
        return ratios

    def receptivity(self) -> bool:
        """Return True when any status entry is below its Permeability.

        Receptivity is the check, not the move. It fires when
        local similarity < permeability for any StatusEntry. Entries with
        an undefined ratio (no occupied neighbors) do not fire.
        """
        for entry in self.statuses:
            ratio = self.local_similarity(entry)
            if ratio is not None and ratio < entry.permeability:
                return True
        return False

    def proceptivity(self) -> bool:
        """Move to a random empty cell if Receptivity reports a breach.

        Returns True when the agent moved. The agent stays when it is
        satisfied, or when the grid has no empty cell.
        """
        if not self.receptivity():
            return False
        destination = self.model.random_empty_cell()
        if destination is None:
            return False
        self.cell = destination
        return True

    def activate(self) -> None:
        """One random-sequential turn: Receptivity, then Proceptivity."""
        if self.proceptivity():
            self.model.moves += 1

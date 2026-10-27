# AGENTS.md — Schelling Operational Status v0.2

Instructions for AI coding agents working in `schelling-v0.2/`.

## Project purpose

This folder is the v0.2 Schelling model for Computational Systemics: two
fixed binary criteria, each with its own Permeability. The behavior is
defined in `docs/schelling-operational-status-spec.md`. That spec is the
primary coding reference. Implement it. Do not widen it.

Computational Systemics is generative agent-based modeling grounded in
Conciliatorics. The operators in this model are Fronterization, Permeability,
Receptivity, and Proceptivity. The framework documents are in `docs/`:

- `docs/computational-systemics-summary.md` — why these models exist.
- `docs/conciliatorics.md` — the treatise. Open it when an operator needs its original definition.
- `docs/visualization-guidelines.md` — shared dashboard look. v0.1 is the reference. This version's spec adds the mark channel and the second chart series.

`../schelling-v0.1/` is the implemented one-criterion model and the tree to
copy. Do not modify it. Do not import it. Copy the files the spec names and
change the copies in this folder.

## Current tree

The spec and these instructions are in place. The model, the CLI, and the
dashboard are not. Build them here, under the package name `schelling_status`.

When the tree exists, keep this shape:

- `schelling_status/` — `status.py` (`StatusEntry`), `agent.py` (`SchellingAgent`), `model.py` (`SchellingModel`).
- `run.py` — CLI step log. The step cap is enforced here, not inside `SchellingModel.step()`.
- `app.py` — Solara dashboard.
- `requirements.txt` — `mesa[viz]==3.5.1` and NetworkX.
- `setup.sh` — create `.venv`, install when needed, run `solara run app.py`.
- `docs/schelling-operational-status-spec.md` — this version's contract.
- `docs/computational-systemics-summary.md` — why these models exist.
- `docs/conciliatorics.md` — the treatise.
- `docs/visualization-guidelines.md` — shared dashboard look.

## Rules that carry over

- Grid with vacancies. Empty cells stay out of the similarity ratio. No occupied neighbors means the ratio is undefined and the agent is satisfied on that entry.
- Fronterization is the attribute value. Permeability is the threshold in `[0, 1]`.
- Receptivity fires when local similarity is strictly below permeability for any entry.
- Proceptivity moves the agent to a random empty cell when Receptivity fires, or leaves it in place when none exists.
- `SchellingModel.step()` zeroes the move count, calls `agents.shuffle_do("activate")`, and records the step. Do not rewrite that method to special-case the two criteria.
- The constructor is keyword-only. Passing both `width` and `grid_width`, or both `density` and `vacancy_rate`, raises.
- Both entries stay `mutable=False`. Values do not change during a run.

## Coding conventions

- Prefer Mesa (Python).
- This folder uses its own `.venv`. Before any Python command:

```bash
source .venv/bin/activate
```

- Install from `requirements.txt`. `pip install mesa` omits Solara, Matplotlib, and NetworkX, and `solara run app.py` will not start. Mesa 3.5 requires Python >= 3.12.
- Keep the Operational Status mapping explicit in the code and in `README.md`.
- Prefer clarity over premature optimization.
- The dashboard draws with Matplotlib through `SpaceRenderer`. `StatusSpaceRenderer` calls `setup_structure` and `setup_agents`. Controls live in `solara.Sidebar`. The main pane is `solara.Columns([13, 7])`: the grid, then the stats and chart. Do not move those components into `SolaraViz`. Its `GridDraggable` never mounts on this Solara build, because vue-grid-layout calls `window.Vue.use` and that function is absent. The stats panel is one HTML widget updated in place. `solara.Markdown` builds a new widget every step, the text vanishes for a frame, and the chart jumps.
- Play is Mesa's `ModelController` in the sidebar. The dashboard is local. Do not add a hosted Solara target.

## Workflow

1. Read `docs/schelling-operational-status-spec.md` and `docs/visualization-guidelines.md` before changing the model or the dashboard.
2. Copy the v0.1 tree as the spec's setup section describes. Change the copies.
3. Verify the model with `python run.py`, including the type-only regression against v0.1.
4. Verify the dashboard with `solara run app.py`. Confirm the grid, both marker shapes, the stats, and both chart series.
5. Ask before adding anything the spec lists as deferred.

## Out of scope unless the user asks

- Dynamic Fronterization, relevance weights, and Sub/Supra or Hypo/Hyper gradations.
- A satisfaction rule other than the independent per-entry check.
- A third criterion, continuous Fronterization, or a similarity window.
- YAML config and parameter sweeps.
- Full Conciliatorics machinery beyond Operational Status.
- Political or real-world case data.
- A public hosted dashboard.
- Edits to `schelling-v0.1`.

When in doubt, stay inside the spec and keep the Operational Status mapping visible in the code.

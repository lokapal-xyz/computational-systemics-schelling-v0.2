# Schelling Operational Status (v0.2)

A Mesa implementation of Schelling segregation with two fixed status entries on every agent. Each entry has its own Fronterization and its own Permeability. Receptivity fires when either entry is breached. Proceptivity moves the agent once, to a random empty cell.

The coding reference is `docs/schelling-operational-status-spec.md`. The framework documents are in `docs/` as well:

- `docs/computational-systemics-summary.md` — why these models exist.
- `docs/conciliatorics.md` — the treatise. The operators' original definitions.
- `docs/visualization-guidelines.md` — the shared dashboard look.

![Solara Start](./docs/solara-start.png)

## Quick start

From this folder, one command creates `.venv` if needed, installs dependencies when they are missing or outdated, and starts the dashboard:

```bash
chmod +x setup.sh   # only needed once
./setup.sh
```

Open the local URL the script prints. Stop the dashboard with Ctrl+C. `./setup.sh` runs in its own shell, so a later terminal activates the environment with `source .venv/bin/activate`.

The same steps by hand:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
solara run app.py
```

`requirements.txt` installs Mesa 3.5.1 with its visualization extra (Solara and Matplotlib) and NetworkX, which Mesa imports at startup. Mesa 3.5 needs Python 3.12. This folder has its own `.venv`. The v0.1 environment stays in `../schelling-v0.1/.venv`.

For a printed step log, use `python run.py`. See [Run](#run) for the flags and the columns.

## Repository layout

- `app.py` — interactive dashboard. Launch with `solara run app.py`.
- `run.py` — one simulation, printed step by step. The step cap is enforced here.
- `schelling_status/` — the model.
  - `status.py` — `StatusEntry` (fronterization and permeability).
  - `agent.py` — `SchellingAgent` (Receptivity and Proceptivity).
  - `model.py` — `SchellingModel` (grid, step, two segregation indexes, breach counts).
- `requirements.txt` — pinned Mesa visualization install and NetworkX.
- `setup.sh` — create `.venv`, install if needed, and start the dashboard.
- `docs/` — design documents.
  - `schelling-operational-status-spec.md` — v0.2 coding reference.
  - `computational-systemics-summary.md` — why these models exist.
  - `conciliatorics.md` — the treatise.
  - `visualization-guidelines.md` — the shared dashboard look.

## Operational Status mapping

| Term | In the code |
| --- | --- |
| Fronterization | `StatusEntry.fronterization`. The attribute value, `0` or `1`. Fixed for the run (`mutable=False`). |
| Permeability | `StatusEntry.permeability`. Fraction of similar neighbors that entry requires, in `[0, 1]`. `type` and `mark` each store their own. |
| Receptivity | `SchellingAgent.receptivity()`. Fires when local similarity is strictly below that entry's permeability for any status entry. |
| Proceptivity | `SchellingAgent.proceptivity()`. Moves the agent to one random empty cell when Receptivity fires. Stays if the grid has no empty cell. The breach counts record which entry fired. |

`SchellingAgent.statuses` is a list of two entries in the normal run (`type`, then `mark`). `--type-only` places the `type` entry alone. `SchellingModel.step()` sets the move count to 0, calls `agents.shuffle_do("activate")`, and records the grid. It does not special-case the two criteria.

Similarity on a criterion is an exact match of fronterization. Empty cells are left out of the ratio. An agent with no occupied neighbors has an undefined ratio on that entry and is satisfied on it.

`segregation_type` and `segregation_mark` are the means of the defined ratios on that criterion. Agents with no occupied neighbors are omitted from that mean. When no agent has a defined ratio, the index is `0.0`. Each criterion keeps its own index.

`dissatisfied` counts agents whose Receptivity fires. An agent breached on both entries counts once there, and also appears in `dissatisfied_both`. The breach columns overlap, so `dissatisfied` is `dissatisfied_type + dissatisfied_mark - dissatisfied_both`.

## Grid and schedule

- Non-toroidal Moore neighborhood (8 cells, fewer on the border).
- One agent per cell. Vacancy rate defaults to 0.15 on the CLI.
- Two criteria, `type` and `mark`. Each is split into equal groups of `0` and `1` unless a share is set. Value `0` receives the extra agent when the count is odd. The two shuffles are independent.
- Each step activates agents in random order. A move is visible to agents activated later in the same step.
- The run stops when no agent is dissatisfied. `run.py` also stops at the step cap. `step()` does not enforce the cap.

The constructor is keyword-only. Passing both `width` and `grid_width`, or both `density` and `vacancy_rate`, raises. A `permeability`, `n_types`, or `minority_fraction` argument raises. Name the criterion: `permeability_type`, `permeability_mark`, `type_share`, `mark_share`.

## Dashboard

```bash
source .venv/bin/activate
solara run app.py
```

The page is the shared Computational Systemics layout. The app bar title is **Computational Systemics — Schelling Operational Status**. The sidebar has Controls, Model Parameters, and Information. Play, pause, step, and reset are Mesa's `ModelController`. The play interval starts at 200 ms. The main pane is the grid, then the stats and the chart.

Color is `type`: cyan `#4FC3F7` for 0, amber `#FFB74D` for 1. Shape is `mark`: circle for 0, square for 1, at the same scatter area. A white edge means Receptivity is firing. The stats panel is one HTML widget updated in place. The chart plots `segregation_type` in cyan and `segregation_mark` in `#CE93D8`, with the legend kept. The footer reads `v0.2 prototype`.

Slider changes rebuild the model from the values Mesa's `ModelCreator` stores. Dashboard defaults are a 40×40 grid, density 0.75, both permeabilities 0.40, type B share 0.30, mark B share 0.50, and seed 42.

The dashboard runs on this machine and always includes mark.

## Run

From this folder, with this folder's virtual environment:

```bash
source .venv/bin/activate
python run.py
python run.py --permeability-type 0.5 --permeability-mark 0.4 --seed 1
python run.py --permeability-mark 0 --seed 1
python run.py --type-only --permeability 0.4 --seed 1
```

The default command is two criteria, equal groups, both thresholds 0.4, seed 1. Step 0 is the initial grid (`moves` is 0). Later rows are the grid after that sweep.

Two-criterion columns:

```text
step  dissatisfied  dissatisfied_type  dissatisfied_mark  dissatisfied_both  moves  segregation_type  segregation_mark
```

Ratios print to 4 decimals and counts as integers. The summary prints both permeabilities, both shares (or `equal`), the initial and final index on each criterion, final dissatisfied, total moves, and steps run.

`--type-only` places one `type` entry and prints the v0.1 columns (`dissatisfied`, `moves`, `segregation_index`). The threshold comes from `--permeability`. Combining `--type-only` with `--permeability-type`, `--permeability-mark`, or `--mark-share` raises. Passing `--permeability` without `--type-only` raises.

The same series is on the model after the run:

```python
model.datacollector.get_model_vars_dataframe()
model.fronterization_grid("type")  # rows are y, columns are x, None is empty
model.fronterization_grid("mark")
```

## Defaults

CLI defaults, from `python run.py`:

| Parameter | Default |
| --- | --- |
| grid width, height | 50, 50 |
| vacancy rate | 0.15 |
| permeability, type and mark | 0.4, 0.4 |
| type share, mark share | equal groups |
| steps | 150 |
| seed | 1 |

Dashboard defaults:

| Control | Default | Range |
| --- | --- | --- |
| Width, height | 40 | 20–60, step 1 |
| Density | 0.75 | 0.50–0.95, step 0.05 |
| Permeability (type) | 0.40 | 0.00–0.80, step 0.05 |
| Permeability (mark) | 0.40 | 0.00–0.80, step 0.05 |
| Type B share | 0.30 | 0.10–0.50, step 0.05 |
| Mark B share | 0.50 | 0.10–0.50, step 0.05 |
| Seed | 42 | text input |

## Checked runs

Seed 1, 50×50, vacancy 0.15, equal groups. `--type-only` matches a fresh v0.1 run, printed line for line, at permeability 0.3, 0.4, and 0.7. The initial index is 0.5066 in all three. Each stops with no dissatisfied agents.

| Permeability | Steps | Final segregation index | Total moves |
| --- | --- | --- | --- |
| 0.3 | 11 | 0.7436 | 816 |
| 0.4 | 14 | 0.8237 | 1,296 |
| 0.7 | 73 | 0.9940 | 10,725 |

The default two-criterion command, both thresholds 0.4, runs 27 steps and stops with no dissatisfied agents. `segregation_type` goes from 0.5066 to 0.8577. `segregation_mark` goes from 0.4974 to 0.8690. Total moves: 4,957. Fronterization on both entries is unchanged at the end.

`--permeability-mark 0` keeps `dissatisfied_mark` and `dissatisfied_both` at 0 on every row. The type index still rises, from 0.5066 to 0.8102, over 13 steps and 1,250 moves, and the run stops satisfied. The mark index moves from 0.4974 to 0.5001. Agents carry mark when they move for type, so an inactive criterion can drift.

Raising one permeability, with the other held fixed and the seed held at 1, raises that criterion's final index. Every run below reached satisfaction.

| Type | Mark | Steps | Final type | Final mark | Moves |
| --- | --- | --- | --- | --- | --- |
| 0.30 | 0.40 | 35 | 0.7767 | 0.8717 | 3,768 |
| 0.50 | 0.40 | 42 | 0.9213 | 0.8850 | 6,910 |
| 0.40 | 0.30 | 28 | 0.8503 | 0.7969 | 3,704 |
| 0.40 | 0.40 | 27 | 0.8577 | 0.8690 | 4,957 |
| 0.40 | 0.50 | 38 | 0.8785 | 0.9029 | 6,921 |

With the dashboard defaults (40×40, density 0.75, both permeabilities 0.40, type B share 0.30, mark B share 0.50, seed 42), the indexes go from 0.580 and 0.511 to 0.885 and 0.850. The run stops at step 40 with no dissatisfied agents and 3,144 moves.

## v0.2 scope

This version is the v0.1 model plus a second fixed binary criterion.

- Two entries, `type` and `mark`. Fronterization is `0` or `1` and does not change during a run.
- A Permeability of its own for each entry, chosen before the run.
- An independent share for each criterion. The default is equal groups.
- A segregation index and breach counts per criterion. Receptivity stays the any-entry check.
- A type-only CLI path that reproduces the v0.1 step log.
- A browser dashboard with color for `type`, shape for `mark`, both indexes, both breach lines, and two chart series.

## Deferred

Dynamic fronterization, relevance weights, Sub/Supra and Hypo/Hyper gradations, any satisfaction rule beyond the independent any-entry check, a third criterion, a correlation between `type` and `mark`, YAML config, parameter sweeps, and a hosted dashboard.

![Solara End](./docs/solara-end.png)

# Schelling Operational Status — Implementation Spec (v0.2)

**Purpose:** Coding reference for the two-criterion Schelling model.  
**Companions:** `computational-systemics-summary.md` (why these models exist) and `conciliatorics.md` (the treatise). Open the treatise only when an operator needs its original definition.  
**Source tree:** `../../schelling-v0.1/`. Copy it. Do not modify it and do not import it.  
**Status:** Specified. The model in this folder is not implemented yet.

## 1. Goal of v0.2

A grid-based agent model in which every agent carries two fixed status entries. Each entry has its own Fronterization and its own Permeability. Receptivity fires when either entry is breached. Proceptivity moves the agent once, to a random empty cell.

v0.2 answers a question v0.1 cannot. With two independently assigned binary attributes, does the grid settle on one criterion, on both, or keep moving because a gain on one entry breaks the other?

v0.1 remains the classic recovery: one binary criterion, one shared Permeability, fixed values. v0.2 is that model plus a second fixed criterion. It is not a new satisfaction rule, and it is not dynamic Fronterization.

## 2. What v0.2 adds

- A second `StatusEntry` on every agent: `criterion = "mark"`, Fronterization `0` or `1`, `mutable=False`.
- A Permeability of its own for `type` and for `mark`.
- An independent share for each criterion. The default is equal groups on both.
- A segregation index per criterion, plus separate breach counts.
- A dashboard that shows both values at once: color for `type`, marker shape for `mark`.
- A type-only CLI path that places one entry and reproduces the v0.1 step log.

The package name stays `schelling_status`. The step method stays a shuffle of `activate`.

## 3. Behavior carried over from v0.1

Keep these rules. They are already implemented in the v0.1 tree.

- Non-toroidal Moore neighborhood (8 cells, fewer on the border).
- One agent per cell. Empty cells are left out of the similarity ratio.
- Similarity on a criterion is an exact match of Fronterization.
- No occupied neighbors means the ratio is undefined. An undefined ratio does not fire Receptivity. The agent is satisfied on that entry.
- Agents activate in random order. A move is visible to agents activated later in the same step.
- Proceptivity moves to a random empty cell, or stays when the grid has no empty cell.
- The run stops when no agent is dissatisfied. `run.py` also stops at its step cap. `SchellingModel.step()` does not enforce the cap.
- The constructor is keyword-only. Passing both `width` and `grid_width`, or both `density` and `vacancy_rate`, raises.
- Step 0 is the initial grid. `moves` is 0. Later rows describe the grid after that sweep.

Every agent in the two-criterion model has both entries. The neighbor loop can keep treating a missing criterion as a non-match, but v0.2 does not rely on that path.

## 4. Agent schema

```text
Agent
├── id
├── position: (x, y)
└── statuses: list[StatusEntry]     # length 2 by default, length 1 on the type-only path

StatusEntry
├── criterion: "type" | "mark"
├── fronterization: 0 | 1
├── permeability: float              # in [0, 1], stored on the entry
└── mutable: False
```

Fronterization is the attribute value. Permeability is the fraction of similar occupied neighbors that entry requires. Receptivity fires for an entry when its ratio is defined and strictly below that entry's Permeability.

Do not update Fronterization during a run. The `mutable` flag stays `False` and the step loop does not read it.

## 5. Assignment and Permeability

Place agents as v0.1 does: choose the occupied cells, then assign values.

**Type.** When `type_share` is omitted, split the agents into values `0` and `1` as equally as the count allows, using the same remainder rule as v0.1 (`_balanced_values` with two types: value `0` receives the extra agent when the count is odd). When `type_share` is set, it is the fraction with Fronterization `1` on `type`. `round(n_agents * type_share)` agents get `1`. The rest get `0`. Shuffle the type list with the model RNG.

**Mark.** Same rule, with `mark_share`, and a separate shuffle. Skip mark assignment on the type-only path so that path consumes randomness in the same order as v0.1.

Zip the two lists onto the chosen cells. An agent's type and mark are independent given the two shares. There is no correlation parameter.

Draw type values first, then mark values. A two-criterion run therefore does not match a v0.1 grid cell for cell, even at the same seed. That is expected. The type-only path is the bit-level regression. The two-criterion run is a new experiment.

Each entry stores its own Permeability:

- `permeability_type` on the `type` entry.
- `permeability_mark` on the `mark` entry.

Both default to `0.4`. There is no single `permeability` argument on the two-criterion constructor. A name that sets both would hide which criterion moved.

A threshold of `0` never fires, because a ratio is never strictly below `0`. A threshold of `1` fires unless every occupied neighbor matches.

## 6. Receptivity and Proceptivity

For each entry, the local similarity ratio is:

```text
matching occupied neighbors / occupied neighbors
```

Empty cells do not appear in either count. The ratio is `None` when there are no occupied neighbors.

Receptivity returns true when any entry has a defined ratio strictly below its Permeability. This is the same any-entry check as v0.1. An agent breached on both entries is dissatisfied once.

Proceptivity, when Receptivity returns true, moves the agent to one random empty cell. The move is not labeled by which criterion fired. The breach counts carry that information. The agent stays when it is satisfied, or when no empty cell exists.

`activate` is still Receptivity, then Proceptivity. `step` is still: set the move count to 0, `agents.shuffle_do("activate")`, record the state.

## 7. Stopping

After each record, including the initial grid, `running` becomes false when the dissatisfied count is 0. Dissatisfied means Receptivity fires, the any-entry check.

`run.py` stops at `steps` (default 150) when agents are still dissatisfied. The dashboard plays until nobody is dissatisfied, with the same Mesa play controls as v0.1.

## 8. Parameters

CLI defaults match v0.1 where the parameter exists. Dashboard defaults match the v0.1 dashboard, plus the mark controls.

### Constructor

Keyword-only.

| Parameter | Default | Notes |
| --- | --- | --- |
| `grid_width` / `width` | 50 | One of the two names. Both raises. |
| `grid_height` / `height` | 50 | One of the two names. Both raises. |
| `vacancy_rate` | 0.15 | Fraction empty, in `[0, 1)`. |
| `density` | derived | Fraction occupied. Dashboard name. Both `density` and `vacancy_rate` raises. |
| `permeability_type` | 0.4 | Stored on the `type` entry. In `[0, 1]`. |
| `permeability_mark` | 0.4 | Stored on the `mark` entry. Ignored when `include_mark` is false. |
| `type_share` | `None` | Fraction with type Fronterization `1`. `None` means equal groups. |
| `mark_share` | `None` | Fraction with mark Fronterization `1`. `None` means equal groups. Ignored when `include_mark` is false. |
| `include_mark` | `True` | `False` is the type-only path: one entry, named `type`. |
| `steps` | 150 | Cap for the CLI. Not enforced inside `step`. |
| `seed` | `None` | `None` draws a seed. Integers and numeric strings are accepted, as in v0.1. |

`run.py` passes `seed=1`. The dashboard passes `seed=42`.

Reject a `permeability` argument. Reject `n_types` and `minority_fraction`. v0.2 is binary, and the share parameters replace the v0.1 minority fraction. `type_share` is that fraction for the `type` criterion.

### CLI

Default command, two criteria, equal groups, both thresholds 0.4:

```bash
python run.py
```

| Flag | Default |
| --- | --- |
| `--width`, `--height` | 50, 50 |
| `--vacancy-rate` | 0.15 |
| `--permeability-type` | 0.4 |
| `--permeability-mark` | 0.4 |
| `--type-share` | omitted, equal groups |
| `--mark-share` | omitted, equal groups |
| `--steps` | 150 |
| `--seed` | 1 |
| `--type-only` | off |

`--type-only` sets `include_mark=False` and reads the type threshold from `--permeability` (default 0.4), which is v0.1's flag name. Passing `--permeability-type`, `--permeability-mark`, or `--mark-share` together with `--type-only` raises. Passing `--permeability` without `--type-only` raises.

### Dashboard

Same page structure as v0.1. Defaults:

| Control | Default | Range |
| --- | --- | --- |
| Width, height | 40 | 20–60, step 1 |
| Density | 0.75 | 0.50–0.95, step 0.05 |
| Permeability (type) | 0.40 | 0.00–0.80, step 0.05 |
| Permeability (mark) | 0.40 | 0.00–0.80, step 0.05 |
| Type B share | 0.30 | 0.10–0.50, step 0.05 |
| Mark B share | 0.50 | 0.10–0.50, step 0.05 |
| Seed | 42 | text input |

Play interval default 200 ms. Slider changes rebuild the model through Mesa's `ModelCreator`. The dashboard always includes mark. It has no type-only switch.

Leave the CLI defaults alone when changing the dashboard, and the reverse.

## 9. Observables

Record these after the initial grid and after every step.

| Reporter | Definition |
| --- | --- |
| `dissatisfied` | Agents whose Receptivity fires. The any-entry count. |
| `dissatisfied_type` | Agents whose `type` ratio is defined and strictly below `permeability_type`. |
| `dissatisfied_mark` | Agents whose `mark` ratio is defined and strictly below `permeability_mark`. |
| `dissatisfied_both` | Agents counted in both breach columns. |
| `moves` | Agents who relocated during the sweep. 0 at step 0. |
| `segregation_type` | Mean of defined `type` ratios. Agents with no occupied neighbors are omitted. |
| `segregation_mark` | Mean of defined `mark` ratios, same rule. |

The breach columns overlap. `dissatisfied` is not the sum of the two breach counts. An agent in `dissatisfied_both` is still one dissatisfied agent.

Do not pool the two ratios into one headline index. v0.1's `mean_local_similarity` averages every defined ratio on the agent. With two entries that blend hides which criterion clustered. v0.2 does not report that pooled number.

When no agent has a defined ratio on a criterion, that criterion's index is `0.0`.

`fronterization_grid(criterion)` stays. Pass `"type"` or `"mark"`. Rows are `y`, columns are `x`, an empty cell is `None`.

### CLI table

Two-criterion columns, in this order:

```text
step  dissatisfied  dissatisfied_type  dissatisfied_mark  dissatisfied_both  moves  segregation_type  segregation_mark
```

Print ratios to 4 decimals and counts as integers. After the table, print both permeabilities, both shares (or `equal`), the initial and final index on each criterion, final dissatisfied, total moves, and steps run.

### Type-only table

Columns and summary labels match v0.1 so the logs can be compared directly:

```text
step  dissatisfied  moves  segregation_index
```

`segregation_index` is the `type` mean. The summary prints `permeability`, `initial segregation index`, `final segregation index`, `final dissatisfied`, `total moves`, and `steps run`, with the same labels `run.py` uses in v0.1.

## 10. Type-only regression

`--type-only` places a single `type` entry and does not draw mark values. Placement, the shuffle inside `step`, and the recorded series then follow the v0.1 random stream.

Check it against a fresh run in `schelling-v0.1`, same flags:

```bash
# from schelling-v0.1, with that folder's .venv
python run.py --permeability 0.4 --seed 1

# from schelling-v0.2, with this folder's .venv
python run.py --type-only --permeability 0.4 --seed 1
```

The printed series match, including the initial row. Repeat for permeability `0.3` and `0.7`. A note from the v0.1 build recorded, for seed 1 on a 50×50 grid with vacancy 0.15 and equal groups: initial index 0.507, and final results of 11 steps / 0.744 / 816 moves at permeability 0.3, 14 steps / 0.824 / 1296 moves at 0.4, and 73 steps / 0.994 / 10725 moves at 0.7. Those figures are rounded. The fresh v0.1 log is the target if it and the note disagree.

Use this folder's `.venv` for v0.2 and v0.1's `.venv` for v0.1. Do not point the two projects at one environment.

## 11. The mark-threshold control

`--permeability-mark 0` keeps the mark entry and never lets it fire. Expect `dissatisfied_mark` and `dissatisfied_both` to be 0 on every row.

`segregation_mark` may still change. Agents move because of `type` and carry `mark` with them, so the spatial mix of an inactive criterion can drift. That drift is a result. Do not treat a changing mark index as a bug when the mark threshold is 0.

This control does not reproduce the v0.1 series. Mark assignment consumes extra random draws. Use section 10 for the bit-level check. Use this section to confirm that an inactive criterion contributes no breaches while the active criterion still clusters.

At permeability 0.4 on `type`, the type index should rise from its initial value and the run should reach a state with no dissatisfied agents, or hit the step cap while still climbing. Record the series. Do not tune the model to hit a chosen final number.

## 12. Dashboard

Follow `visualization-guidelines.md` for the page, the palette, the channels, and the Solara constraints. The captures there are the v0.1 dashboard. v0.2 keeps that page. This section is only what v0.2 adds.

Footer line: `v0.2 prototype`.

### Grid encoding

Color is `type`. Shape is `mark`. The v0.1 cyan/amber reading stays intact, and the second criterion gets its own channel.

| Fronterization | Visual |
| --- | --- |
| `type` 0 | Fill `#4FC3F7` (cyan) |
| `type` 1 | Fill `#FFB74D` (amber) |
| `mark` 0 | Marker `"o"` (circle) |
| `mark` 1 | Marker `"s"` (square) |
| Receptivity firing | White edge `#F5F5F5`, linewidth about 1.4 |
| Satisfied | Faint edge `#2A2A2A`, linewidth about 0.4 |

Use the same scatter area for circles and squares, sized from the grid span the way v0.1 sizes the circle. Both shapes must read on a 40×40 grid at stream scale.

Legend, in the stats panel:

```text
Cyan fill    = type A (0)
Amber fill   = type B (1)
Circle       = mark A (0)
Square       = mark B (1)
White edge   = currently dissatisfied
```

### Stats

Show, on every step:

- Step
- Segregation on `type`, 3 decimals
- Segregation on `mark`, 3 decimals
- Dissatisfied agents, count and percent of occupied cells
- Dissatisfied on `type`, on `mark`, and on both
- Total moves (cumulative)
- Both permeabilities
- `Running…` or `Stopped: all agents satisfied`

### Chart

Two series, via `make_plot_component`, using the reporter names:

- `segregation_type` in `#4FC3F7`
- `segregation_mark` in `#CE93D8`

Keep the legend, with those two names. Title: **Segregation by criterion**. Y-axis from a floor at or below the lower series up to 1. Include 0.4 in the floor calculation the way v0.1 does, so a flat early series does not zoom into a thin band, and a series that starts under 0.4 is still visible. X-axis includes step 0 without collapsing the scale.

The v0.1 chart styling deletes the legend because it has one series. The v0.2 styling keeps it.

## 13. Repository setup

Copy from `schelling-v0.1` into this folder:

- `schelling_status/` (the package, not its `__pycache__`)
- `run.py`
- `app.py`
- `requirements.txt`
- `setup.sh`
- `.gitignore`

Leave behind: `.venv`, `__pycache__`, `.git`, `docs/`, `temp/`, `AGENTS.md`, `README.md`. This folder already has its own `AGENTS.md`, `README.md`, and spec.

Create a new `.venv` here. Install from this folder's `requirements.txt`.

After the model runs, rewrite `README.md` in the style of v0.1: quick start, layout, the Operational Status table, CLI and dashboard defaults, and the v0.2 scope. Point the framework documents at the copies in this folder: `computational-systemics-summary.md`, `conciliatorics.md`, and `visualization-guidelines.md`.

Do not initialize a remote unless the user asks.

## 14. Success criteria

- The type-only CLI matches v0.1's printed series for seed 1 at permeability 0.3, 0.4, and 0.7 (section 10).
- The default two-criterion CLI finishes, prints both indexes and the breach columns, and stops when nobody is dissatisfied or at the step cap.
- With `--permeability-mark 0`, mark breaches stay 0 and the type index still moves in the clustering direction (section 11).
- Raising one criterion's Permeability, with the other held fixed and the seed held fixed, raises that criterion's final segregation index on runs that reach satisfaction. Record the compared series in the README or in a short note under `temp/`. `temp/` is gitignored.
- Both Fronterization values are unchanged at the end of a run.
- `step` still only shuffles `activate`.
- The dashboard shows cyan and amber, circles and squares, a white edge on dissatisfied agents, both indexes, both breach lines, and two chart series. Sliders rebuild the model. Play advances the grid.
- Keyword-only construction. Conflicting size or density aliases raise. A stray `permeability` argument raises.

## 15. Implementation order

1. Read this spec, `visualization-guidelines.md`, and the v0.1 modules this spec names: `status.py`, `agent.py`, `model.py`, `run.py`, `app.py`.
2. Copy the tree (section 13) and create `.venv`.
3. Place two entries. Keep the type-only path on the same random stream as v0.1.
4. Replace the pooled segregation index with the two reporters and the breach counts.
5. Extend `run.py`. Confirm section 10, then section 11.
6. Extend the dashboard encoding, the stats widget, and the chart, on the shared page from the visualization guidelines. Confirm them in the browser.
7. Rewrite `README.md` from the run that just happened.

## 16. Deferred

Leave these out of v0.2.

- Dynamic Fronterization. Values stay fixed. The income-style case, where a changed value trips an unchanged Permeability, is a later version.
- Relevance weights.
- Sub/Supra and Hypo/Hyper gradations.
- Any combination rule beyond the independent any-entry check. That includes requiring both entries to breach, a weighted sum of ratios, and a single blended threshold.
- A third criterion, more than two Fronterization values, and continuous similarity windows.
- A correlation parameter between `type` and `mark`.
- YAML config and parameter sweeps.
- A hosted dashboard.

---

*This spec is the coding reference for v0.2. The shared dashboard look is `visualization-guidelines.md`. The v0.1 spec and the v0.1 visualization spec remain the references for `schelling-v0.1`.*

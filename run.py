"""Run one Schelling Operational Status simulation and print the step log."""

from __future__ import annotations

import argparse

from schelling_status import SchellingModel


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the v0.2 Schelling Operational Status model."
    )
    parser.add_argument("--width", type=int, default=50, help="Grid width (default 50).")
    parser.add_argument("--height", type=int, default=50, help="Grid height (default 50).")
    parser.add_argument(
        "--vacancy-rate",
        type=float,
        default=0.15,
        help="Fraction of empty cells (default 0.15).",
    )
    parser.add_argument(
        "--permeability-type",
        type=float,
        default=None,
        help="Type threshold in [0, 1] (default 0.4). Not valid with --type-only.",
    )
    parser.add_argument(
        "--permeability-mark",
        type=float,
        default=None,
        help="Mark threshold in [0, 1] (default 0.4). Not valid with --type-only.",
    )
    parser.add_argument(
        "--type-share",
        type=float,
        default=None,
        help="Fraction with type Fronterization 1. Omit for equal groups.",
    )
    parser.add_argument(
        "--mark-share",
        type=float,
        default=None,
        help="Fraction with mark Fronterization 1. Omit for equal groups. Not valid with --type-only.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=150,
        help="Maximum steps (default 150). Stops sooner if nobody is dissatisfied.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1,
        help="RNG seed (default 1).",
    )
    parser.add_argument(
        "--type-only",
        action="store_true",
        help="One type entry, v0.1 columns. Reads the threshold from --permeability.",
    )
    parser.add_argument(
        "--permeability",
        type=float,
        default=None,
        help="Type threshold for --type-only, in [0, 1] (default 0.4). Requires --type-only.",
    )
    args = parser.parse_args()

    if args.type_only:
        if (
            args.permeability_type is not None
            or args.permeability_mark is not None
            or args.mark_share is not None
        ):
            parser.error(
                "--type-only cannot be combined with --permeability-type, "
                "--permeability-mark, or --mark-share"
            )
        permeability_type = 0.4 if args.permeability is None else args.permeability
        model = SchellingModel(
            grid_width=args.width,
            grid_height=args.height,
            vacancy_rate=args.vacancy_rate,
            permeability_type=permeability_type,
            type_share=args.type_share,
            include_mark=False,
            steps=args.steps,
            seed=args.seed,
        )
    else:
        if args.permeability is not None:
            parser.error("--permeability is only valid with --type-only")
        permeability_type = (
            0.4 if args.permeability_type is None else args.permeability_type
        )
        permeability_mark = (
            0.4 if args.permeability_mark is None else args.permeability_mark
        )
        model = SchellingModel(
            grid_width=args.width,
            grid_height=args.height,
            vacancy_rate=args.vacancy_rate,
            permeability_type=permeability_type,
            permeability_mark=permeability_mark,
            type_share=args.type_share,
            mark_share=args.mark_share,
            steps=args.steps,
            seed=args.seed,
        )

    while model.running and model.steps < model.max_steps:
        model.step()

    frame = model.datacollector.get_model_vars_dataframe()
    frame.index.name = "step"
    if args.type_only:
        print(
            frame.to_string(
                formatters={
                    "dissatisfied": "{:.0f}".format,
                    "moves": "{:.0f}".format,
                    "segregation_index": "{:.4f}".format,
                }
            )
        )
    else:
        print(
            frame.to_string(
                formatters={
                    "dissatisfied": "{:.0f}".format,
                    "dissatisfied_type": "{:.0f}".format,
                    "dissatisfied_mark": "{:.0f}".format,
                    "dissatisfied_both": "{:.0f}".format,
                    "moves": "{:.0f}".format,
                    "segregation_type": "{:.4f}".format,
                    "segregation_mark": "{:.4f}".format,
                }
            )
        )
    print()
    initial = frame.iloc[0]
    final = frame.iloc[-1]
    if args.type_only:
        print(f"permeability:              {model.permeability_type:.2f}")
        print(f"initial segregation index: {initial['segregation_index']:.4f}")
        print(f"final segregation index:   {final['segregation_index']:.4f}")
    else:
        print(f"permeability_type:         {model.permeability_type:.2f}")
        print(f"permeability_mark:         {model.permeability_mark:.2f}")
        print(f"type_share:                {_share_label(model.type_share)}")
        print(f"mark_share:                {_share_label(model.mark_share)}")
        print(f"initial segregation_type:  {initial['segregation_type']:.4f}")
        print(f"final segregation_type:    {final['segregation_type']:.4f}")
        print(f"initial segregation_mark:  {initial['segregation_mark']:.4f}")
        print(f"final segregation_mark:    {final['segregation_mark']:.4f}")
    print(f"final dissatisfied:        {int(final['dissatisfied'])}")
    print(f"total moves:               {int(frame['moves'].sum())}")
    print(f"steps run:                 {len(frame) - 1}")
    if not model.running:
        print("stopped: no dissatisfied agents")
    else:
        print("stopped: reached max steps")


def _share_label(share: float | None) -> str:
    if share is None:
        return "equal"
    return f"{share:.2f}"


if __name__ == "__main__":
    main()

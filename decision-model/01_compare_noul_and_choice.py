"""Compare Noul and Choice on four identical states and record raw responses."""

import json
from pathlib import Path

from typesafe_sdk import Choice, Noul, TypeSafeClient

TYPESAFE_BASE_URL = "http://localhost:11434"
TYPESAFE_API_KEY = "ollama"
TYPESAFE_DEFAULT_MODEL = "nimble"

INSTRUCTIONS = (
    "Based only on the supplied forecast, will it rain on the specified date? "
    "Do not invent weather data or infer weather from location or date alone."
)
BASE_STATE = {"location": "Berlin", "date": "2026-10-06"}
EXPERIMENTS = [
    ("A", "No evidence", "insufficient evidence", dict(BASE_STATE)),
    ("B", "Rain evidence", "strong YES", {
        **BASE_STATE, "summary": "Heavy rain expected throughout the day",
    }),
    ("C", "Dry evidence", "strong NO", {
        **BASE_STATE, "summary": "Clear skies and dry conditions expected",
    }),
    ("D", "Conflicting evidence", "uncertain/conflicted", {
        **BASE_STATE,
        "summary": "Heavy rain expected throughout the day",
        "additional_forecast": "Dry conditions with no precipitation expected",
    }),
]


def try_noul(client: TypeSafeClient, forecast: dict[str, str]):
    return client.system_one(
        state=forecast,
        questions={"might_rain": Noul(
            instructions=INSTRUCTIONS,
            criteria={
                "true": "The forecast indicates rain is expected.",
                "false": "The forecast indicates no rain is expected.",
            },
        )},
    )


def try_choice(client: TypeSafeClient, forecast: dict[str, str]):
    return client.system_one(
        state=forecast,
        questions={"might_rain": Choice(
            instructions=INSTRUCTIONS,
            criteria={
                "YES": "The forecast indicates rain is expected.",
                "NO": "The forecast indicates no rain is expected.",
                "UNKNOWN": (
                    "There is insufficient weather evidence, or the forecasts "
                    "conflict without a basis for resolving them."
                ),
            },
        )},
    )


def main() -> None:
    results = []
    output_dir = Path(__file__).resolve().parent
    json_path = output_dir / "01_experiment_results.json"

    def save_results() -> None:
        # Save after every response so completed calls survive a later failure.
        json_path.write_text(json.dumps({
            "requested_model": TYPESAFE_DEFAULT_MODEL,
            "instructions": INSTRUCTIONS,
            "results": results,
        }, indent=2) + "\n", encoding="utf-8")

    with TypeSafeClient(
        base_url=TYPESAFE_BASE_URL,
        api_key=TYPESAFE_API_KEY,
        model=TYPESAFE_DEFAULT_MODEL,
        timeout=120,
    ) as client:
        # All Noul calls first, followed by Choice on exactly the same states.
        for experiment, label, expectation, forecast in EXPERIMENTS:
            print(f"Running Noul {experiment}: {label}", flush=True)
            response = try_noul(client, forecast)
            value = response.nouls["might_rain"].noul
            print(f"Exact Noul YES value: {value!r}", flush=True)
            results.append({
                "experiment": experiment,
                "state_label": label,
                "expected_conceptually": expectation,
                "state": forecast,
                "noul_yes": value,
                "noul_response": response.model_dump(mode="json"),
            })
            save_results()

        for result in results:
            print(f"Running Choice {result['experiment']}: {result['state_label']}", flush=True)
            response = try_choice(client, result["state"])
            answer = response.choices["might_rain"]
            result["choice"] = answer.choice
            result["choice_probabilities"] = answer.probabilities
            result["choice_response"] = response.model_dump(mode="json")
            save_results()

    table = [
        "| State | Noul YES | Choice YES | Choice NO | Choice UNKNOWN |",
        "|---|---|---|---|---|",
    ]
    for result in results:
        probabilities = result["choice_probabilities"]
        cells = [result["state_label"], f"{result['noul_yes']:.2%}"]
        cells.extend(f"{probabilities[key]:.2%}" for key in ("YES", "NO", "UNKNOWN"))
        table.append("| " + " | ".join(cells) + " |")

    table_path = output_dir / "01_experiment_results.md"
    table_path.write_text("\n".join(table) + "\n", encoding="utf-8")
    print("\n" + "\n".join(table))
    print(f"\nRaw responses saved to {json_path}")
    print(f"Table saved to {table_path}")


if __name__ == "__main__":
    main()

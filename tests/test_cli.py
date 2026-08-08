import json

from eazydatafix.cli import main


def test_cli_runs_multiple_inputs_with_json_config_and_structured_logs(tmp_path) -> None:
    """CLI processes ordered inputs and writes machine-readable outputs and logs."""
    first = tmp_path / "a.csv"
    second = tmp_path / "b.csv"
    first.write_text("value\n1\n", encoding="utf-8")
    second.write_text("value\n2\n", encoding="utf-8")
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps({"workflow": "profile", "inputs": [str(second)]}), encoding="utf-8"
    )
    output = tmp_path / "output.json"
    logs = tmp_path / "logs.jsonl"

    assert (
        main(
            [str(first), "--config", str(config), "--output", str(output), "--log-file", str(logs)]
        )
        == 0
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    assert [record["dataset"] for record in report["records"]] == [str(first), str(second)]
    assert report["passed"] is True
    assert len(logs.read_text(encoding="utf-8").splitlines()) == 4


def test_cli_returns_configuration_exit_code_for_invalid_inputs() -> None:
    """CLI uses exit code 2 for deterministic configuration errors."""
    assert main([]) == 2


import json

from failure_risk.pipeline import generate_dataset
from failure_risk.validation_report import create_validation_report


def test_validation_report_passes_for_valid_dataset(tmp_path):
    data = generate_dataset(days=1, seed=12345)
    output_path = tmp_path / "reports" / "validation_report.json"

    report = create_validation_report(data, str(output_path))

    assert report["status"] == "passed"
    assert report["error_count"] == 0
    assert len(report["tables_checked"]) == 10
    assert output_path.exists()

    saved_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved_report["status"] == "passed"


def test_validation_report_records_errors(tmp_path):
    data = generate_dataset(days=1, seed=12345)
    data["machines"].loc[0, "line_id"] = "INVALID-LINE"

    output_path = tmp_path / "reports" / "validation_report.json"
    report = create_validation_report(data, str(output_path))

    assert report["status"] == "failed"
    assert report["error_count"] > 0
    assert report["errors"]

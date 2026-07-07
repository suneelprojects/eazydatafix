from pathlib import Path

import easydatafix as edf


def test_report_exporters(
    data_dir,
    tmp_path: Path,
) -> None:

    report = edf.assess(
        data_dir / "report.csv",
    )

    json_file = tmp_path / "report.json"
    html_file = tmp_path / "report.html"
    markdown_file = tmp_path / "report.md"
    csv_file = tmp_path / "report.csv"
    excel_file = tmp_path / "report.xlsx"
    pdf_file = tmp_path / "report.pdf"

    report.to_json(json_file)
    report.to_html(html_file)
    report.to_markdown(markdown_file)
    report.to_csv(csv_file)
    report.to_excel(excel_file)
    report.to_pdf(pdf_file)

    assert json_file.exists()
    assert html_file.exists()
    assert markdown_file.exists()
    assert csv_file.exists()
    assert excel_file.exists()
    assert pdf_file.exists()

    assert json_file.stat().st_size > 0
    assert html_file.stat().st_size > 0
    assert markdown_file.stat().st_size > 0
    assert csv_file.stat().st_size > 0
    assert excel_file.stat().st_size > 0
    assert pdf_file.stat().st_size > 0

from easydatafix.assessment.engine import AssessmentEngine


def test_assessment_engine(data_dir) -> None:

    engine = AssessmentEngine()

    report = engine.assess(
        data_dir / "assessment.csv",
    )

    assert report.dataset_info.rows == 3
    assert report.dataset_info.columns == 4

    assert report.quality.score >= 0
    assert report.quality.grade is not None

    assert report.completeness.completeness_score == 100
    assert report.uniqueness.uniqueness_score == 100

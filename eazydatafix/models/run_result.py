from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eazydatafix.models.assessment_report import AssessmentReport
    from eazydatafix.models.dataset_profile import DatasetProfile
    from eazydatafix.models.eda_result import EDAResult
    from eazydatafix.models.fix_result import FixResult


@dataclass(frozen=True, slots=True)
class RunResult:
    """Contains the deterministic profile, assessment, fix, and EDA workflow results."""

    profile: DatasetProfile
    assessment: AssessmentReport
    fix_result: FixResult
    eda_result: EDAResult

import pandas as pd

from eazydatafix.assessment.checks.validity.aadhaar_check import AadhaarCheck
from eazydatafix.assessment.checks._runner import run_checks
from eazydatafix.assessment.checks.validity.credit_card_check import CreditCardCheck
from eazydatafix.assessment.checks.validity.date_check import DateCheck
from eazydatafix.assessment.checks.validity.email_check import EmailCheck
from eazydatafix.assessment.checks.validity.gstin_check import GstinCheck
from eazydatafix.assessment.checks.validity.ip_address_check import IpAddressCheck
from eazydatafix.assessment.checks.validity.pan_check import PanCheck
from eazydatafix.assessment.checks.validity.phone_check import PhoneCheck
from eazydatafix.assessment.checks.validity.pincode_check import PincodeCheck
from eazydatafix.assessment.checks.validity.url_check import UrlCheck
from eazydatafix.models.validation_result import ValidationResult


class ValidityEngine:
    """
    Runs all validity checks.
    """

    def __init__(self) -> None:

        self._checks = [
            EmailCheck(),
            PhoneCheck(),
            DateCheck(),
            UrlCheck(),
            IpAddressCheck(),
            CreditCardCheck(),
            PincodeCheck(),
            AadhaarCheck(),
            PanCheck(),
            GstinCheck(),
        ]

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:
        return run_checks(
            self._checks,
            df,
        )

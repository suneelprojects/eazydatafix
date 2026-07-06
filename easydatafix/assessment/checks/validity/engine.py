import pandas as pd

from easydatafix.assessment.checks.validity.aadhaar_check import AadhaarCheck
from easydatafix.assessment.checks.validity.credit_card_check import CreditCardCheck
from easydatafix.assessment.checks.validity.date_check import DateCheck
from easydatafix.assessment.checks.validity.email_check import EmailCheck
from easydatafix.assessment.checks.validity.gstin_check import GstinCheck
from easydatafix.assessment.checks.validity.ip_address_check import IpAddressCheck
from easydatafix.assessment.checks.validity.pan_check import PanCheck
from easydatafix.assessment.checks.validity.phone_check import PhoneCheck
from easydatafix.assessment.checks.validity.pincode_check import PincodeCheck
from easydatafix.assessment.checks.validity.url_check import UrlCheck
from easydatafix.models.validation_result import ValidationResult


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

        results: list[ValidationResult] = []

        for check in self._checks:
            results.extend(
                check.evaluate(df)
            )

        return results

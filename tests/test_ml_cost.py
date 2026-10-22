"""Budget arithmetic and uncertainty must work without Modal/network dependencies."""
import copy
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ml_cost", ROOT / "scripts/ml_cost.py")
cost = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cost)


class CostTest(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "templates/ml/cost.example.json").read_text())

    def test_unknown_costs_remain_unknown_and_never_authorize_launch(self):
        result = cost.estimate(self.config)
        self.assertEqual(result["unknown_extras"], ["egress", "storage"])
        self.assertIsNone(result["reserve_usd"])
        self.assertIsNone(result["within_budget"])
        self.assertIsNone(result["scenarios"]["high"]["total_usd"])
        self.assertEqual(Decimal(result["scenarios"]["high"]["compute_usd"]), Decimal("1.8648"))
        self.assertFalse(result["launch_authorized"])

    def test_all_attempts_resources_extras_and_contingency_are_charged(self):
        self.config["extras_usd"] = {"evaluation": "1", "storage": "0.2", "egress": "0"}
        result = cost.estimate(self.config)
        self.assertEqual(Decimal(result["compute_rate_usd_per_second"]), Decimal("0.001036"))
        self.assertEqual(Decimal(result["reserve_usd"]), Decimal("3.67776"))
        self.assertTrue(result["within_budget"])
        self.config["budget_usd"] = "3.67775"
        self.assertFalse(cost.estimate(self.config)["within_budget"])
        self.config["budget_usd"] = "3.67776"
        self.assertTrue(cost.estimate(self.config)["within_budget"])

    def test_no_gpu_is_supported_and_rates_are_not_hardcoded(self):
        self.config["gpu_count"] = 0
        self.assertEqual(Decimal(cost.estimate(self.config)["compute_rate_usd_per_second"]), Decimal("0.000036"))
        self.config["product"] = "sandbox"
        self.config["rates_per_second"]["cpu_core"] = "0.00003"
        self.assertEqual(Decimal(cost.estimate(self.config)["compute_rate_usd_per_second"]), Decimal("0.000076"))

    def test_invalid_numbers_are_rejected(self):
        for value in [True, None, -1, "-1", "NaN", "Infinity", float("inf"), {}, "1e9"]:
            with self.subTest(value=value):
                config = copy.deepcopy(self.config)
                config["billed_memory_gib"] = value
                with self.assertRaises(ValueError):
                    cost.estimate(config)
        for value in [True, 1.1, 0, -1, "2"]:
            with self.subTest(attempts=value):
                config = copy.deepcopy(self.config)
                config["scenarios"]["high"]["attempts"] = value
                with self.assertRaises(ValueError):
                    cost.estimate(config)

    def test_missing_or_misnamed_units_and_reversed_scenarios_fail(self):
        for key in ["extras_usd", "rate_as_of", "rates_per_second", "budget_usd"]:
            config = copy.deepcopy(self.config)
            del config[key]
            with self.assertRaises(ValueError):
                cost.estimate(config)
        self.config["scenarios"]["low"]["seconds_per_attempt"] = "100000"
        with self.assertRaises(ValueError):
            cost.estimate(self.config)

    def test_currency_and_date_and_unrecognized_fields_fail(self):
        for key, value in [("currency", "EUR"), ("rate_as_of", "yesterday"),
                           ("product", "unknown"), ("schema_version", True),
                           ("contingency_fraction", "1.1"), ("unexpected", 1)]:
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                cost.estimate(config)

    def test_duplicate_json_keys_fail(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            json.loads('{"budget_usd": "1", "budget_usd": "100"}', object_pairs_hook=cost.unique_object)

    def test_real_cli_example_is_explicitly_incomplete(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/ml_cost.py"),
                                 str(ROOT / "templates/ml/cost.example.json")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNone(json.loads(result.stdout)["within_budget"])


if __name__ == "__main__":
    unittest.main()

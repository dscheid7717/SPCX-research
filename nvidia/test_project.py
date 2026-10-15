"""Project 1 validation suite -- NVIDIA (NVDA).

Run from the nvidia folder:   python -m unittest test_project -v

Each test names the claim it protects. The directional changed-input tests in
DirectionalChangedInputTests were written and committed BEFORE analysis.py was first
executed; the commit that added this file is the evidence (see docs/validation-and-ai-use.md).
"""

import importlib.util
import io
import json
import pathlib
import contextlib
import unittest

import analysis
import dcf as dcf_engine

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent


def _load_root_module(name):
    """Load a root-level training module without colliding with nvidia/ names."""
    spec = importlib.util.spec_from_file_location(f"root_{name}", ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class KnownAnswerTests(unittest.TestCase):
    """The engines reproduce the course's published training answers."""

    def test_dcf_training_case_value_per_share(self):
        result = dcf_engine.run_dcf(**dcf_engine.TRAINING_INPUTS)
        self.assertAlmostEqual(result["value_per_share"],
                               dcf_engine.TRAINING_KNOWN_VALUE_PER_SHARE, delta=0.005)

    def test_dcf_training_case_grid(self):
        t = dcf_engine.TRAINING_INPUTS
        for (rate, g), expected in dcf_engine.TRAINING_KNOWN_GRID.items():
            got = dcf_engine.value_per_share_only(
                t["starting_fcff"], t["growth_rates"], rate, g,
                t["non_operating_cash"], t["debt"], t["diluted_shares"])
            self.assertAlmostEqual(got, expected, delta=0.005, msg=f"WACC {rate}, g {g}")

    def test_dcf_training_case_reverse_dcf(self):
        t = dcf_engine.TRAINING_INPUTS
        shift = dcf_engine.reverse_dcf_growth_shift(
            dcf_engine.TRAINING_TARGET_PRICE, t["starting_fcff"], t["growth_rates"],
            t["wacc"], t["terminal_growth"], t["non_operating_cash"], t["debt"],
            t["diluted_shares"], lower_bound=-0.05, upper_bound=0.10)
        self.assertAlmostEqual(shift * 100, dcf_engine.TRAINING_KNOWN_SHIFT_POINTS, delta=0.01)

    def test_asbury_proforma_training_case(self):
        """The root Lab 09 engine still prints the published $291.75."""
        module = _load_root_module("proforma")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            module.main()
        self.assertIn("291.75", buffer.getvalue())


class ArticulationTests(unittest.TestCase):
    """The three statements articulate, and the base year reconciles to the filing."""

    @classmethod
    def setUpClass(cls):
        cls.model_run = analysis.run_model()

    def _check(self, name):
        return next(c for c in self.model_run["checks"] if c["check"] == name)

    def test_model_is_valid(self):
        self.assertTrue(self.model_run["valid"], [c for c in self.model_run["checks"] if not c["passed"]])

    def test_base_year_reconciles(self):
        self.assertTrue(self._check("Base year reconciles to the 10-K")["passed"])
        self.assertTrue(self._check("Base revenue equals filed FY2026 revenue")["passed"])

    def test_balance_sheet_balances_every_year(self):
        for year in self.model_run["projection"]:
            self.assertAlmostEqual(year["balance_gap"], 0.0, delta=analysis.TOLERANCE,
                                   msg=year["label"])

    def test_cash_flow_ties_to_balance_sheet_cash(self):
        for row in self.model_run["cash_flows"]:
            self.assertAlmostEqual(row["tie_gap"], 0.0, delta=analysis.TOLERANCE,
                                   msg=row["label"])

    def test_fcff_reconciles_to_fcfe(self):
        self.assertTrue(self._check("FCFF reconciles to the pro-forma's FCFE")["passed"])

    def test_project_inputs_do_not_leak_into_lab10_engine(self):
        """After a run, proforma.py is back to its Lab 10 values (the lab record)."""
        import proforma
        self.assertEqual(proforma.REVENUE_GROWTH, [0.30, 0.22, 0.16, 0.11, 0.07])
        self.assertEqual(proforma.GROSS_MARGIN, [0.710, 0.705, 0.700, 0.695, 0.690])


class BridgeTests(unittest.TestCase):
    """Enterprise value to equity to per-share, both ways."""

    def test_bridge(self):
        run = analysis.run_model()
        v = run["valuation"]
        b = analysis.BRIDGE
        equity = (v["enterprise_value"] + b["cash_and_marketable_securities"]
                  + b["non_marketable_equity_securities"] - b["debt"])
        self.assertAlmostEqual(equity, v["equity_value"], delta=analysis.TOLERANCE)
        self.assertAlmostEqual(v["value_per_share"] * b["diluted_shares"], equity,
                               delta=analysis.TOLERANCE)
        self.assertAlmostEqual(v["pv_explicit"] + v["pv_terminal"], v["enterprise_value"],
                               delta=analysis.TOLERANCE)

    def test_bridge_inputs_match_the_filing(self):
        """Independent restatement of the bridge lines from the 10-K balance sheet."""
        b = analysis.BRIDGE
        self.assertEqual(b["cash_and_marketable_securities"], 10_605.0 + 51_951.0)
        self.assertEqual(b["debt"], 999.0 + 7_469.0)
        self.assertEqual(b["non_marketable_equity_securities"], 22_251.0)


class DirectionalChangedInputTests(unittest.TestCase):
    """Written before analysis.py was first executed. Each states the expected direction."""

    def setUp(self):
        self.base_value = analysis.value_per_share(analysis.base_inputs())

    def _value(self, **overrides):
        return analysis.value_per_share(
            analysis.apply_overrides(analysis.base_inputs(), overrides))

    def test_higher_beta_lowers_value(self):
        # Expected: beta 2.216 -> 2.516 raises Ke by 1.5pp, so value per share FALLS.
        self.assertLess(self._value(beta=2.516), self.base_value)

    def test_higher_fy2027_growth_raises_value(self):
        # Expected: +10pp on FY2027E growth only raises every later year's revenue base,
        # so value per share RISES.
        path = list(analysis.BASE_INPUTS["revenue_growth"])
        path[0] += 0.10
        self.assertGreater(self._value(revenue_growth=path), self.base_value)

    def test_lower_gross_margin_lowers_value(self):
        # Expected: -2pp margin every year lowers operating income, so value FALLS.
        margins = [m - 0.02 for m in analysis.BASE_INPUTS["gross_margin"]]
        self.assertLess(self._value(gross_margin=margins), self.base_value)

    def test_sbc_as_cash_cost_lowers_value(self):
        # Expected: removing the SBC add-back from FCFF lowers value.
        self.assertLess(self._value(sbc_as_cash_cost=True), self.base_value)

    def test_restore_base_recovers_base_value(self):
        self._value(beta=3.0)
        self.assertAlmostEqual(analysis.value_per_share(analysis.base_inputs()),
                               self.base_value, places=9)


class DcfBoundaryTests(unittest.TestCase):
    """Monotonicity over the WACC x growth grid and the Gordon boundary."""

    def test_grid_monotonic(self):
        self.assertTrue(analysis.grid_is_monotonic(analysis.sensitivity_grid()))

    def test_terminal_growth_at_or_above_wacc_refuses(self):
        inputs = analysis.base_inputs()
        inputs["terminal_growth"] = analysis.wacc(inputs) + 0.001
        run = analysis.run_model(inputs)
        self.assertFalse(run["valid"])
        self.assertIsNone(run["valuation"])

    def test_terminal_share_reported(self):
        share = analysis.run_model()["valuation"]["terminal_share_of_ev"]
        self.assertTrue(0.0 < share < 1.0)


class HighestRiskFailureTests(unittest.TestCase):
    """The failures that would silently produce a wrong value must fail loudly instead."""

    def test_dropped_sbc_equity_credit_refuses(self):
        inputs = analysis.base_inputs()
        inputs["inject_fault"] = "drop_sbc_equity_credit"
        run = analysis.run_model(inputs)
        self.assertFalse(run["valid"])
        self.assertIsNone(run["valuation"])
        first = run["projection"][0]
        self.assertAlmostEqual(abs(first["balance_gap"]), first["stock_compensation"],
                               delta=analysis.TOLERANCE)

    def test_opening_mapping_error_refuses(self):
        inputs = analysis.base_inputs()
        inputs["inject_fault"] = "opening_mapping_error"
        run = analysis.run_model(inputs)
        self.assertFalse(run["valid"])
        self.assertIsNone(run["valuation"])

    def test_fault_does_not_leak_into_next_run(self):
        inputs = analysis.base_inputs()
        inputs["inject_fault"] = "opening_mapping_error"
        analysis.run_model(inputs)
        self.assertTrue(analysis.run_model()["valid"])

    def test_unknown_input_name_refused(self):
        with self.assertRaises(KeyError):
            analysis.apply_overrides(analysis.base_inputs(), {"revenue_grwth": [0.1] * 5})


class PeerPolicyTests(unittest.TestCase):
    """One definition, one date, one window -- and a recomputation by hand."""

    def test_policy_checks_pass(self):
        for item in analysis.comparables()["checks"]:
            self.assertTrue(item["passed"], item)

    def test_nvda_ev_ebitda_by_hand(self):
        ev = 221.30 * 24_514 + 8_468 - 62_556
        ebitda = 130_387 + 2_843
        self.assertAlmostEqual(analysis.comparables()["rows"]["NVDA"]["ev_ebitda"],
                               ev / ebitda, places=9)


class ReproducibilityTests(unittest.TestCase):
    """The frozen visible output is what the engine produces now."""

    def test_frozen_output_matches_fresh_run(self):
        path = HERE / "visible_output.json"
        if not path.exists():
            self.skipTest("visible_output.json not frozen yet")
        frozen = json.loads(path.read_text(encoding="utf-8"))
        fresh = analysis.visible_output(analysis.run_analysis())
        self.assertEqual(frozen["valuation"], json.loads(json.dumps(fresh["valuation"])))
        self.assertEqual(frozen["recommendation"]["action"], fresh["recommendation"]["action"])


if __name__ == "__main__":
    unittest.main()

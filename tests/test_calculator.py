"""Pure rate-engine tests (Home Assistant is not required)."""

from datetime import UTC, datetime, timedelta
import importlib.util
from pathlib import Path
import sys
import types

ROOT = Path(__file__).parents[1]
PACKAGE_PATH = ROOT / "custom_components" / "duke_energy_cost"
PACKAGE = "custom_components.duke_energy_cost"

custom_components = types.ModuleType("custom_components")
custom_components.__path__ = []
sys.modules.setdefault("custom_components", custom_components)
package = types.ModuleType(PACKAGE)
package.__path__ = [str(PACKAGE_PATH)]
sys.modules.setdefault(PACKAGE, package)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        f"{PACKAGE}.{name}", PACKAGE_PATH / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


const = _load("const")
tariffs = _load("tariffs")
calculator = _load("calculator")


def _local_as_utc(year, month, day, hour):
    return datetime(year, month, day, hour, tzinfo=calculator.LOCAL_TZ).astimezone(UTC)


def _config(schedule):
    return {
        **tariffs.DEFAULTS[schedule],
        const.CONF_BILLING_CYCLE_DAY: 1,
        const.CONF_THREE_PHASE: False,
        const.CONF_ADDITIONAL_KWH_RATE: 0.0,
        const.CONF_MONTHLY_ADJUSTMENT: 0.0,
        const.CONF_TAX_PERCENT: 0.0,
        const.CONF_CPP_EVENTS: "",
        const.CONF_DEMAND_MODE: const.DEMAND_MODE_HOURLY,
    }


def test_shared_tou_periods_and_observed_holiday():
    events = {}
    assert tariffs.tou_period(
        datetime(2026, 7, 6, 18, tzinfo=calculator.LOCAL_TZ),
        const.SCHEDULE_R_TOU,
        events,
    ) == tariffs.PERIOD_ON_PEAK
    assert tariffs.tou_period(
        datetime(2026, 7, 3, 18, tzinfo=calculator.LOCAL_TZ),
        const.SCHEDULE_R_TOU,
        events,
    ) == tariffs.PERIOD_OFF_PEAK
    assert tariffs.tou_period(
        datetime(2026, 1, 6, 12, tzinfo=calculator.LOCAL_TZ),
        const.SCHEDULE_R_TOU,
        events,
    ) == tariffs.PERIOD_DISCOUNT


def test_cpp_shifted_start_hour():
    events = tariffs.parse_cpp_events("2026-07-06@17")
    period = tariffs.tou_period(
        datetime(2026, 7, 6, 17, tzinfo=calculator.LOCAL_TZ),
        const.SCHEDULE_R_TOU_CPP,
        events,
    )
    assert period == tariffs.PERIOD_CRITICAL_PEAK


def test_ev_cross_midnight_discount():
    assert tariffs.tou_period(
        datetime(2026, 2, 1, 23, tzinfo=calculator.LOCAL_TZ),
        const.SCHEDULE_R_TOU_EV,
        {},
    ) == tariffs.PERIOD_DISCOUNT
    assert tariffs.tou_period(
        datetime(2026, 2, 1, 5, tzinfo=calculator.LOCAL_TZ),
        const.SCHEDULE_R_TOU_EV,
        {},
    ) == tariffs.PERIOD_STANDARD


def test_res_winter_tier_and_basic_charge():
    config = _config(const.SCHEDULE_RES)
    start = _local_as_utc(2026, 1, 2, 12)
    points = calculator.calculate(
        [calculator.UsageInterval(start, start + timedelta(hours=1), 801.0)],
        const.SCHEDULE_RES,
        config,
    )
    expected_energy = 800 * 0.12623 + 1 * 0.11623
    assert round(points[-1].energy_cost_sum, 6) == round(expected_energy, 6)
    assert round(points[-1].total_cost_sum, 6) == round(expected_energy + 14, 6)


def test_daily_aggregate_is_spread_without_losing_energy():
    start = _local_as_utc(2026, 7, 6, 0)
    expanded = calculator.expand_to_hours(
        [calculator.UsageInterval(start, start + timedelta(days=1), 24.0)]
    )
    assert len(expanded) == 24
    assert sum(item.kwh for item in expanded) == 24.0


def test_one_kwh_default_rate_for_every_tou_schedule():
    cases = (
        (const.SCHEDULE_R_TOUD, (2026, 7, 6, 18), 0.15638 + 1.99 + 3.91),
        (const.SCHEDULE_R_TOU, (2026, 7, 6, 18), 0.29905),
        (const.SCHEDULE_R_TOU_CPP, (2026, 7, 6, 18), 0.41002),
        (const.SCHEDULE_R_TOU_EV, (2026, 7, 6, 23), 0.06548),
    )
    for schedule, local_parts, variable_total in cases:
        config = _config(schedule)
        if schedule == const.SCHEDULE_R_TOU_CPP:
            config[const.CONF_CPP_EVENTS] = "2026-07-06"
        start = _local_as_utc(*local_parts)
        point = calculator.calculate(
            [calculator.UsageInterval(start, start + timedelta(hours=1), 1.0)],
            schedule,
            config,
        )[-1]
        assert round(point.energy_cost_sum, 5) == round(
            0.15638 if schedule == const.SCHEDULE_R_TOUD else variable_total, 5
        )
        assert round(point.total_cost_sum, 5) == round(14 + variable_total, 5)


def test_owned_cost_statistic_ids_are_stable():
    assert const.cost_statistic_ids(
        "duke_energy:electric_322516396_energy_consumption"
    ) == (
        "duke_energy_cost:duke_energy_electric_322516396_energy_consumption_energy_cost",
        "duke_energy_cost:duke_energy_electric_322516396_energy_consumption_estimated_total_cost",
    )


if __name__ == "__main__":
    test_shared_tou_periods_and_observed_holiday()
    test_cpp_shifted_start_hour()
    test_ev_cross_midnight_discount()
    test_res_winter_tier_and_basic_charge()
    test_daily_aggregate_is_spread_without_losing_energy()
    test_one_kwh_default_rate_for_every_tou_schedule()
    test_owned_cost_statistic_ids_are_stable()
    print("7 pure calculation tests passed")

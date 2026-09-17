"""Pure rate-engine and tariff-catalogue tests (Home Assistant not required)."""

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
    spec = importlib.util.spec_from_file_location(f"{PACKAGE}.{name}", PACKAGE_PATH / f"{name}.py")
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


def _config(profile_id):
    return {
        **tariffs.PROFILES[profile_id].defaults,
        const.CONF_BILLING_CYCLE_DAY: 1,
        const.CONF_THREE_PHASE: False,
        const.CONF_ADDITIONAL_KWH_RATE: 0.0,
        const.CONF_MONTHLY_ADJUSTMENT: 0.0,
        const.CONF_TAX_PERCENT: 0.0,
        const.CONF_CPP_EVENTS: "",
        const.CONF_DEMAND_MODE: const.DEMAND_MODE_HOURLY,
    }


def _one_hour(profile_id, local_parts, kwh=1.0, config=None):
    config = config or _config(profile_id)
    start = _local_as_utc(*local_parts)
    return calculator.calculate(
        [calculator.UsageInterval(start, start + timedelta(hours=1), kwh)],
        profile_id,
        config,
    )[-1]


def test_catalogue_covers_every_service_area_and_state():
    assert set(tariffs.STATE_NAMES) == {"NC", "SC", "OH", "KY", "IN", "FL"}
    assert set(tariffs.SERVICE_AREAS) == {
        "nc_dep", "nc_dec", "sc_dep", "sc_dec", "oh_deo", "ky_dek", "in_dei", "fl_def"
    }
    assert len(tariffs.PROFILES) >= 35
    assert all(tariffs.profiles_for_area(area) for area in tariffs.SERVICE_AREAS)


def test_every_catalogue_profile_calculates_with_its_defaults():
    for profile_id in tariffs.PROFILES:
        point = _one_hour(profile_id, (2026, 7, 6, 12))
        assert point.total_cost >= 0
        assert point.rate >= 0


def test_carolinas_periods_and_observed_holiday():
    profile = tariffs.PROFILES["nc_dep_r_tou"]
    assert tariffs.tou_period(datetime(2026, 7, 6, 18, tzinfo=calculator.LOCAL_TZ), profile, {}) == tariffs.PERIOD_ON_PEAK
    assert tariffs.tou_period(datetime(2026, 7, 3, 18, tzinfo=calculator.LOCAL_TZ), profile, {}) == tariffs.PERIOD_OFF_PEAK
    assert tariffs.tou_period(datetime(2026, 1, 6, 12, tzinfo=calculator.LOCAL_TZ), profile, {}) == tariffs.PERIOD_DISCOUNT


def test_cpp_event_and_ev_periods():
    cpp = tariffs.PROFILES["nc_dep_r_tou_cpp"]
    events = tariffs.parse_cpp_events("2026-07-06@17")
    assert tariffs.tou_period(datetime(2026, 7, 6, 17, tzinfo=calculator.LOCAL_TZ), cpp, events) == tariffs.PERIOD_CRITICAL_PEAK
    ev = tariffs.PROFILES["nc_dep_r_tou_ev"]
    assert tariffs.tou_period(datetime(2026, 2, 1, 23, tzinfo=calculator.LOCAL_TZ), ev, {}) == tariffs.PERIOD_DISCOUNT
    assert tariffs.tou_period(datetime(2026, 2, 1, 5, tzinfo=calculator.LOCAL_TZ), ev, {}) == tariffs.PERIOD_STANDARD


def test_current_cpp_period_uses_wall_clock():
    config = _config("nc_dep_r_tou_cpp")
    at_2040 = datetime(2026, 9, 16, 20, 40, tzinfo=calculator.LOCAL_TZ)
    period, rate = calculator.current_period_rate(
        at_2040, "nc_dep_r_tou_cpp", config
    )
    assert period == tariffs.PERIOD_ON_PEAK
    assert rate == .21952

    config[const.CONF_CPP_EVENTS] = "2026-09-16"
    period, rate = calculator.current_period_rate(
        at_2040, "nc_dep_r_tou_cpp", config
    )
    assert period == tariffs.PERIOD_CRITICAL_PEAK
    assert rate == .41002

    at_2100 = datetime(2026, 9, 16, 21, 0, tzinfo=calculator.LOCAL_TZ)
    period, _ = calculator.current_period_rate(
        at_2100, "nc_dep_r_tou_cpp", config
    )
    assert period == tariffs.PERIOD_OFF_PEAK


def test_nc_progress_residential_model():
    point = _one_hour("nc_dep_res", (2026, 1, 2, 12), 801)
    energy = 800 * .12623 + .11623
    assert round(point.energy_cost_sum, 6) == round(energy, 6)
    assert round(point.total_cost_sum, 6) == round(energy + 14, 6)


def test_flat_two_tier_and_three_tier_models():
    assert round(_one_hour("nc_dec_rs", (2026, 6, 2, 12)).energy_cost, 6) == .122603
    sc = _one_hour("sc_dec_rs", (2026, 6, 2, 12), 1001)
    assert round(sc.energy_cost, 6) == round(1000 * .138125 + .144661, 6)
    indiana = _one_hour("in_dei_rs", (2026, 6, 2, 12), 1001)
    expected = 300 * .186556 + 700 * .135777 + .123051
    assert round(indiana.energy_cost, 6) == round(expected, 6)


def test_demand_and_seasonal_tou_models():
    demand = _one_hour("nc_dep_r_toud", (2026, 7, 6, 18))
    assert round(demand.total_cost, 5) == round(14 + .15638 + 1.99 + 3.91, 5)
    ohio = _one_hour("oh_deo_td", (2026, 7, 6, 12))
    assert ohio.period == tariffs.PERIOD_ON_PEAK
    assert round(ohio.rate, 6) == .079950


def test_florida_minimum_bill_floor_and_solar_fixed_charge():
    florida = _one_hour("fl_def_rs1", (2026, 7, 6, 12))
    assert florida.total_cost == 30
    config = _config("sc_dec_r_stou")
    config[const.CONF_SYSTEM_SIZE_KW] = 20
    solar = _one_hour("sc_dec_r_stou", (2026, 7, 6, 12), config=config)
    raw = 13.09 + 20 * .47 + 5 * 5.86 + .128191
    assert round(solar.total_cost, 6) == round(raw, 6)


def test_daily_aggregate_is_spread_without_losing_energy():
    start = _local_as_utc(2026, 7, 6, 0)
    expanded = calculator.expand_to_hours([calculator.UsageInterval(start, start + timedelta(days=1), 24)])
    assert len(expanded) == 24
    assert sum(item.kwh for item in expanded) == 24


def test_owned_cost_statistic_ids_are_stable():
    assert const.cost_statistic_ids("duke_energy:electric_322516396_energy_consumption") == (
        "duke_energy_cost:duke_energy_electric_322516396_energy_consumption_energy_cost",
        "duke_energy_cost:duke_energy_electric_322516396_energy_consumption_estimated_total_cost",
    )


if __name__ == "__main__":
    tests = [value for name, value in globals().copy().items() if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} pure calculation tests passed")

"""Read Duke statistics and publish derived cost statistics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    statistics_during_period,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .calculator import (
    LOCAL_TZ,
    CostPoint,
    UsageInterval,
    billing_cycle_key,
    calculate,
    current_period_rate,
)
from .const import (
    CONF_BILLING_CYCLE_DAY,
    CONF_CURRENCY,
    CONF_NAME,
    CONF_SOURCE_STATISTIC,
    CONF_TARIFF_PROFILE,
    DEFAULT_HISTORY_DAYS,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
    cost_statistic_ids,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DukeEnergyCostData:
    """Latest calculated values exposed by sensor entities."""

    last_update: datetime
    last_usage_start: datetime | None
    energy_cost_statistic_id: str
    total_cost_statistic_id: str
    current_rate: float
    current_period: str
    cycle_key: str
    cycle_kwh: float
    cycle_energy_cost: float
    cycle_total_cost: float
    on_peak_demand_kw: float
    max_demand_kw: float
    source_points: int
    derived_points: int
    aggregate_data_estimated: bool


class DukeEnergyCostCoordinator(DataUpdateCoordinator[DukeEnergyCostData]):
    """Coordinate recorder reads and derived-statistic writes."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(hours=DEFAULT_SCAN_INTERVAL_HOURS),
        )
        self.config_entry = entry
        self.config = {**entry.data, **entry.options}
        (
            self.energy_cost_statistic_id,
            self.total_cost_statistic_id,
        ) = cost_statistic_ids(self.config[CONF_SOURCE_STATISTIC])

    async def _async_update_data(self) -> DukeEnergyCostData:
        try:
            rows = await get_instance(self.hass).async_add_executor_job(
                statistics_during_period,
                self.hass,
                dt_util.utcnow() - timedelta(days=DEFAULT_HISTORY_DAYS),
                None,
                {self.config[CONF_SOURCE_STATISTIC]},
                "hour",
                None,
                {"state", "sum"},
            )
            source_rows = rows.get(self.config[CONF_SOURCE_STATISTIC], [])
            intervals, estimated = self._to_intervals(source_rows)
            if not intervals:
                raise UpdateFailed(
                    translation_domain=DOMAIN,
                    translation_key="no_statistics",
                )
            points = calculate(intervals, self.config[CONF_TARIFF_PROFILE], self.config)
            if not points:
                raise UpdateFailed(
                    translation_domain=DOMAIN,
                    translation_key="no_statistics",
                )
            self._write_statistics(points)
            latest = points[-1]
            now = dt_util.utcnow()
            current_cycle = billing_cycle_key(
                now.astimezone(LOCAL_TZ),
                int(self.config[CONF_BILLING_CYCLE_DAY]),
            )
            same_cycle = current_cycle == latest.cycle_key
            current_period, current_rate = current_period_rate(
                now,
                self.config[CONF_TARIFF_PROFILE],
                self.config,
                latest.cycle_kwh if same_cycle else 0.0,
                latest.max_demand_kw if same_cycle else 0.0,
            )
            return DukeEnergyCostData(
                last_update=dt_util.utcnow(),
                last_usage_start=latest.start,
                energy_cost_statistic_id=self.energy_cost_statistic_id,
                total_cost_statistic_id=self.total_cost_statistic_id,
                current_rate=current_rate,
                current_period=current_period,
                cycle_key=latest.cycle_key,
                cycle_kwh=latest.cycle_kwh,
                cycle_energy_cost=latest.cycle_energy_cost,
                cycle_total_cost=latest.cycle_total_cost,
                on_peak_demand_kw=latest.on_peak_demand_kw,
                max_demand_kw=latest.max_demand_kw,
                source_points=len(source_rows),
                derived_points=len(points),
                aggregate_data_estimated=estimated,
            )
        except UpdateFailed:
            raise
        except (KeyError, TypeError, ValueError) as err:
            raise UpdateFailed(str(err)) from err

    @staticmethod
    def _to_intervals(rows: list[dict[str, Any]]) -> tuple[list[UsageInterval], bool]:
        """Convert Recorder rows to usage intervals, preserving aggregate totals."""
        usable = [row for row in rows if row.get("start") is not None]
        usable.sort(key=lambda row: float(row["start"]))
        result: list[UsageInterval] = []
        previous_sum: float | None = None
        previous_gap = timedelta(hours=1)
        aggregate_estimated = False

        for index, row in enumerate(usable):
            start = dt_util.utc_from_timestamp(float(row["start"]))
            if index + 1 < len(usable):
                next_start = dt_util.utc_from_timestamp(float(usable[index + 1]["start"]))
                gap = next_start - start
                if gap <= timedelta(0) or gap > timedelta(days=40):
                    gap = previous_gap
            else:
                gap = previous_gap
            previous_gap = gap

            state = row.get("state")
            if state is None and row.get("sum") is not None:
                current_sum = float(row["sum"])
                state = 0.0 if previous_sum is None else current_sum - previous_sum
                previous_sum = current_sum
            elif row.get("sum") is not None:
                previous_sum = float(row["sum"])
            if state is None:
                continue
            kwh = float(state)
            if kwh < 0:
                continue
            if gap > timedelta(hours=1, minutes=5):
                aggregate_estimated = True
            result.append(UsageInterval(start, start + gap, kwh))
        return result, aggregate_estimated

    def _write_statistics(self, points: list[CostPoint]) -> None:
        """Queue replacement/upsert of owned external statistics."""
        currency = str(self.config[CONF_CURRENCY]).upper()
        name = str(self.config[CONF_NAME])
        energy_meta = StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_sum=True,
            name=f"{name} energy cost",
            source=DOMAIN,
            statistic_id=self.energy_cost_statistic_id,
            unit_class=None,
            unit_of_measurement=currency,
        )
        total_meta = StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_sum=True,
            name=f"{name} estimated total cost",
            source=DOMAIN,
            statistic_id=self.total_cost_statistic_id,
            unit_class=None,
            unit_of_measurement=currency,
        )
        energy_rows = [
            StatisticData(start=p.start, state=p.energy_cost, sum=p.energy_cost_sum)
            for p in points
        ]
        total_rows = [
            StatisticData(start=p.start, state=p.total_cost, sum=p.total_cost_sum)
            for p in points
        ]
        async_add_external_statistics(self.hass, energy_meta, energy_rows)
        async_add_external_statistics(self.hass, total_meta, total_rows)

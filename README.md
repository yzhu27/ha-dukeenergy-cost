# Duke Energy Cost

An unofficial Home Assistant integration that estimates Duke Energy Carolinas
North Carolina residential electricity costs from usage imported by the
official Duke Energy/Opower integration. It does not modify that integration or
connect to Duke Energy directly.

Supported schedules: **RES, R-TOUD, R-TOU, R-TOU-CPP, and R-TOU-EV**. Published
tariff values are prefilled and remain user-editable.

> Estimates can differ from a bill because of delayed or aggregate usage,
> 15-minute demand peaks, rider changes, meter-read dates, and rounding. This
> project is not affiliated with Duke Energy.

## Install

Requires Home Assistant 2026.3.0 or newer and a working Duke Energy/Opower kWh
statistic.

### HACS custom repository

1. In **HACS → Integrations → Custom repositories**, add this GitHub repository
   as category **Integration**.
2. Download **Duke Energy Cost** and restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration** and search for it.

### Manual

Copy `custom_components/duke_energy_cost` to
`/config/custom_components/`, restart Home Assistant, and add the integration.

## Configure

1. Select the statistic resembling
   `duke_energy:electric_..._energy_consumption`.
2. Select the schedule printed on the bill and enter the billing-cycle day.
3. Review the prefilled rates. Rates are dollars per kWh; sales tax is a
   percentage—enter `7` for 7%.
4. For R-TOUD, choose a demand method. For R-TOU-CPP, enter announced event
   dates as `YYYY-MM-DD` or `YYYY-MM-DD@HH`.

Use **Configure** on the integration to change any value later.

## Energy dashboard

Edit the existing Duke Energy grid source and select **Use an entity tracking
the total cost**, then choose the statistic ending in `_energy_cost`.

- `_energy_cost`: energy charges aligned with usage; recommended for the Energy
  dashboard.
- `_estimated_total_cost`: energy plus configured fixed charges, demand, riders,
  adjustments, and tax.
- **Billing-cycle estimated total** sensor: recommended view of the full current
  bill estimate.

## Bill adjustments

- **Additional rider/adjustment per kWh:** combined usage-based extras in
  dollars/kWh.
- **Additional monthly adjustment:** fixed amount per billing cycle; credits may
  be entered as negative values.
- **Sales tax:** percentage applied to the calculated subtotal.

Example: enter `0.03481` for $0.03481/kWh, `1.81` for a $1.81 monthly charge,
and `7` for 7% tax. These numbers are examples, not universal rates.

## Important limitations

- Daily/monthly usage is distributed uniformly because its true hourly load
  shape is unavailable.
- R-TOUD hourly data cannot exactly reproduce Duke's 15-minute demand peak;
  manual billed kW values are available.
- CPP event dates must be entered manually.
- Changing rates recalculates retained history with the new values.

Rate details are in [TARIFF_REFERENCE.md](TARIFF_REFERENCE.md). For problems,
check **Developer Tools → Statistics** for `duke_energy_cost:` and open a
[GitHub issue](https://github.com/yzhu27/ha-dukeenergy-cost/issues) with
sanitized logs. Do not post account details or unredacted bills.

To uninstall, first detach the cost statistic from the Energy dashboard, then
delete the integration entry. Its entities and external statistics are removed
automatically.

[Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [MIT License](LICENSE)

[![Open your Home Assistant instance and add this repository to HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=yzhu27&repository=ha-dukeenergy-cost&category=integration)

# Duke Energy Cost

An unofficial Home Assistant integration that turns the cumulative kWh
statistics from the official Duke Energy/Opower integration into estimated
energy cost statistics. It does not request Duke Energy credentials or modify
the official integration.

Residential tariff profiles are bundled for Duke Energy service areas in
**North Carolina, South Carolina, Ohio, Kentucky, Indiana, and Florida**.
Published defaults remain editable because riders, fuel charges, taxes, and
effective dates can vary by account.

> This is an estimate, not a bill. Aggregate usage, billing-demand intervals,
> event notices, riders, meter-read dates, and rounding can cause differences.
> This project is not affiliated with Duke Energy.

## Install

[![Open your Home Assistant instance and add this repository to HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=yzhu27&repository=ha-dukeenergy-cost&category=integration)

In **HACS → Integrations → Custom repositories**, add this repository as an
**Integration**, download **Duke Energy Cost**, and restart Home Assistant.
Then open **Settings → Devices & services → Add integration** and search for
**Duke Energy Cost**.

For a manual installation, copy `custom_components/duke_energy_cost` to
`/config/custom_components/` and restart Home Assistant.

## Configure

1. Select the Duke Energy cumulative kWh statistic.
2. Select the service state and, in NC or SC, the Duke Energy operating company
   printed on the bill.
3. Select the bill-facing plan name or abbreviation, such as
   **Residential Service (RES)**. You do not need to know a leaf number.
4. Review the plan-specific rates. Only inputs used by that plan are shown.

The defaults come from the tariff files listed in
[TARIFF_REFERENCE.md](TARIFF_REFERENCE.md). Plans with separate riders, fuel,
or supplier charges show a warning; combine those bill items under
**Additional riders/adjustments per kWh**. Enter sales tax as a percentage—for
example, `7` means 7%.

## Energy dashboard

Edit the Duke Energy grid source, choose **Use an entity tracking the total
cost**, and select the statistic ending in `_energy_cost`.

- `_energy_cost` is the usage-aligned energy charge and is recommended for the
  Energy dashboard.
- `_estimated_total_cost` also includes configured fixed charges, demand,
  riders, adjustments, minimum-bill floors, and tax.
- The **Billing-cycle estimated total** sensor shows the current-cycle estimate.

## Limits

- Daily or monthly source data is spread uniformly across hours.
- Hourly readings only approximate 15- or 30-minute billing demand; demand plans
  can instead use kW values from the bill.
- CPP event dates must be entered after Duke announces them.
- Solar export credits are not calculated; solar plans should use net-import
  data.
- Changing a plan or rate recalculates retained cost history.

To uninstall, detach the cost statistic from the Energy dashboard and delete
the integration entry. Its generated entities and statistics are removed.

[Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [MIT License](LICENSE)

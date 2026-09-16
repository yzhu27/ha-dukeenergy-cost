# Duke Energy Carolinas, North Carolina residential tariff reference

This file is the implementation source of truth for the bundled defaults in this
repository. It was transcribed from Duke Energy Carolinas NC rate-schedule leafs
500–504 supplied by the user. The PDFs remain the legal source; this integration
is an estimate and is not a billing system.

All energy prices below are converted from cents/kWh to USD/kWh in code.
“Eastern prevailing time” means `America/New_York`, including daylight-saving
time.

## Schedule RES — leaf 500

- Effective: 2025-10-01.
- Customer/basic charge: $14.00 per month, single phase.
- Three-phase service: add $9.00 per month.
- May through September: $0.12623/kWh for all energy.
- October through April: $0.12623/kWh for the first 800 kWh in the billing
  month and $0.11623/kWh thereafter.
- No time-of-use periods.

## Schedule R-TOUD — leaf 501

- Effective: 2025-10-01.
- Customer/basic charge: $14.00 per month, single phase.
- Three-phase service: add $9.00 per month.
- On-peak demand: $1.99/kW per billing month.
- Maximum demand: $3.91/kW per billing month.
- On-peak energy: $0.15638/kWh.
- Off-peak energy: $0.06633/kWh.
- Discount energy: $0.04347/kWh.
- Billing demand is based on 15-minute demand. Duke Energy integration hourly
  energy statistics cannot reproduce a true 15-minute maximum. The integration
  therefore defaults to an explicitly labelled hourly-average estimate and also
  permits demand charges to be disabled or manually supplied.

## Schedule R-TOU — leaf 502

- Effective: 2025-10-01.
- Customer/basic charge: $14.00 per month, single phase.
- Three-phase service: add $9.00 per month.
- On-peak energy: $0.29905/kWh.
- Off-peak energy: $0.11321/kWh.
- Discount energy: $0.07372/kWh.

## Schedule R-TOU-CPP — leaf 503

- Effective: 2025-10-01.
- Customer/basic charge: $14.00 per month, single phase.
- Three-phase service: add $9.00 per month.
- Critical-peak energy: $0.41002/kWh.
- On-peak energy: $0.21952/kWh.
- Off-peak energy: $0.11000/kWh.
- Discount energy: $0.08274/kWh.
- Normally no more than 20 critical-peak days per calendar year, except system
  emergencies. Duke notifies customers by the preceding day.
- On a CPP day, the ordinary on-peak hours become critical-peak hours. Duke may
  move the window one hour earlier or later. The integration accepts explicit
  dates and an optional start-hour override for this reason.

## Shared periods for R-TOUD, R-TOU and R-TOU-CPP

### Summer (May through September)

- On-peak: 18:00–21:00, Monday through Friday, excluding listed holidays.
- Discount: 01:00–06:00 every day, including holidays.
- Off-peak: all other hours.

### Non-summer (October through April)

- On-peak: 06:00–09:00, Monday through Friday, excluding listed holidays.
- Discount: 01:00–03:00 and 11:00–16:00 every day, including holidays.
- Off-peak: all other hours.

### Holidays

- New Year's Day
- Good Friday
- Memorial Day
- Independence Day
- Labor Day
- Thanksgiving Day
- Day after Thanksgiving
- Christmas Day

When a fixed-date holiday falls on Saturday it is observed on Friday; when it
falls on Sunday it is observed on Monday.

## Schedule R-TOU-EV — leaf 504

- Effective: 2026-01-01.
- Pilot schedule.
- Customer/basic charge: $14.00 per month, single phase.
- Three-phase service: add $9.00 per month.
- Standard energy: $0.13096/kWh.
- Discount energy: $0.06548/kWh.
- Discount: 23:00–05:00 every day, including holidays.
- Standard: all other hours.

## Charges deliberately defaulted to zero

The leafs refer to riders, renewable-energy/portfolio adjustments, storm
securitization charges and applicable North Carolina sales tax but do not state
all current numeric values in these five documents. Consequently, the bundled
defaults are:

- Additional per-kWh rider/adjustment: $0.00000/kWh.
- Additional monthly adjustment: $0.00/month.
- Sales tax: 0.000%.

All three values are user-configurable. This avoids inventing a rate while still
allowing the estimate to be tuned against a real bill.

## Calculation conventions used by the integration

- Input is an hourly cumulative-energy statistic supplied by the existing Duke
  Energy integration.
- Each hourly increment is priced according to the local start time of the
  interval.
- The billing-cycle start day defaults to 1 and is configurable from 1 through
  28.
- The basic charge (and optional three-phase charge) is applied once per billing
  cycle in the estimated-total statistic, not in the energy-only cost statistic.
- Optional riders, monthly adjustments, demand charges and tax are included only
  in the estimated-total statistic.
- Rates and configuration changes rebuild the derived history so historical
  totals use one internally consistent configuration.


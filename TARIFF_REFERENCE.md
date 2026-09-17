# Duke Energy residential tariff reference

This document is the implementation reference for residential tariff profiles.
It was rebuilt from the 42 tariff PDFs and eight website screenshots in
`duke-energy-tariff/`. Files were reviewed on 2026-09-16.

The tariff PDFs are the controlling source. A rate listed here is a tariff
component, not a promise that it equals the final bill. Riders, fuel clauses,
taxes, municipal fees, credits and minimum-bill rules must be added when the
source tariff requires them.

## How a customer should select a plan

Do not ask customers to know a leaf or sheet number. Ask for location first,
then show the wording found on the bill and the marketing name shown by Duke.
For example:

`Residential Service (RES) - Standard Rate`

The selector must be searchable by official name, code, marketing name and
leaf/sheet. Leaf and sheet numbers belong in the description, not at the start
of the label.

The required location hierarchy is:

- North Carolina
  - Duke Energy Carolinas
  - Duke Energy Progress
- South Carolina
  - Duke Energy Carolinas
  - Duke Energy Progress
- Ohio
- Kentucky
- Indiana
- Florida

## Configuration models

The selected tariff profile determines which fields are shown.

| Model | Fields shown to the customer |
| --- | --- |
| Flat | Customer charge, energy rate, minimum bill, riders/adjustments, tax |
| Tiered | Customer charge, tier thresholds and rates, seasonal months when applicable, minimum bill, riders/adjustments, tax |
| TOU | Customer charge, peak/off-peak/discount rates and periods, minimum bill, riders/adjustments, tax |
| TOU + demand | TOU fields plus on-peak and maximum-demand rates and demand method |
| TOU + CPP | TOU fields plus critical-peak rate, event dates and optional shifted event hours |
| Solar TOU | TOU + CPP fields plus system size, non-bypassable charge, grid-access fee and net-export handling |

All stored energy rates use USD/kWh even when the tariff prints cents/kWh.
Demand rates use USD/kW. A profile has a stable state/company/code ID, such as
`nc_dep_res`; its effective date is separate metadata so existing Home
Assistant entries survive a published-rate update.

## Shared Carolinas TOU periods

Unless a profile below says otherwise, the NC/SC Carolinas and Progress TOU,
TOU-demand and TOU-CPP schedules use Eastern prevailing time:

- May through September:
  - On-peak: 18:00-21:00, Monday-Friday, excluding tariff holidays.
  - Discount: 01:00-06:00 every day.
  - Off-peak: all remaining hours.
- October through April:
  - On-peak: 06:00-09:00, Monday-Friday, excluding tariff holidays.
  - Discount: 01:00-03:00 and 11:00-16:00 every day.
  - Off-peak: all remaining hours.
- Holidays: New Year's Day, Good Friday, Memorial Day, Independence Day,
  Labor Day, Thanksgiving Day, the day after Thanksgiving, and Christmas Day,
  with the stated Friday/Monday observance rule.
- CPP schedules normally allow up to 20 event days per year. Ordinary on-peak
  hours become critical-peak hours and may be shifted one hour earlier or later
  when Duke announces the event.

## North Carolina - Duke Energy Progress

The following profiles apply to the Duke Energy Progress service territory in
North Carolina.

| Customer-facing choice | Effective | Model | Filed defaults |
| --- | --- | --- | --- |
| Residential Service (RES) - Standard Rate | 2025-10-01 | Seasonal tiered | $14.00/month; May-Sep $0.12623/kWh; Oct-Apr first 800 kWh $0.12623, additional $0.11623 |
| Residential Service Time-of-Use (R-TOUD) - Smart Usage Select Option | 2025-10-01 | TOU + demand | $14.00/month; peak $0.15638, off-peak $0.06633, discount $0.04347; on-peak demand $1.99/kW; maximum demand $3.91/kW |
| Residential Service Time-of-Use (R-TOU) - Smart Usage Option | 2025-10-01 | TOU | $14.00/month; peak $0.29905, off-peak $0.11321, discount $0.07372 |
| Residential Service Time-of-Use with Critical Peak Pricing (R-TOU-CPP) - Flex Savings Option | 2025-10-01 | TOU + CPP | $14.00/month; critical $0.41002, peak $0.21952, off-peak $0.11000, discount $0.08274 |
| Residential Service Pilot Time-of-Use with Discount Charging Period (R-TOU-EV) - EV Overnight Advantage | 2026-01-01 | Two-period TOU | $14.00/month; standard $0.13096, discount $0.06548 |

Additional rules:

- Three-phase service adds $9.00/month.
- R-TOUD demand uses the maximum 15-minute interval. Hourly Duke/Opower data
  can only estimate it; the UI must offer hourly estimate, manual billed kW or
  exclusion.
- R-TOU-EV discount hours are 23:00-05:00 every day; all other hours are
  standard.
- The PDFs reference riders, storm securitization and NC sales tax. Those
  amounts are not supplied by leafs 500-504 and must remain separate,
  user-adjustable values rather than invented defaults.

## North Carolina - Duke Energy Carolinas

All profiles below are effective 2026-01-01 and reference additional riders,
including fuel, efficiency/DSM, clean-energy, storm-securitization and other
adjustments.

| Customer-facing choice | Reference | Model | Filed defaults |
| --- | --- | --- | --- |
| Residential Service (RS) - Standard Rate | Leaf 11 | Flat | $14.00/month; $0.122603/kWh |
| Residential Service, Electric Water Heating and Space Conditioning (RE) - Standard Rate | Leaf 13 | Seasonal tiered | $14.00/month; May-Sep $0.117845/kWh; Oct-Apr first 800 kWh $0.117845, additional $0.106061 |
| Residential Service, Energy Star (ES) | Leaf 14 | Tiered with eligibility variant | $14.00/month. Standard: first 800 $0.116473, additional $0.116473. All-electric: first 800 $0.111953, additional $0.100758. The tier applies Oct-Apr; May-Sep all usage uses the first-tier rate. |
| Residential Service, Time-of-Use (RT) - Smart Usage Select Option | Leaf 15 | TOU + demand | $14.00/month; peak $0.171204, off-peak $0.078411, discount $0.053929; on-peak demand $2.34/kW; maximum demand $4.47/kW |
| Residential Service, Time-of-Use with Critical Peak Pricing (RSTC) - Flex Savings Option | Leaf 136 | TOU + CPP | $14.00/month; critical $0.427695, peak $0.234984, off-peak $0.102875, discount $0.074375 |
| Residential Service for All-Electric Customers, Time-of-Use with Critical Peak Pricing (RETC) - Flex Savings Option | Leaf 137 | TOU + CPP | $14.00/month; critical $0.442601, peak $0.213412, off-peak $0.097428, discount $0.070480 |
| Residential Service Pilot Time-of-Use with Discount Charging Period (RT-EV) - EV Overnight Advantage | Leaf 25 | Two-period TOU | $14.00/month; standard $0.123504, discount $0.061752; discount 23:00-05:00 daily |

The ES profile must ask whether the account is billed on the Standard or
All-Electric column. RT demand is based on a maximum 30-minute interval and
needs the same estimate/manual/exclude choice as other demand tariffs.

## South Carolina - Duke Energy Carolinas

Unless noted otherwise, these profiles are effective 2026-03-01. The tariffs
state that fuel, variable-environmental, avoided-capacity and DERP adjustments
apply, along with the listed riders, storm charges, taxes and municipal fees.
Those amounts are additional unless they are explicitly part of a rate below.

| Customer-facing choice | Reference | Model | Filed defaults |
| --- | --- | --- | --- |
| Residential Service (RS) - Standard Rate | Leaf 11 | Tiered | $11.96/month; first 1,000 kWh $0.138125, additional $0.144661 |
| Residential Service, Electric Water Heating and Space Conditioning (RE) - Standard Rate | Leaf 13 | Tiered | $11.96/month; first 1,000 kWh $0.128547, additional $0.134604 |
| Residential Service, Energy Star (ES) | Leaf 14 | Tiered with eligibility variant | $11.96/month. Standard: first 1,000 $0.131589, additional $0.137798. All-electric: first 1,000 $0.122490, additional $0.128244. |
| Residential Service, Time-of-Use (RT) - Smart Usage Select Option | Leaf 15 | TOU + demand | $13.09/month; peak $0.216118, off-peak $0.096597, discount $0.059814; on-peak demand $2.02/kW; maximum demand $4.72/kW |
| Residential Service, Time-of-Use with Critical Peak Pricing (RSTC) - Flex Savings Option | Leaf 19 | TOU + CPP | $13.09/month; critical $0.403705, peak $0.264869, off-peak $0.131171, discount $0.088409 |
| Residential Service for All-Electric Customers, Time-of-Use with Critical Peak Pricing (RETC) - Flex Savings Option | Leaf 20 | TOU + CPP | $13.09/month; critical $0.392575, peak $0.257296, off-peak $0.123157, discount $0.080971 |
| Residential Service, Time-of-Use with Discount Charging Period (RT-EV) | Leaf 12 | Two-period TOU | Effective 2026-06-01; $13.09/month; standard $0.149616, discount $0.100753; discount 23:00-05:00 daily |
| Residential Service, Solar Time-of-Use (R-STOU) | Leaf 16 | Solar TOU + CPP | Effective 2026-08-01; $13.09/month; critical $0.332758, peak $0.209021, off-peak $0.128191, super-off-peak $0.093782 |

SC Carolinas R-STOU details:

- March-November weekday peak: 18:00-21:00.
- December-February weekday peak: 06:00-09:00 and 18:00-21:00.
- Super-off-peak: 00:00-06:00 in March-November only.
- Non-bypassable charge: $0.47/month per kW of generation capacity.
- Grid-access fee: $5.86/month per kW above 15 kW for systems larger than
  15 kW.
- Minimum customer/distribution charge: $30 under the tariff formula.
- Net excess energy credits require separate export statistics and the
  applicable solar rider; consumption-only input cannot calculate them.

## South Carolina - Duke Energy Progress

All provided profiles are effective 2026-08-01. Each adds applicable riders,
storm recovery, Leaf 601 adjustments, sales tax and local/franchise fees.

| Customer-facing choice | Reference | Model | Filed defaults |
| --- | --- | --- | --- |
| Residential Service (RES) - Standard Rate | Leaf 500 | Seasonal tiered | $11.78/month; May-Sep $0.14949/kWh; Oct-Apr first 800 kWh $0.14949, additional $0.13949 |
| Residential Service Time-of-Use (R-TOUD) - Smart Usage Select Option | Leaf 501 | TOU + demand | $14.63/month; peak $0.20402, off-peak $0.09569, discount $0.06768; on-peak demand $2.47/kW; maximum demand $4.85/kW |
| Residential Service Solar Time-of-Use (R-STOU) | Leaf 502 | Solar TOU + CPP | $14.63/month; critical $0.31865, peak $0.21044, off-peak $0.13584, super-off-peak $0.10588 |
| Time-of-Use/Critical Peak Pricing (R-TOU-CPP) - Flex Savings Option | Leaf 503 | TOU + CPP | $14.63/month; critical $0.38147, peak $0.29480, off-peak $0.13301, discount $0.09272 |
| Residential Service with Discount Charging Period (R-TOU-EV) | Leaf 504 | Two-period TOU | $14.63/month; standard $0.15756, discount $0.10244; discount 23:00-05:00 daily |

Three-phase service adds $9.00/month. R-TOUD demand uses maximum 30-minute
intervals. R-STOU uses the same March-November/December-February peak and
super-off-peak schedule described for SC Carolinas solar TOU. Its additional
charges are $0.49/month per kW non-bypassable and $4.29/month per kW above
15 kW for systems larger than 15 kW, with a $30 minimum
customer/distribution charge.

## Ohio - Duke Energy Ohio

The supplied Ohio sheets contain **distribution charges only** and direct the
reader to Sheet 85 for applicable riders. The defaults below must therefore be
presented as base distribution components, with a visible warning that a final
bill estimate also needs current riders and, where applicable, generation or
supplier charges.

| Customer-facing choice | Reference/effective | Model | Filed distribution defaults |
| --- | --- | --- | --- |
| Rate RS - Residential Service | Sheet 30; 2023-01-03 | Flat | $8.00/month; $0.039693/kWh |
| Rate ORH - Optional Residential Service with Electric Space Heating | Sheet 31; 2023-01-03 | Seasonal tiered + demand-dependent block | $8.00/month. Jun-Sep $0.039693/kWh. Other months: first 1,000 kWh $0.039298, additional $0.021706, and usage above 150 times monthly demand $0.014632. |
| Rate TD-CPP - Optional Time-of-Day with Critical Peak Pricing | Sheet 32; 2023-01-03 | TOU + CPP | $8.00/month; critical $0.096514, summer peak $0.057908, off-peak $0.038605, discount $0.030884 |
| Rate TD - Optional Time-of-Day | Sheet 33; 2025-06-01 | Seasonal TOU | $17.50/month; summer peak $0.079950/off-peak $0.013960; winter peak $0.063519/off-peak $0.013976 |
| Rate RS3P - Residential Three-Phase Service | Sheet 35; 2023-01-03 | Flat | $10.50/month; $0.039693/kWh |
| Rate RSLI - Residential Service, Low Income | Sheet 36; 2023-01-03 | Flat | $2.00/month; $0.039693/kWh |

Rate CUR on Sheet 34 is cancelled and withdrawn; it must not be selectable for
a new configuration.

Ohio period rules:

- TD-CPP summer is May-September. Discount is 00:00-05:00 daily. Summer peak
  is 14:00-20:00 Monday-Friday excluding holidays. Winter has no ordinary peak
  rate; a called winter CPP event is a six-hour window between 06:00 and 21:00.
  Up to 10 CPP days are normally allowed.
- TD summer is June-September. Summer peak is 11:00-20:00 weekdays; winter
  peak is 09:00-14:00 and 17:00-21:00 weekdays; holidays are off-peak.
- ORH winter demand is the greatest 15-minute use with a minimum of 10 kW.
  Its third energy block cannot be estimated accurately from monthly kWh alone.

## Kentucky - Duke Energy Kentucky

The website screenshot and supplied tariff contain one residential schedule:

| Customer-facing choice | Reference/effective | Model | Filed base defaults |
| --- | --- | --- | --- |
| Rate RS - Residential Service | Sheet 30; 2026-09-01 | Flat | $14.75/month; $0.128121/kWh; minimum is the customer charge |

Riders ESM, DSMR, FAC and PSM are applicable and are not numerically included
in the supplied Sheet 30. They must remain separate adjustments until their
current rider sheets are bundled.

## Indiana - Duke Energy Indiana

The website labels Rate RS as Standard Rate and Optional Rate RS TOU as Smart
Usage Option.

| Customer-facing choice | Reference/effective | Model | Filed defaults |
| --- | --- | --- | --- |
| Rate RS - Residential Electric Service - Standard Rate | Sheet 6; 2026-06-17 | Tiered | $13.70/month; first 300 kWh $0.186556, next 700 $0.135777, over 1,000 $0.123051 |
| Optional Rate RS - High Efficiency Residential Service | Sheet 6.3; 2025-02-27 | Seasonal tiered | $13.70/month; first 300 $0.208501, next 700 $0.151748; over 1,000 is $0.112521 Jul-Oct and $0.109746 Nov-Jun |
| Optional Rate RS TOU - Time-of-Use - Smart Usage Option | Sheet 6.5; 2025-02-27 | TOU | $13.70/month; peak $0.214198, off-peak $0.142799, discount $0.085679 |

Indiana RS TOU uses peak 17:00-21:00 all year plus 06:00-08:00 in winter;
discount is 00:00-04:00 and all other hours are off-peak. The filed clock
periods move one hour later during daylight-saving time. Winter runs from the
first Sunday in November through the second Sunday in March. Listed holidays
are off-peak.

The Low-Income Customer Assistance Program on Sheet 6.7 is not a distinct
energy rate. It is a one-time annual bill credit for eligible customers on RS,
High Efficiency RS or RS TOU; the supplied sheet does not state a credit
amount. It should be an optional credit/program setting, not a tariff profile.
The supplied Sheet 7, 7.1 and 7.5 PDFs are commercial schedules and are outside
this residential integration.

All Indiana energy schedules are subject to the applicable adjustment riders
listed in tariff Appendix A; those numeric rider values are not in the supplied
PDFs.

## Florida - Duke Energy Florida

The screenshot lists four residential schedules, but the supplied tariff set
contains current rate files only for RS-1 and RST-1. RSL-1 and RSL-2 are marked
optional and closed to new customers, so they are not selectable without
current supporting rate files.

| Customer-facing choice | Reference/effective | Model | Filed non-fuel defaults |
| --- | --- | --- | --- |
| RS-1 - Residential Service - Standard Rate | Sheet 6.120; 2026-06-01 | Seasonal tiered | $14.35/month. Dec-Feb: first 1,000 kWh $0.08754, additional $0.10242. Mar-Nov: first 1,000 $0.07686, additional $0.08453. $30 minimum bill. |
| RST-1 - Residential Service, Optional Time of Use - Smart Usage Option | Sheet 6.140; 2026-06-01 | TOU | $14.35/month; peak $0.11090, off-peak $0.08215, discount $0.04984; $30 minimum bill |

Florida RST-1 periods:

- Peak 18:00-21:00 Monday-Friday in every month.
- December-February adds a weekday peak of 05:00-10:00.
- Discount is 00:00-06:00 in March-November and 00:00-03:00 in
  December-February.
- Holidays listed by the tariff are excluded from peak hours.

Both Florida PDFs require cost-recovery factors from BA-1 plus separate Fuel
Cost Recovery and Asset Securitization factors. Gross receipts/regulatory
assessment, right-of-way, municipal and sales taxes may also apply. The base
rates above must not be presented as an all-in price. RS-1 also describes an
optional $7.50/month EV charging credit, but eligibility depends on charger
behavior that whole-home hourly consumption cannot reliably prove.

## Implementation rules

- Filter profiles by state and operating company before asking for a plan.
- Use the exact customer-facing labels above; never display a bare leaf number
  as the only identifier.
- Prefill only values supported by the bundled PDFs and label base-only rates
  clearly where current riders are missing.
- Hide fields irrelevant to the selected model. For example, Kentucky RS needs
  only customer charge and energy rate, while NC Progress R-TOUD needs three
  energy rates, two demand rates and a demand method.
- Keep each tariff's effective date with its published defaults.
- For CPP plans, require announced event dates; without them, estimates must be
  labelled incomplete rather than pricing all peak hours as ordinary peak.
- For demand tariffs, explain the source interval mismatch and allow manual
  billed demand.
- Solar tariffs need both import and export data plus system size. Do not treat
  net consumption as gross imports.
- Keep rider, tax, municipal-fee and manual credit inputs separate from the
  filed base tariff. Defaults should be zero when the required source sheet is
  not bundled.

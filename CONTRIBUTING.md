# Contributing

Thank you for helping improve Duke Energy Cost.

## Before opening an issue

1. Update to the latest release.
2. Check existing issues.
3. Confirm that the official Duke Energy/Opower integration has imported a
   cumulative kWh statistic.
4. Remove private information. Never publish account numbers, service
   addresses, credentials, or unredacted bills.

A useful bug report includes the Home Assistant and integration versions, rate
schedule, source statistic ID, expected and actual behavior, sanitized logs,
and the smallest time range that demonstrates the problem.

## Pull requests

Keep changes focused. Update tests, documentation, translations, and the
changelog when they are affected. Tariff changes must cite the public tariff
leaf and its effective date in the pull-request description.

Run before submitting:

```bash
python tests/test_calculator.py
python -m compileall custom_components/duke_energy_cost
```

GitHub Actions must pass HACS validation, Hassfest, and the Python tests.

## Rate data

Do not derive global defaults from one customer's bill. Base schedule rates on
official public tariff documents. Account-specific riders and adjustments must
remain user-configurable and clearly labeled as such.

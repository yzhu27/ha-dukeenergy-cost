# Changelog

## 0.2.0

- Rename the integration to Duke Energy Cost and change its domain to
  `duke_energy_cost` for the first public repository release.
- Replace the long README with concise installation and usage guidance.
- Add field-level explanations for every rate, charge, demand value, adjustment,
  tax, and billing-cycle input in the configuration UI.
- Add a one-click HACS repository button to the README.
- Add the HACS-required issue tracker, code owner, country and minimum Home
  Assistant metadata.
- Add an original local brand icon, Hassfest validation, issue templates,
  contribution and security guidance, and a publishing checklist.

## 0.1.3

- Classify the component as a service integration so its config entry is shown
  in the Integrations list rather than being routed to Helpers.
- Clear both owned external cost statistics when the config entry is deleted.
- Keep statistic-ID generation in one tested helper used by setup and cleanup.

## 0.1.2

- Replace advanced Home Assistant form selectors with basic text, number,
  boolean and select schemas for broader frontend/backend compatibility.
- Populate the source-statistic dropdown directly from Recorder kWh sum
  statistics.
- Display the integration version in the first setup page description so stale
  custom-component caches are easy to identify.

## 0.1.1

- Fix an empty initial setup dialog on Home Assistant releases where
  `HomeAssistant.config` has no `currency` attribute.
- Use the tariff's known currency, USD, as the portable default.

## 0.1.0

- Initial implementation of schedules RES, R-TOUD, R-TOU, R-TOU-CPP and
  R-TOU-EV.

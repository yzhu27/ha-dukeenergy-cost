# Publishing checklist

This file records the repository settings and release steps that cannot be
completed inside the source tree.

## GitHub repository

- Make the repository public.
- Confirm the owner is `yzhu27`. If the final owner or repository name differs,
  update `documentation`, `issue_tracker`, README links, and `codeowners`.
- Enable Issues and private vulnerability reporting.
- Set this description:

  > Home Assistant custom integration that estimates Duke Energy North Carolina residential electricity costs from Duke/Opower usage statistics.

- Add topics: `home-assistant`, `hacs`, `custom-integration`, `duke-energy`,
  `energy-dashboard`, `north-carolina`, `time-of-use`, `electricity-rates`.
- Do not use a Duke Energy logo or imply official endorsement.

## Before a release

- Confirm the manifest version matches the intended release tag without the
  leading `v` (manifest `0.2.0`, tag `v0.2.0`).
- Confirm tariff sources and effective dates.
- Run the local tests and compile check.
- Push and wait for HACS, Hassfest, and Python test jobs to pass with no ignored
  checks.
- Create a published GitHub Release, not only a tag, and include user-facing
  release notes.
- Install the release through HACS as a custom repository on a clean Home
  Assistant instance before requesting default inclusion.

## HACS default inclusion

- Keep `country: US` because this repository is limited to North Carolina.
- Ensure at least one published release exists.
- Submit from the repository owner's or a major contributor's GitHub account.
- Follow the current HACS inclusion form and resolve every automated review
  finding rather than adding validation ignores.

Official references:

- https://hacs.xyz/docs/publish/start/
- https://hacs.xyz/docs/publish/integration/
- https://hacs.xyz/docs/publish/action/
- https://hacs.xyz/docs/publish/include/

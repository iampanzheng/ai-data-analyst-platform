# Stage 4.4 Package — GitHub Repository & CI

**Version:** v0.1  
**Status:** CANDIDATE

## Goal

Prepare P1 for its first public GitHub publication without changing the application feature set.

## Implemented in v0.1

- GitHub Actions deterministic CI workflow;
- current-tree publication hygiene check;
- optional full-history pre-publication secret/path scan;
- Makefile `repo-check`, `publish-check`, and `ci` targets;
- first-publication runbook;
- Stage 4.4 documentation and project-status updates.

## CI boundary

Default GitHub CI intentionally runs deterministic Mock configuration only. Real-provider acceptance remains an explicit/manual verification because it depends on external credentials, quotas, network behavior, and provider availability.

## Closeout gates

Stage 4.4 is not CLOSED until the actual remote repository exists and:

1. the first push succeeds;
2. public README/assets render correctly;
3. GitHub Actions passes on `main`;
4. repository About description/topics are configured;
5. publication hygiene/history checks pass before the public push.

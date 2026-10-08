# Stage 4.5 — Release / Deployment Decision

**v1.0 closeout — CLOSED; GitHub Release v1.0.0 published.**

## Deployment decision

Release P1 v1.0.0 as a reproducible **local/self-hosted portfolio reference**, without deploying the existing developer configuration to a public server. Existing loopback-bound ports, database defaults, absence of user authentication, and curated dataset are appropriate for local demonstration but **not sufficient for open-internet hosting**.

Public hosting is an optional future initiative requiring a separate threat model and hosting design: ingress/TLS, authentication and authorization, network isolation, managed secrets, database least privilege/credential rotation, persistent volume/backups, rate limiting, telemetry retention/privacy, abuse controls, resource budgets, and external penetration/security review. Do not merely change 127.0.0.1 to 0.0.0.0.

## Release gates

1. Merge Stage 4.5 v0.1 candidate; run `make release-check` on a clean Git working tree.
2. Run `make verify` and `make acceptance` against running local services (when applicable). Record the actual results; acceptance may depend on fixture/preconditions.
3. Push reviewed release commits to `main`, wait for matching-head GitHub Actions **PASS**.
4. Create annotated tag `v1.0.0` on that verified commit; push the tag.
5. Create GitHub Release from that existing tag, using `docs/RELEASE.md` as notes and `docs/assets/p1-ai-data-analyst-demo.mp4` as an asset; publish only after preview.
6. Validate release tag / commit / assets / LICENSE / README media links from signed-out browser, and record actual release URL. A GitHub Release asset link is a reliable downloadable asset but not an inline-player guarantee.
7. Only then write Stage 4.5 v1.0 CLOSED, Phase 4 CLOSED, and final P1 closeout; do not predeclare completion.

## Suggested CLI workflow

```bash
make repo-check
make release-check
make verify
make acceptance
# After reviewing and committing the release candidate, and confirming latest CI green:
git status --short
git log -1 --oneline
git tag -a v1.0.0 -m "P1 AI Data Analyst Platform v1.0.0"
git push origin main
git push origin v1.0.0
gh release create v1.0.0 docs/assets/p1-ai-data-analyst-demo.mp4 \
  --verify-tag --title "P1 AI Data Analyst Platform v1.0.0" \
  --notes-file docs/RELEASE.md
# Confirm via `gh release view v1.0.0 --web`
```

Run `gh auth login` beforehand if GitHub CLI is not authenticated. Alternatively create a Release in GitHub UI, select the existing tag, upload MP4, and paste `docs/RELEASE.md` content. No CI secret is needed for default Mock checks.

## Version policy

`p1-phase4-stage4.x` = internal milestone tags; `v1.0.0` = public portfolio release. Do not force-update a published tag. The final closeout tag may be created later without moving the `v1.0.0` release tag.

## Final release outcome (2026-10-08)

The verified [v1.0.0 Release](https://github.com/iampanzheng/ai-data-analyst-platform/releases/tag/v1.0.0) is public and marked Latest. Release assets include the MP4 and GitHub-generated source archives. The MP4 is downloadable but not reliably playable in the GitHub code viewer. Local Docker Compose is the supported reference deployment, not a public internet service. This outcome was confirmed by user-provided screenshots and verification logs. The release tag remains immutable; final closeout changes are post-release documentation commits on main.

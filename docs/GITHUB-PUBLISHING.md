# GitHub First-Publication Runbook

This runbook is for Stage 4.4. It assumes the P1 repository has remained local until the first public publication.

## Target repository

Recommended name:

```text
ai-data-analyst-platform
```

Recommended default branch:

```text
main
```

Recommended visibility for the portfolio release:

```text
Public
```

Do not add a Website URL until Stage 4.5 has a stable deployment.

Repository description and topics are defined in [`GITHUB-METADATA.md`](GITHUB-METADATA.md).

## 1. Final local gates

From the intended publication branch:

```bash
make repo-check
make verify
make publish-check
```

`make repo-check` scans the current tracked tree. `make publish-check` additionally scans Git history for forbidden `.env` / archive paths and strong secret patterns.

The history scan is intentionally required before the first public push because deleting a secret from the current working tree does not remove it from Git history.

## 2. Review Git state

```bash
git status
git log --oneline --decorate --graph -30
git tag --list 'p1-*'
```

Confirm:

- the working tree is clean;
- meaningful Stage 4 commits are present;
- Stage tags intended for publication exist;
- no generated ZIP/TAR package is tracked;
- the final demo video and canonical screenshots are tracked.

## 3. Decide licensing before publication

This repository currently does not assume an open-source license. Before making the repository public, deliberately choose one of:

- add a license appropriate for the intended reuse policy; or
- publish without a license, which means others do not receive broad reuse rights by default.

Do not add a license mechanically just for appearance.

## 4. Create the GitHub repository

Create an **empty** repository. Do not ask GitHub to initialize README, `.gitignore`, or license if those already exist locally.

Suggested repository name:

```text
ai-data-analyst-platform
```

After creation, add the remote shown by GitHub, for example:

```bash
git remote add origin git@github.com:<OWNER>/ai-data-analyst-platform.git
git remote -v
```

HTTPS is also acceptable if that is the user's preferred authentication flow.

## 5. First push

```bash
git branch -M main
git push -u origin main
git push origin --tags
```

Do not force-push after publication unless there is a specific history-rewrite reason.

## 6. Configure repository About metadata

Use the exact description/topics prepared in [`GITHUB-METADATA.md`](GITHUB-METADATA.md).

Leave Website empty until Stage 4.5.

## 7. Verify GitHub rendering

Check on GitHub:

- README first screen is readable;
- Mermaid architecture renders;
- four screenshots load;
- the MP4 link opens/downloads correctly;
- all relative documentation links resolve;
- Stage status says Stage 4.4 ACTIVE until CI is proven remotely.

## 8. Verify Actions CI

The default workflow is `.github/workflows/ci.yml`.

It intentionally uses deterministic Mock LLM configuration and runs:

```text
repository hygiene
→ make verify
→ cleanup
```

Real-provider acceptance is deliberately excluded from normal PR/push CI because provider secrets, quotas, network latency, and external service availability are not deterministic build properties.

Wait for the initial `CI` workflow to pass on `main` before closing Stage 4.4.

## 9. Optional branch protection after first CI pass

For a solo portfolio repository, keep this lightweight. A reasonable later setting is:

- require the `Deterministic repository verification` check before merge;
- disallow force pushes to `main`;
- keep direct administration simple unless collaborators are added.

Do not add enterprise-style policy complexity solely for appearance.

## 10. Stage 4.4 closeout evidence

Stage 4.4 should close only after:

```text
GitHub repository created
first push completed
README / assets render correctly
initial GitHub Actions CI PASS
About description / topics configured
no public-secret regression found
```


## Publication completed

The first public publication completed successfully:

- repository: `https://github.com/iampanzheng/ai-data-analyst-platform`;
- default branch: `main`;
- first GitHub Actions run: PASS;
- MIT License selected.

The repository-owned MP4 remains the canonical demo asset. A GitHub Release asset can be added in Stage 4.5 for a more polished download/playback surface.

# Dependency license and security plan

Status: the Dependency Review policy and CI job are implemented. Baseline review,
repository settings and the later work below remain open.

This is engineering guidance, not legal advice. A qualified reviewer should
approve the license policy and any exception involving GPL, LGPL or AGPL code.

## What this does

The plan adds two GitHub safety nets without allowing a bot to change the
repository:

- **Dependency Review** checks each pull request. It reports newly introduced
  dependencies and fails CI when one has a license outside the project's policy
  or a known vulnerability above the chosen severity threshold.
- **Dependabot Alerts** watches dependencies already present on the default
  branch. When GitHub learns about a vulnerability, maintainers get an alert.
  Dependabot Security Updates and Version Updates remain disabled, so it makes
  no commits and opens no update pull requests.

Humans continue to update dependencies with `scripts/update-dependencies.sh`.
That script produces the candidate manifest and lockfile changes; the resulting
pull request is where Dependency Review checks licenses and vulnerabilities.
The existing static checks and tests still determine whether the update works.

Trivy is a later, complementary layer. GitHub Dependency Review examines the
dependency change in a pull request; Trivy can examine the complete image built
from the Dockerfile, including its Debian packages.

## Container distribution boundary

This repository does **not** publish a container image. CI builds `p-swamp`
only to test it, loads it into the ephemeral runner and discards it. There is no
registry login, registry write permission or GHCR artifact.

A downstream deployment may build and publish its own image from this
repository's Dockerfile. That distributor must assess the resulting image and
meet the license obligations for what it distributes; those release-compliance
artifacts are not something this repository can generate or retain for an image
it does not publish.

Dependency Review is still useful here. It protects the source tree, the browser
bundle and the image recipe from newly introduced license and vulnerability
risk before a downstream distributor consumes them. If this repository starts
publishing binaries later, SBOM generation, notices, corresponding-source
retention and scheduled artifact scanning need a separate implementation plan.

## Implementation plan

### 1. Correct first-party license metadata

- Change the root `pyproject.toml` license metadata from MIT to the SPDX
  identifier `Apache-2.0`; the repository `LICENSE` and first-party SPDX headers
  already establish that intent.
- Check every first-party package manifest for consistent metadata.
- Refresh affected locks and verify built Python package metadata reports
  Apache-2.0.

### 2. Establish and review the baseline

- The application dependency baseline is recorded in
  `doc/dependency-license-inventory.md`, including the server runtime, browser
  bundle, build/dev tools, desktop base, desktop `[full]` extra, transitive
  packages and commit-pinned Git dependencies.
- Inventory Debian packages in the image recipe separately; Dependency Review
  does not inspect an image filesystem.
- For each item, record whether it is distributed in `p-swamp`, sent to the
  browser, build-only, optional, or separately deployed.
- Review the current MPL-2.0 npm packages and desktop dependencies such as
  PySide6 before selecting an allowlist.
- Record exceptions by package, version or range, scope, rationale, approver and
  review date.

### 3. Enable and verify Dependency Graph

- Enable **Dependency Graph** under repository **Settings > Advanced Security**.
  This is a GitHub repository setting and cannot be enabled by a committed
  workflow with read-only permissions.
- Dependency Review consumes graph snapshots; it does not construct the graph.
  Without this setting the action cannot compare the base and head revisions.
- GitHub parses both npm lockfiles directly. Current GitHub/Dependabot supports
  uv dependency graph jobs for `uv.lock`; the action retries briefly if those
  snapshots are still being generated.
- In the first pull request, inspect **Insights > Dependency graph** and the
  Dependency Review job summary. Confirm that both uv projects, both npm locks,
  transitive packages and commit-pinned Git dependencies appear.
- Add a dependency-submission workflow only if that verification exposes a real
  coverage gap. Running a second graph generator preemptively would add CI time,
  permissions and snapshot-ordering failure modes without improving supported
  manifests.

### 4. Define the license policy

- The evidence-backed permissive SPDX allowlist is stored in
  `.github/dependency-review-config.yml`; its baseline is documented in
  `doc/dependency-license-inventory.md`. An allowlist is preferable to trying to
  enumerate every copyleft or non-standard license that must be denied.
- Decide explicitly whether MPL and LGPL are accepted in each scope.
- Require an architectural and legal exception for GPL or AGPL application
  dependencies.
- Decide whether unknown licenses block immediately or warn during baseline
  cleanup. GitHub reports unknown license metadata but does not fail on it by
  default, so strict unknown-license enforcement needs an additional check.
- The action currently applies one license allowlist to every scope. Any future
  distinction between runtime/browser and optional/development tooling needs
  explicit package exceptions or a separate policy check.

### 5. Priority pull-request gate (implemented)

- `dependency-review` runs in `.github/workflows/quality-checks.yml` using
  `actions/dependency-review-action@v5` with `contents: read` only.
- Both checks are enabled. High and critical runtime vulnerabilities fail, as do
  recognized licenses outside the checked-in allowlist.
- Results stay in the check log and job summary; the workflow has no
  pull-request write permission.
- The normal trigger is `pull_request`, because Dependency Review compares the
  dependency snapshots at the pull request's base and head revisions. It should
  not run on every push to every branch.
- A feature-branch pull request to `main` is the primary test path and uses the
  workflow from that branch. Once the workflow exists on the default branch,
  manual dispatch can also compare the selected branch with a configurable base
  ref.
- Verify in a test pull request that GitHub sees both uv projects, the npm lock,
  path dependencies and transitive dependencies.
- Test one allowed and one deliberately rejected dependency change.
- Require the `dependency-review` job in branch protection and document the
  fourth required job in `AGENTS.md`.

### 6. Enable report-only Dependabot

- Enable **Dependency Graph** and **Dependabot Alerts** in repository settings.
- Leave **Dependabot Security Updates** disabled.
- Leave **Dependabot Version Updates** disabled and do not add
  `.github/dependabot.yml`.
- Configure the relevant maintainers to receive security-alert notifications.
- Keep `scripts/update-dependencies.sh` as the update mechanism.

Dependabot Alerts are generated from the default branch's dependency graph.
They report vulnerabilities but do not change files. When a human chooses to
remediate one, they update the appropriate constraints or run the update script,
review its report and open a normal pull request. Dependency Review then checks
that the proposed replacement did not introduce a prohibited license or another
known vulnerability.

### 7. Add lower-priority Trivy coverage

- Scan `p-swamp:smoketest` after the existing CI image build so the artifact is
  not built twice.
- Initially report findings while the baseline is triaged; make selected
  severities blocking only after establishing an exception process.
- There is no published artifact to scan on a schedule. Revisit scheduled scans
  only if an immutable image is published somewhere in the future.
- Avoid treating every GPL-labelled OS package as an application license-policy
  violation; image composition and application linking are different questions.

## Todo list

- [x] Remove obsolete GHCR publication and redistribution assumptions.
- [x] Add Dependency Review configuration and its CI job.
- [x] Document PR and manual branch-comparison testing.
- [ ] Correct MIT package metadata to Apache-2.0.
- [x] Inventory application dependencies and licenses in every defined scope.
- [ ] Inventory the packages in the final container image.
- [ ] Review existing MPL, LGPL and unknown-license findings.
- [x] Ground the initial SPDX allowlist in the dependency inventory.
- [ ] Verify uv, npm, path and transitive dependency coverage in a test PR.
- [ ] Require `dependency-review` in branch protection.
- [ ] Enable and verify Dependency Graph.
- [ ] Enable Dependabot Alerts only.
- [ ] Confirm Security Updates and Version Updates remain disabled.
- [ ] Document the human remediation path through
      `scripts/update-dependencies.sh`.
- [ ] Obtain legal review of GPL/LGPL/AGPL policy and current findings.
- [ ] Add a non-blocking Trivy image scan later.

## Open questions

- Are MPL-2.0 and LGPL dependencies acceptable, and in which scopes?
- Should unknown licenses block immediately or warn during baseline cleanup?
- Should optional desktop and development dependencies use the same policy as
  dependencies distributed in the web image?
- Should the initial high vulnerability threshold change after baseline review?
- Who approves exceptions and owns periodic review?
- Who should receive Dependabot and failed-check notifications?
- Should this repository ever publish binaries, or should that remain strictly a
  downstream deployment responsibility?

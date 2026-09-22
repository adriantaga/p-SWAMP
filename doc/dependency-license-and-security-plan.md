# Dependency license and security plan

Status: planning document. Nothing below is implemented yet.

This is engineering guidance, not legal advice. A qualified reviewer should
approve the license policy and any exception involving GPL, LGPL or AGPL code.

## What this will do

The first stage adds two GitHub safety nets without allowing a bot to change the
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
dependency change in a pull request; Trivy examines the container that is
actually distributed, including its Debian packages, and can rescan an unchanged
image when new vulnerabilities are disclosed.

## Why the published image matters

The root `Dockerfile` produces one `p-swamp` image containing the built React
client, the FastAPI backend, the root `pswamp` package, Python runtime
dependencies and a Debian userspace. GitHub Actions publishes that image to
GHCR. Pulling from GHCR delivers copies of all those components, so this is
software distribution for license-compliance purposes.

The data-flow branch also runs the same image in three roles: server,
stats-worker and time-series stub. It separately pulls `apache/kafka:4.3.1`.
Only `p-swamp` is built and republished by this repository; Kafka remains a
separate third-party image, but its license and vulnerabilities still matter to
the deployed system.

## GPL binaries in a container

Using an official binary or official base image does not remove the downstream
distributor's obligations. Debian and the base-image publisher may have complied
when distributing to this project; publishing the derived `p-swamp` image is a
new distribution by this project.

At the same time, putting independent programs in one container is commonly
**mere aggregation**. A GPL command-line utility such as a shell or compression
tool does not normally make unrelated application code GPL merely because both
are files in the same image. The conclusion can differ when the application
copies GPL code, links to a GPL library, loads it as a module or otherwise forms
one combined work. A container boundary alone does not decide that question.

For an unmodified, independent GPL binary distributed in the image, the
practical obligations are generally:

1. Keep its copyright and license notices. Debian packages normally install
   these under `/usr/share/doc/<package>/copyright` and refer to license texts
   under `/usr/share/common-licenses`. Verify that image slimming has not removed
   them.
2. Give recipients the GPL license and do not impose terms that contradict
   their GPL rights for that component.
3. Make the **exact corresponding source** for the distributed binary available
   using a method permitted by that component's GPL version. Corresponding
   source includes the source and applicable distribution patches and build
   material, not merely the upstream project's newest source release.
4. Keep that source available for the period and by the delivery mechanism the
   applicable license requires. GPLv2 and GPLv3 express the source-delivery
   alternatives differently.
5. If this project modifies the GPL component, include those modifications in
   the corresponding source and mark changes where required.

The project does **not** need to compile the binary itself for these duties to
apply. Conversely, it does not normally need to relicense `p-swamp` merely
because an unmodified, independent GPL utility is aggregated in the image.

The safest operational approach for online image distribution is not to rely on
a written offer or on an upstream URL continuing to work. For each published
image digest:

- retain an SBOM and the exact binary package versions;
- retain the corresponding Debian source packages, including Debian patches,
  for copyleft binary packages in that image;
- publish or link recipients to a durable source bundle adjacent to the release;
- retain required license and copyright notices; and
- document how a recipient obtains that source from the image/release page.

An ordinary link to a moving Debian or upstream page is weak evidence: it may no
longer contain the exact source used for the binary. A Debian snapshot URL can
help identify exact source, but legal review should decide whether relying on a
third party satisfies the applicable distribution option or whether this
project should host its own bundle.

LGPL and MPL require separate treatment. LGPL commonly requires source for the
covered library and preservation of recipients' ability to replace or relink
it. MPL-2.0 applies at file level and requires source availability for covered
files. AGPL can add source obligations when a modified covered program is used
over a network. These are reasons to classify dependencies rather than treating
every occurrence of the word "GPL" alike.

## Implementation plan

### 1. Correct first-party license metadata

- Change the root `pyproject.toml` license metadata from MIT to the SPDX
  identifier `Apache-2.0`; the repository `LICENSE` and first-party SPDX headers
  already establish that intent.
- Check every first-party package manifest, including `core/pyproject.toml`, for
  consistent metadata.
- Refresh affected locks and verify built Python package metadata reports
  Apache-2.0.

### 2. Establish and review the baseline

- Inventory the server runtime, browser bundle, build/dev tools, desktop base,
  desktop `[full]` extra, Debian image packages and separately deployed images.
- Include transitive packages, Git dependencies and dependencies whose licenses
  cannot be identified.
- For each item, record whether it is distributed in `p-swamp`, sent to the
  browser, build-only, optional, or separately deployed.
- Review the current MPL-2.0 npm packages and desktop dependencies such as
  PySide6 before selecting an allowlist.
- Record exceptions by package, version or range, scope, rationale, approver and
  review date.

### 3. Define the license policy

- Store an explicit permissive SPDX allowlist in
  `.github/dependency-review-config.yml`. An allowlist is preferable to trying
  to enumerate every copyleft or non-standard license that must be denied.
- Decide explicitly whether MPL and LGPL are accepted in each scope.
- Require an architectural and legal exception for GPL or AGPL application
  dependencies.
- Decide whether unknown licenses block immediately or warn during baseline
  cleanup. GitHub reports unknown license metadata but does not fail on it by
  default, so strict unknown-license enforcement needs an additional check.
- Keep runtime/browser policy distinct from optional and development tooling
  where the distribution facts differ.

### 4. Add the priority pull-request gate

- Add a `dependency-review` job to `.github/workflows/quality-checks.yml` using
  `actions/dependency-review-action@v5` with read-only permissions.
- Enable both license and vulnerability checks. Start by failing on high and
  critical runtime vulnerabilities, then adjust after reviewing the baseline.
- Use the checked-in policy file and job summary; do not grant pull-request write
  permission merely to post comments.
- Verify in a test pull request that GitHub sees both uv projects, the npm lock,
  path dependencies, transitive dependencies and the data-flow branch additions.
- Test one allowed and one deliberately rejected dependency change.
- Require the `dependency-review` job in branch protection and document the
  fourth required job in `AGENTS.md`.

### 5. Enable report-only Dependabot

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

### 6. Implement redistribution compliance for GHCR

- Generate an SBOM for the final `p-swamp` image, keyed by immutable image
  digest.
- Verify the final image retains Debian copyright files and common license
  texts; do not assume the base image guarantees they survive later layers.
- Map installed Debian binaries to their exact source package names and versions.
- Decide and implement a durable corresponding-source publication mechanism for
  copyleft components, preferably an archived source bundle per released image.
- Generate a third-party notices/source-location document for each release.
- Retain these compliance artifacts for the required period.
- Review separately pulled images such as Apache Kafka, but do not claim that
  this project redistributes them unless it starts mirroring or repackaging them.

### 7. Add lower-priority Trivy coverage

- Scan `p-swamp:smoketest` after the existing CI image build so the artifact is
  not built twice.
- Initially report findings while the baseline is triaged; make selected
  severities blocking only after establishing an exception process.
- Add a scheduled scan of the published GHCR image because disclosures occur
  without repository changes.
- Scan the separately deployed Kafka image independently.
- Reuse the image SBOM and avoid treating every GPL-labelled OS package as an
  application license-policy violation.

## Todo list

- [ ] Base implementation on the integrated data-flow branch.
- [ ] Correct MIT package metadata to Apache-2.0.
- [ ] Inventory dependencies and licenses in every defined scope.
- [ ] Inventory the packages in the final container image.
- [ ] Review existing MPL, LGPL and unknown-license findings.
- [ ] Agree on the SPDX allowlist and exception record format.
- [ ] Add Dependency Review configuration and its CI job.
- [ ] Verify uv, npm, path and transitive dependency coverage in a test PR.
- [ ] Require `dependency-review` in branch protection.
- [ ] Enable Dependency Graph and Dependabot Alerts only.
- [ ] Confirm Security Updates and Version Updates remain disabled.
- [ ] Document the human remediation path through
      `scripts/update-dependencies.sh`.
- [ ] Decide how exact corresponding source will be retained and published.
- [ ] Verify license/copyright files remain in the final image.
- [ ] Generate an image SBOM and third-party notices artifact.
- [ ] Obtain legal review of GPL/LGPL/AGPL policy and current findings.
- [ ] Add non-blocking Trivy image and scheduled scans later.

## Open questions

- Are MPL-2.0 and LGPL dependencies acceptable, and in which scopes?
- Should unknown licenses block immediately or warn during baseline cleanup?
- Should optional desktop and development dependencies use the same policy as
  dependencies distributed in the web image?
- What vulnerability severity should block the first implementation: high or
  critical?
- Who approves exceptions and owns periodic review?
- Who should receive Dependabot and failed-check notifications?
- Will source bundles be attached to GitHub releases, published as OCI artifacts
  beside GHCR images, or hosted elsewhere?
- How long will compliance artifacts be retained?
- Will the project rely on Debian Snapshot for exact source availability, or
  mirror the source packages it distributes?
- Does legal review agree that each current GPL component is independent
  aggregation rather than linked or combined with `p-swamp`?

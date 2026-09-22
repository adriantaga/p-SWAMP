# Dependency license inventory

Inventory date: 2026-09-22.

This is engineering input to the dependency policy, not legal advice. License
metadata can be incomplete or wrong; reciprocal and commercial alternatives
need qualified review before the project relies on them.

## Scope and method

The inventory covers the dependency inputs committed to this repository:

- `app/client-web/package-lock.json`: 572 npm package records, including
  transitive and platform-specific optional packages;
- `e2e/package-lock.json`: 6 npm package records;
- root `uv.lock` and `app/server-python/uv.lock`: 81 unique registry package and
  version pairs, plus four commit-pinned Git dependencies; and
- actions referenced by `.github/workflows/*.yml`.

npm licenses come directly from each exact package record in the lockfiles.
Python locks do not store license metadata, so the registry-backed results use
the exact locked version's PyPI metadata. Commit-pinned Git dependencies use the
license file at the locked commit. Broad legacy Python classifiers are reported
as broad classifiers rather than guessed into a more specific SPDX license.

This does not inventory Debian packages in the Docker base images. Dependency
Review does not inspect those; the planned image scan is the appropriate check.

## npm results

The web client lock contains these declarations:

| License expression | Package records | Notes |
| --- | ---: | --- |
| MIT | 477 | Predominant application and build-tool license |
| ISC | 26 | Permissive |
| MPL-2.0 | 24 | `lightningcss` plus platform binaries; review required |
| Apache-2.0 | 19 | Permissive with notice and patent terms |
| BSD-2-Clause | 11 | Permissive |
| BSD-3-Clause | 8 | Permissive |
| BlueOak-1.0.0 | 2 | `isexe`, `minimatch`; permissive |
| 0BSD | 1 | Permissive |
| CC-BY-4.0 | 1 | `caniuse-lite` browser data; attribution required |
| OFL-1.1 | 1 | Bundled Geist font |
| Python-2.0 | 1 | Permissive Python license |
| MIT OR CC0-1.0 | 1 | `type-fest`; either permissive option may be used |

The e2e lock contains three Apache-2.0 and three MIT package records. No npm
package record is missing a license declaration.

The npm `dev` marker describes how npm installs a package, not whether code from
that package reaches the browser. For example, Lightning CSS is installed in
the web build stage and transforms CSS, but its executable is not copied into
the final server image.

## Python results

The exact registry package versions group as follows. The two NumPy and SciPy
versions are lock alternatives for different supported Python versions.

| Declared license | Exact locked packages |
| --- | --- |
| Apache-2.0 | `asttokens`, `kafka-python`, `pytest-asyncio`, `tzdata` |
| Apache-2.0 OR BSD-2-Clause | `packaging` |
| BSD-2-Clause | `pygments` |
| BSD-3-Clause | `click`, `idna`, `ipython`, `matplotlib-inline`, `networkx`, `psutil`, `python-dotenv`, `starlette`, `uvicorn`, `websockets` |
| BSD classifier only | `colorama`, `contourpy`, `cycler`, `ipython-pygments-lexers`, `kiwisolver`, `nodeenv`, `numpy-dynamic-array`, `pandas`, `prompt-toolkit`, `pyopengl`, `qtrangeslider`, `scipy` 1.17.1 and 1.18.1, `traitlets` |
| ISC | `pexpect`, `ptyprocess` |
| MIT | `annotated-doc`, `annotated-types`, `anyio`, `cfgv`, `fastapi`, `filelock`, `fonttools`, `httptools`, `identify`, `iniconfig`, `platformdirs`, `pre-commit`, `pydantic`, `pydantic-core`, `pyparsing`, `pyqtgraph`, `pyshp`, `pytest`, `ruff`, `tomli`, `typing-inspection`, `virtualenv`, `wcwidth` |
| MIT classifier only | `executing`, `ezdxf`, `h11`, `jedi`, `nfoursid`, `parso`, `pluggy`, `pure-eval`, `python-discovery`, `pyyaml`, `six`, `stack-data`, `watchfiles` |
| MIT-CMU | `pillow` |
| MPL-2.0 AND MIT | `tqdm`; review required because both licenses apply |
| PSF-2.0 | `distlib`, `matplotlib`, `typing-extensions` |
| Apache-2.0 OR BSD-3-Clause | `python-dateutil` (legacy classifiers) |
| Apache-2.0 OR MIT | `uvloop` (legacy classifiers) |
| BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | `numpy` 2.4.6 and 2.5.2; includes bundled components |
| EPL-2.0 OR BSD-3-Clause | `paho-mqtt`; source distribution is dual licensed |
| LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only OR commercial | `pyside6`, `pyside6-addons`, `pyside6-essentials`, `shiboken6`; review required |

The commit-pinned Git dependencies are:

| Package | Locked commit | License | Scope |
| --- | --- | --- | --- |
| `synchrophasor` (`hallvar-h/pypmu`) | `e16662c` | BSD-3-Clause | Desktop base; excluded from the web image |
| `nqkafka` | `0a90ea2` | MIT | Desktop `[full]` extra |
| `tops-rt` | `f6fe1a4` | MIT | Desktop `[full]` extra |
| `tops` | `5c6e777` | MIT | Transitive through `tops-rt` |

The web server runtime has no MPL, EPL, LGPL or GPL dependency. Those findings
are in the desktop `[full]` extra, except MPL-2.0 in the web build chain. Python
development dependencies in the two locks use permissive licenses.

## GitHub Actions

The workflows reference `actions/checkout`, `actions/setup-node`,
`actions/upload-artifact`, `actions/dependency-review-action`,
`astral-sh/setup-uv`, `docker/setup-buildx-action` and
`docker/build-push-action`. Their repository licenses are MIT or Apache-2.0,
which are already allowed. GitHub recognizes workflow `uses:` entries as
dependencies when Dependency Graph is enabled.

## Policy result

The allowlist contains the observed permissive software licenses plus
CC-BY-4.0 for browser compatibility data and OFL-1.1 for the font. It does not
pre-approve MPL-2.0, EPL-2.0, LGPL or GPL. Existing dependencies are a baseline;
Dependency Review evaluates additions and changes, so an update involving one
of those licenses will stop for explicit review.

Unknown licenses are reported by GitHub but do not fail Dependency Review. The
Python packages with broad or alternative metadata above should therefore also
be checked in the first real pull-request run against GitHub's own license
classification.

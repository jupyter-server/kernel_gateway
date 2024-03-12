# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

## 3.0.1

([Full Changelog](https://github.com/jupyter-server/kernel_gateway/compare/v3.0.0...03a8313485357e9dde2db0751009bc2345791fbd))

### Bugs fixed

- Don't add signal handler for SIGQUIT on Windows [#399](https://github.com/jupyter-server/kernel_gateway/pull/399) ([@jackgerrits](https://github.com/jackgerrits))

### Maintenance and upkeep improvements

- Update Release Scripts [#400](https://github.com/jupyter-server/kernel_gateway/pull/400) ([@blink1073](https://github.com/blink1073))
- Increase test timeout [#397](https://github.com/jupyter-server/kernel_gateway/pull/397) ([@blink1073](https://github.com/blink1073))
- chore: update pre-commit hooks [#396](https://github.com/jupyter-server/kernel_gateway/pull/396) ([@pre-commit-ci](https://github.com/pre-commit-ci))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/kernel_gateway/graphs/contributors?from=2024-02-06&to=2024-03-12&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter-server%2Fkernel_gateway+involves%3Ablink1073+updated%3A2024-02-06..2024-03-12&type=Issues) | [@jackgerrits](https://github.com/search?q=repo%3Ajupyter-server%2Fkernel_gateway+involves%3Ajackgerrits+updated%3A2024-02-06..2024-03-12&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter-server%2Fkernel_gateway+involves%3Apre-commit-ci+updated%3A2024-02-06..2024-03-12&type=Issues) | [@welcome](https://github.com/search?q=repo%3Ajupyter-server%2Fkernel_gateway+involves%3Awelcome+updated%3A2024-02-06..2024-03-12&type=Issues)

<!-- <END NEW CHANGELOG ENTRY> -->

## 3.0.0

([Full Changelog](https://github.com/jupyter-server/kernel_gateway/compare/v3.0.0rc1))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/kernel_gateway/graphs/contributors?from=2024-01-29&to=2024-02-06&type=c))

## 3.0.0rc1

([Full Changelog](https://github.com/jupyter-server/kernel_gateway/compare/v3.0.0rc0...f88571d721e3d6270351e352063a2a8685bf1682))

### Maintenance and upkeep improvements

- Add trusted publisher token permissions [#395](https://github.com/jupyter-server/kernel_gateway/pull/395) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/kernel_gateway/graphs/contributors?from=2024-01-29&to=2024-01-29&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter-server%2Fkernel_gateway+involves%3Ablink1073+updated%3A2024-01-29..2024-01-29&type=Issues)

## 3.0.0rc0

([Full Changelog](https://github.com/jupyter-server/kernel_gateway/compare/2.5.2...bdd97581cd449e11b1efbf8d5cc0b19bfaf17559))

### Enhancements made

- update workflows to point at main [#387](https://github.com/jupyter-server/kernel_gateway/pull/387) ([@Zsailer](https://github.com/Zsailer))
- Use jupyter server as base provider [#384](https://github.com/jupyter-server/kernel_gateway/pull/384) ([@kevin-bates](https://github.com/kevin-bates))

### Maintenance and upkeep improvements

- Update GitHub Actions and Prep for Release [#394](https://github.com/jupyter-server/kernel_gateway/pull/394) ([@blink1073](https://github.com/blink1073))
- Add formatting and lint config [#392](https://github.com/jupyter-server/kernel_gateway/pull/392) ([@blink1073](https://github.com/blink1073))
- Apply auto-formatters [#391](https://github.com/jupyter-server/kernel_gateway/pull/391) ([@blink1073](https://github.com/blink1073))
- Clean up packaging and add py312 support [#389](https://github.com/jupyter-server/kernel_gateway/pull/389) ([@blink1073](https://github.com/blink1073))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter-server/kernel_gateway/graphs/contributors?from=2023-02-06&to=2024-01-29&type=c))

[@blink1073](https://github.com/search?q=repo%3Ajupyter-server%2Fkernel_gateway+involves%3Ablink1073+updated%3A2023-02-06..2024-01-29&type=Issues) | [@codecov](https://github.com/search?q=repo%3Ajupyter-server%2Fkernel_gateway+involves%3Acodecov+updated%3A2023-02-06..2024-01-29&type=Issues) | [@echarles](https://github.com/search?q=repo%3Ajupyter-server%2Fkernel_gateway+involves%3Aecharles+updated%3A2023-02-06..2024-01-29&type=Issues) | [@kevin-bates](https://github.com/search?q=repo%3Ajupyter-server%2Fkernel_gateway+involves%3Akevin-bates+updated%3A2023-02-06..2024-01-29&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyter-server%2Fkernel_gateway+involves%3Apre-commit-ci+updated%3A2023-02-06..2024-01-29&type=Issues) | [@welcome](https://github.com/search?q=repo%3Ajupyter-server%2Fkernel_gateway+involves%3Awelcome+updated%3A2023-02-06..2024-01-29&type=Issues) | [@Zsailer](https://github.com/search?q=repo%3Ajupyter-server%2Fkernel_gateway+involves%3AZsailer+updated%3A2023-02-06..2024-01-29&type=Issues)

## 2.5.0 (2020-04-19)

([Full Changelog](https://github.com/jupyter/kernel_gateway/compare/2.4.3...50b26c553d7eaf6556b1ea9fd8f424388ebb2e94))

### Merged PRs

- Replace TravisCI with Github Actions [#357](https://github.com/jupyter/kernel_gateway/pull/357) ([@dolfinus](https://github.com/dolfinus))
- Fix loading of local notebooks with url special characters in path [#353](https://github.com/jupyter/kernel_gateway/pull/353) ([@bgerrity](https://github.com/bgerrity))
- Render .md files on RTD with MyST-parser [#348](https://github.com/jupyter/kernel_gateway/pull/348) ([@mwouts](https://github.com/mwouts))
- Fix all warnings (but 2) when doing make html [#347](https://github.com/jupyter/kernel_gateway/pull/347) ([@mwouts](https://github.com/mwouts))
- Formally define traits in swagger parser [#346](https://github.com/jupyter/kernel_gateway/pull/346) ([@kevin-bates](https://github.com/kevin-bates))
- Add recommonmark to the list of required Sphinx extensions [#345](https://github.com/jupyter/kernel_gateway/pull/345) ([@mwouts](https://github.com/mwouts))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyter/kernel_gateway/graphs/contributors?from=2020-08-18&to=2021-04-19&type=c))

[@bgerrity](https://github.com/search?q=repo%3Ajupyter%2Fkernel_gateway+involves%3Abgerrity+updated%3A2020-08-18..2021-04-19&type=Issues) | [@dolfinus](https://github.com/search?q=repo%3Ajupyter%2Fkernel_gateway+involves%3Adolfinus+updated%3A2020-08-18..2021-04-19&type=Issues) | [@kevin-bates](https://github.com/search?q=repo%3Ajupyter%2Fkernel_gateway+involves%3Akevin-bates+updated%3A2020-08-18..2021-04-19&type=Issues) | [@mwouts](https://github.com/search?q=repo%3Ajupyter%2Fkernel_gateway+involves%3Amwouts+updated%3A2020-08-18..2021-04-19&type=Issues) | [@willingc](https://github.com/search?q=repo%3Ajupyter%2Fkernel_gateway+involves%3Awillingc+updated%3A2020-08-18..2021-04-19&type=Issues)

## 2.4.3 (2020-08-18)

- [PR-340](https://github.com/jupyter/kernel_gateway/pull/340) enable ssl_version as a JKG config option

## 2.4.2 (2020-08-10)

- [PR-338](https://github.com/jupyter/kernel_gateway/pull/338) Use appropriate maybe-future to handle asyncio futures

## 2.4.1 (2020-06-05)

- [PR-327](https://github.com/jupyter/kernel_gateway/pull/327) Use ==/!= to compare str, bytes, and int literals
- [PR-325](https://github.com/jupyter/kernel_gateway/pull/325) fix: module 'signal' has no attribute 'SIGHUP' on Windows

## 2.4.0 (2019-08-11)

- [PR-323](https://github.com/jupyter/kernel_gateway/pull/323): Update handler not use deprecated maybe_future call
- [PR-322](https://github.com/jupyter/kernel_gateway/pull/322): Update handler compatibility with tornado/pyzmq updates
- [PR-321](https://github.com/jupyter/kernel_gateway/pull/321): Allow Notebook 6.x dependencies
- [PR-317](https://github.com/jupyter/kernel_gateway/pull/317): Better error toleration during server initialization

## 2.3.0 (2019-03-15)

- [PR-315](https://github.com/jupyter/kernel_gateway/pull/315): Call tornado StaticFileHandler.get() as a coroutine

## 2.2.0 (2019-02-26)

- [PR-314](https://github.com/jupyter/kernel_gateway/pull/314): Support serving kernelspec resources
- [PR-307](https://github.com/jupyter/kernel_gateway/pull/307): features.md: Fix a link typo
- [PR-304](https://github.com/jupyter/kernel_gateway/pull/304): Add ability for Kernel Gateway to ignore SIGHUP signal
- [PR-303](https://github.com/jupyter/kernel_gateway/pull/303): Fixed the link to section

## 2.1.0 (2018-08-13)

- [PR-299](https://github.com/jupyter/kernel_gateway/pull/299): adds x_header configuration option for use behind proxies
- [PR-294](https://github.com/jupyter/kernel_gateway/pull/294): Allow access from remote hosts (Notebook 5.6)
- [PR-292](https://github.com/jupyter/kernel_gateway/pull/292): Update dependencies of Jupyter components
- [PR-290](https://github.com/jupyter/kernel_gateway/pull/290): Include LICENSE file in wheels
- [PR-285](https://github.com/jupyter/kernel_gateway/pull/285): Update Kernel Gateway test base class to be compatible with Tornado 5.0
- [PR-284](https://github.com/jupyter/kernel_gateway/pull/284): Add reason argument to set_status() so that custom messages flow back to client
- [PR-280](https://github.com/jupyter/kernel_gateway/pull/280): Add whitelist of environment variables to be inherited from gateway process by kernel
- [PR-275](https://github.com/jupyter/kernel_gateway/pull/275): Fix broken links to notebook-http mode page in docs
- [PR-272](https://github.com/jupyter/kernel_gateway/pull/272): Fix bug when getting kernel language in notebook-http mode
- [PR-271](https://github.com/jupyter/kernel_gateway/pull/271): Fix IPerl notebooks running in notebook-http mode

## 2.0.2 (2017-11-10)

- [PR-266](https://github.com/jupyter/kernel_gateway/pull/266): Make KernelManager and KernelSpecManager configurable
- [PR-263](https://github.com/jupyter/kernel_gateway/pull/263): Correct JSONErrorsMixin for compatibility with notebook 5.2.0

## 2.0.1 (2017-09-09)

- [PR-258](https://github.com/jupyter/kernel_gateway/pull/258): Remove auth token check for OPTIONS requests (CORS)

## 2.0.0 (2017-05-30)

- Update compatibility to notebook>=5.0
- Remove kernel activity API in favor of the one in the notebook package
- Update project overview in the documentation
- Inherit the server `PATH` when launching a new kernel via POST request
  with custom environment variables
- Fix kernel cleanup upon SIGTERM
- Fix security requirements in the swagger spec
- Fix configured headers for OPTIONS requests

## 1.2.2 (2017-05-30)

- Inherit the server `PATH` when launching a new kernel via POST request
  with custom environment variables
- Fix kernel cleanup upon SIGTERM

## 1.2.1 (2017-04-01)

- Add support for auth token as a query parameter

## 1.2.0 (2017-02-12)

- Add command line option to whitelist environment variables for `POST /api/kernels`
- Add support for HTTPS key and certificate files
- Improve the flow and explanations in the `api_intro` notebook
- Fix incorrect use of `metadata.kernelspec.name` as a language name instead of
  `metadata.language.info`
- Fix lingering kernel regression after Ctrl-C interrupt
- Switch to a conda-based dev setup from docker

## 1.1.2 (2016-12-16)

- Fix compatibility with Notebook 4.3 session handler `create_session` call

## 1.1.1 (2016-09-10)

- Add LICENSE file to package distributions

## 1.1.0 (2016-09-08)

- Add an option to force a specific kernel spec for all requests and seed notebooks
- Add support for specifying notebook-http APIs using full Swagger specs
- Add option to serve static web assets from Tornado in notebook-http mode
- Add command line aliases for common options (e.g., `--ip`)
- Fix Tornado 4.4 compatibility: sending an empty body string with a 204 response

## 1.0.0 (2016-07-15)

- Introduce an [API for developing mode plug-ins](https://jupyter-kernel-gateway.readthedocs.io/en/latest/plug-in.html)
- Separate `jupyter-websocket` and `notebook-http` modes into  plug-in packages
- Move mode specific command line options into their respective packages (see `--help-all`)
- Report times with respect to UTC in `/_api/activity` responses

## 0.6.0 (2016-06-17)

- Switch HTTP status from 402 for 403 when server reaches the max kernel limit
- Explicitly shutdown kernels when the server shuts down
- Remove `KG_AUTH_TOKEN` from the environment of kernels
- Fix missing swagger document in release
- Add `--KernelGateway.port_retries` option like in Jupyter Notebook
- Fix compatibility with Notebook 4.2 session handler `create_session` call

## 0.5.1 (2016-04-20)

- Backport `--KernelGateway.port_retries` option like in Jupyter Notebook
- Fix compatibility with Notebook 4.2 session handler `create_session` call

## 0.5.0 (2016-04-04)

- Support multiple cells per path in `notebook-http` mode
- Add a Swagger specification of the `jupyter-websocket` API
- Add `KERNEL_GATEWAY=1` to all kernel environments
- Support environment variables in `POST /api/kernels`
- numpydoc format docstrings on everything
- Convert README to Sphinx/ReadTheDocs site
- Convert `ActivityManager` to a traitlets `LoggingConfigurable`
- Fix `base_url` handling for all paths
- Fix unbounded growth of ignored kernels in `ActivityManager`
- Fix caching of Swagger spec in `notebook-http` mode
- Fix failure to install due to whitespace in `setup.py` version numbers
- Fix call to kernel manager base class when starting a kernel
- Fix test fixture hangs

## 0.4.1 (2016-04-20)

- Backport `--KernelGateway.port_retries` option like in Jupyter Notebook
- Fix compatibility with Notebook 4.2 session handler `create_session` call

## 0.4.0 (2016-02-17)

- Enable `/_api/activity` resource with stats about kernels in `jupyter-websocket` mode
- Enable `/api/sessions` resource with in-memory name-to-kernel mapping for non-notebook clients that want to look-up kernels by associated session name
- Fix prespawn kernel logic regression for `jupyter-websocket` mode
- Fix all handlers so that they return application/json responses on error
- Fix missing output from cells that emit display data in `notebook-http` mode

## 0.3.1 (2016-01-25)

- Fix CORS and auth token headers for `/_api/spec/swagger.json` resource
- Fix `allow_origin` handling for non-browser clients
- Ensure base path is prefixed with a forward slash
- Filter stderr from all responses in `notebook-http` mode
- Set Tornado logging level and Jupyter logging level together with `--log-level`

## 0.3.0 (2016-01-15)

- Support setting of status and headers in `notebook-http` mode
- Support automatic, minimal Swagger doc generation in `notebook-http` mode
- Support download of a notebook in `notebook-http` mode
- Support CORS and token auth in `notebook-http` mode
- Expose HTTP request headers in `notebook-http` mode
- Support multipart form encoding in `notebook-http` mode
- Fix request value JSON encoding when passing requests to kernels
- Fix kernel name handling when pre-spawning
- Fix lack of access logs in `notebook-http` mode

## 0.2.0 (2015-12-15)

- Support notebook-defined HTTP APIs on a pool of kernels
- Disable kernel instance list by default

## 0.1.0 (2015-11-18)

- Support Jupyter Notebook kernel CRUD APIs and Jupyter kernel protocol over Websockets
- Support shared token auth
- Support CORS headers
- Support base URL
- Support seeding kernels code from a notebook at a file path or URL
- Support default kernel, kernel pre-spawning, and kernel count limit
- First PyPI release

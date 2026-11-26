# Maintenance

Read this when updates fail, the browser will not start, a channel fails, or the user wants to uninstall.

- Update: `agent-reach update` upgrades Reach, tools for added channels, and the skill. `agent-reach update --check` only checks for a newer version. Update only with user consent.
- Status: `agent-reach doctor --text` reads local state without network requests. `agent-reach check <channel> --text` performs a live test; `--search` tests only search/jobs. Installation success is not proof of working platform access.
- Browser: `agent-reach browser status` shows state, `browser setup` prepares the browser and extension, and `browser stop` closes the managed browser. After fixing a failed CloakBrowser download, use `browser setup --retry-cloak`.
- Distinguish dependency downloads, browser connections, login, page loading, and rate limits. A network timeout is not proof of expired login.
- Upstream tool errors: record the error and version, then run `agent-reach update` once with user consent. Do not edit installed upstream tools or retry indefinitely.
- Stop the current attempt on `PLATFORM_BLOCKED`, `RATE_LIMITED`, `NEED_LOGIN`, or `BUSY`. Resume after the user resolves the issue; do not repeatedly open windows.
- Keys and proxies: `agent-reach configure groq-key | openai-key | proxy | github-token`. The user supplies the values.
- Port conflict (`Port <n> belongs to an unmanaged browser`): another application holds the dedicated browser port (default 9222). Do not close that application. With consent, use `agent-reach configure browser-port <free-port>`.
- Uninstall: show `agent-reach uninstall --dry-run` first, then run `agent-reach uninstall` after confirmation. Remove only Reach-owned files; preserve other user files and browsers.

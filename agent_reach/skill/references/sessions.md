# Sessions and the dedicated browser

Read this for login, logout, switching accounts, or a `NEED_LOGIN` result.

## Dedicated browser

- Browser channels share one dedicated profile, separate from everyday Chrome. Reach does not close or modify the user's everyday browser.
- Prefer CloakBrowser. If its installation/download fails, use installed Chrome and remember the fallback rather than downloading repeatedly. Retry after fixing connectivity with `agent-reach browser setup --retry-cloak`.
- `agent-reach add <channel>` prepares Node, OpenCLI, the browser, and its extension using tested versions. Windows Chrome fallback may require one manual "Add to Chrome" click.
- Queries are headless by default. Only `agent-reach login <channel>` opens a visible window. Queries reuse an open login window without closing it. While the user logs in, wait for confirmation before querying. After they close it, later queries return to headless mode.
- The browser closes after ten idle minutes and reopens on demand. Real page activity and Reach calls reset the timer. Sessions save periodically during login; the user need not close the window.
- At most two concurrent queries per platform and four total are allowed. Excess queries queue for up to two minutes before returning `BUSY`. Searches on the same platform are at least ten seconds apart. Login, logout, and browser reinstall wait for active queries to finish.
- `agent-reach browser status` shows state, `browser setup` prepares the browser and extension, and `browser stop` closes the managed browser.

## Reusing an existing login

1. On first use, if the user's Chrome is connected to OpenCLI, copy only that site's cookies once into the dedicated browser. Do not copy the full profile, other sites, or password store; do not modify the source browser.
2. Reuse the saved session afterward without periodic reimport. Cookie presence does not prove valid login; use actual action results.
3. If Chrome is not connected, do not promise automatic reuse or infer the user is logged out. Use Reach's saved session.
4. For multiple sources, `agent-reach browser profiles` lists them and `agent-reach browser use <ID>` selects one. Do not switch randomly.
5. `agent-reach login <channel> --import-existing` explicitly copies that site's session again without opening a window. If no session can be copied or the OpenCLI Bridge is unavailable, return `NEED_SETUP` and leave saved sessions unchanged.
6. After the user manually logs into the dedicated window or executes `logout` / `remove`, stop automatic import so an old session cannot reappear.

## When the user must log in

- Ask only when an actual `NEED_LOGIN` result blocks the remaining task. A login button beside public content is not proof that login is required.
- `agent-reach login <channel>` opens the site's login page in the dedicated browser. The user logs in; do not log in for them, request passwords, or print cookies.
- Follow the result's `next` instructions. Some native tools, such as Xueqiu, require `agent-reach login <channel> --sync` afterward.
- Repeat the original action after the user confirms login to verify access.

## Platform differences

- Boss Zhipin search uses OpenCLI and the shared dedicated browser. Do not repeatedly request login when an upstream job-detail bug incorrectly reports it as required.
- Bilibili passes an existing session to its CLI only for subtitles. Ordinary search does not prepare a browser.
- Xueqiu community actions require login; sessions may expire within hours. Repeat the login steps after expiry.

## Logout and removal

- `agent-reach logout <channel>` clears that site's dedicated-browser login and channel state, preserving other sites.
- `agent-reach remove <channel>` removes the channel and that site's login/storage, preserving other sites. On cleanup failure, keep its record and return an error so the user can retry.
- Neither operation is followed by automatic session reimport for that site.

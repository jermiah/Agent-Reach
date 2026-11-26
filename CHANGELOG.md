# Changelog

## Fork sync — 2026-11-26

- Merge 162 upstream commits through `8d9ecc1` (version 1.6.1), including the unified CLI, dedicated browser, session lifecycle, and recent platform/security fixes.
- Keep English documentation, skills, channel descriptions, and installation reports.
- Install and update from `jermiah/Agent-Reach:main`; this fork does not require GitHub release assets. Version checks track the fork, not the original repository.
- Adopt upstream removal of obsolete 1.5 modules and localized README copies.

## [1.6.1] - 2026-11-01


- Several 1.6.0 cases where web search, Reddit, Xiaohongshu or Bilibili failed although the content was reachable, or reported success with empty content, are fixed.
- When another program on your computer uses the browser port, Agent Reach can use a different one; you don't have to close that program.
- A login copy that fails now says so instead of reporting success.
- On Windows, Xiaohongshu links with special characters open correctly.

### Technical details
- Web search: every request identifies itself as `agent-reach/<version>`, so Exa's Cloudflare front no longer blocks it (#877).
- Reddit: when the site tool fails transiently (for example it returns HTML instead of data), search and read fall back to the public web (#880).
- Xiaohongshu: OpenCLI 2.0 results are mapped, so read no longer succeeds with empty fields; search and comments no longer return one empty row when there are no results (#861, #895).
- Bilibili: a QR login that saved no usable credential is no longer reported as success, and the hint now says `agent-reach login bilibili` (#866, #883).
- The dedicated browser's port is configurable with `agent-reach configure browser-port <port>`, for when another tool holds 9222 (#848).
- Login reuse: no "copied 0 cookies" record when the browser bridge is down; an explicit `login <channel> --import-existing` that copies nothing now fails clearly (#879).
- Windows: Xiaohongshu note links containing `&` can be read and their comments loaded (#860).



## [1.6.0] - 2026-10-23


- Upgrading from an older version: just send your AI the "update Agent Reach" sentence. Your keys and settings are kept, and the old program is removed for you.
- Adding a platform takes one sentence. Everything it needs is installed for you, with no admin password; you only log in or enter a key.
- Platforms that need a login, such as Xiaohongshu and X, now use Agent Reach's own browser in the background, never yours, and several AIs can search at once.
- RSS and Exa search are now part of "web". When a new version is out, your AI tells you in plain words what changed and updates only if you say yes.

1.6 is a rebuild. Agents call one command, `agent-reach`; everything Agent Reach installs or stores lives under `~/.agent-reach/`.

### Technical details
- 28 of 40 actions passed real acceptance before release; these shipped untested with maintainer approval: Reddit (test network blocked), Instagram (rate limited), Bilibili subtitles, LinkedIn, Xueqiu hot posts/stocks (no login), Xiaoyuzhou (no key).
- Browser channels share one profile, close after ten idle minutes and reopen on demand.
- Adding a channel prepares its tools; removal clears only that site's login. Default platforms can be removed and updates won't add them back.
- Updating keeps tools that have a tested version at that version; other tools get the newest version inside their supported range.
- Public content remains public-first, with a compact capability receipt.
- Keep Xiaoyuzhou transcription; remove the extra planner and duplicate site extraction.
- Reuse existing local site sessions read-only; queries default to headless, with a visible window for human login.
- The dedicated browser is identified by the id its extension saves inside its own profile, so the user's own Chrome is never mistaken for it; a query no longer closes an open login window.
- Browser channels run queries in parallel: up to 2 per platform and 4 in total, with the rest queued instead of failing BUSY at once; login windows, logout and browser setup wait for running queries.
- Report NEED_LOGIN instead of UPSTREAM_BROKEN when not logged in: Xueqiu community (error 400016), Bilibili subtitles (no Bilibili login), LinkedIn (no LinkedIn login in the dedicated browser).
- Smoother upgrade from 1.5: install and update share one guide, install.md, which checks the version first (update.md, where 1.5 sends users, points to it); `agent-reach update` moves a pip/pipx install to uv by itself; `setup` removes the old Agent Reach program (only Agent Reach itself) and the install report explains what was kept, what changed and which old channels can be added back. Install URLs always point at the latest release.
- Upstream errors reach the agent unchanged (the original message and help); the agent tells the user which platform is temporarily unavailable, by platform name. Reach no longer replaces them with its own advice (NEED_LOGIN still gives Reach's dedicated-browser login steps).


- **update** runs `uv tool install --force` on the latest release, reinstalls every added channel's tools at their declared versions (tested version when set, otherwise the newest version inside `floor`/`exclude`; also when Agent Reach itself has no new release), prunes tools no added channel uses, drops channels no longer in the registry, and refreshes the skill. `result.user_actions` lists in plain sentences what the user must do afterwards. Rollback: `uv tool install --force <previous release zip>`, then `agent-reach update --sync-only`. uv is the only supported installer. 1.5 and earlier installs are migrated on first `setup` / `update`; `config.yaml` keys are kept.
- Xueqiu quotes and stock search via Tencent public quotes (no login); Xueqiu community data uses a session synced from the dedicated browser with `agent-reach login xueqiu --sync`.
- YouTube `transcribe`; LinkedIn reuses OpenCLI search and job-detail in the shared dedicated browser.


- The agent skill is generated from the channel list and replaced on every update.


- RSS channel (agents read feeds themselves).
- xhs-cli, rdt-cli, twitter-cli backends: they read browser cookies by themselves.
- `configure --from-browser`, `twitter-cookies`, `xhs-cookies`, the old `install --channels`, the old `skill --install`, `format`, `check-update`, MCP server entry.
- `watch` (use `doctor`, which now reports `regressed`), `doctor --live` (use `check`), `browser start` (the browser opens by itself), pipx installs.







## Fork localization history

### English-language fork

- Use English throughout the default README, guides, skill references, CLI messages,
  source comments, and test descriptions.
- Point installation, update, and issue links to `jermiah/Agent-Reach`.
- Preserve upstream attribution, Japanese/Korean README translations, and Unicode
  fixtures that verify compatibility with platform content.

### 🐛 Bug Fixes

#### 🔐 Boss Zhipin — Misjudgment of login status (dual credential storage)

- **Root cause:** Boss has two login state storages that do not represent each other - local `~/.boss-agent/auth/session.enc`
  and browser cookies within dedicated Chrome profiles. `boss status` / `status --live` **Only verify the former**
  (Legacy credential library in the Bridge/httpx era), while `existing-browser`’s search in strict CDP mode uses browser cookies.
  When "there are old credentials locally + the browser is not logged in", `boss status` will be reported as `logged_in: true`, misleading the Agent.
  Skip the login and search directly, and finally hit `AUTH_EXPIRED`; the old runbook prohibited `_security_check`
  As if not logged in, the two rules superimpose and push the Agent to the wrong branch of the "anti-bot slider".
- **Fix:** `check()` Added layer 4 read-only detection `_cdp_zhipin_login_cookie()`, using pure standard library
  The minimal WebSocket client implemented directly asks the CDP browser body (`Storage.getCookies`) whether there is zhipin
  The `wt2` cookie, **depends on the browser**, does not introduce new dependencies, does not launch the browser, and does not perform searches.
  No wt2 → Clearly report "The browser is not logged in, search will report AUTH_EXPIRED" and point to "User login +
  `login --cdp`"; detection failed → "Unknown login status" is reported; the security verification page prompt also includes the browser cookie status.
- **Runbook correction:** Delete the misleading rule "Only trust `boss status` to determine the login status" and change it to doctor's
  Browser cookie detection is accurate; after launching the dedicated Chrome, it will be forced to pause to allow the user to visually confirm the login status;
  `AUTH_EXPIRED` is set as ground truth (go directly to the login process, and interpretation in the direction of security verification is prohibited),
  `_security_check` is processed by the slider only when there is no `AUTH_EXPIRED`.

### ✨ Features

#### 🎯 Boss Zhipin channel

- Added `boss` channel: Search jobs via boss-agent-cli + CDP in Chrome and get the full text of JD.
- `check()` Layer 4 read-only detection (boss-agent-cli is installed or not → 9222 port reachability → whether there is zhipin tab
  → Whether there is `wt2` login cookie in the browser).
- Grab the public API (`search_jobs` + `job_card_browser` + `browser_source="existing-browser"`).
- `agent-reach install --system --channels=boss` can install the locked upstream boss-agent-cli
  (#403–#407 have been merged into master) Fixed commit backend; switch back to version constraints after the upstream releases the official version.
- Skill and installation guide support "help me configure Boss Zhipin": Agent starts a dedicated Chrome that only listens to the loopback address,
  The user is only responsible for manual login, and finally the Agent verifies the login status and CDP link.
- Fixed dependency switching from fork snapshot `8ff6bd3` to upstream commit `4c991b7` (#403–#407 has been merged into
  master): The logged-in CDP session can be reused directly, and the search can be done through `--browser-source existing-browser`
  Disable headless downgrades.
- code 37 is classified according to the original copy: the environment exception is `ENVIRONMENT_RISK` and stops immediately; only clear
  A refresh is allowed only after token/stoken expires. Dedicated Chrome profiles should be reused over time and with reduced frequency.

## [1.3.1] - 2026-03-27

### 🐛 Bug Fixes

#### 📈 Xueqiu — Full restoration

- **Fix the root cause of 400 error:** `_ensure_cookies()` can only obtain `acw_tc` (anti-DDoS token) by visiting the homepage only. `xq_a_token` is dynamically generated by Xueqiu front-end JS and cannot be obtained through pure HTTP requests. Added third-level cookie loading strategy: ① Read config file (saved by `--from-browser`) → ② Automatically extract from local Chrome browser (browser-cookie3 needs to be installed) → ③ homepage fallback
- **Fixed User-Agent:** `"agent-reach/1.0"` was recognized and rejected by the Xueqiu anti-bot system and changed to the real Chrome UA
- **Fix missing `Referer` header:** All API requests plus `Referer: https://xueqiu.com/`
- **Fix `get_hot_posts()` endpoint:** The original endpoint `/statuses/hot/listV3.json` has been abandoned (returns empty body), changed to `/v4/statuses/public_timeline_by_category.json`, and the `item.data` JSON string is correctly parsed to obtain author/likes/text
- **Fix `urllib.request.quote` → `urllib.parse.quote`:** Explicitly use correct module
- **Fix `configure --from-browser` not extracting Xueqiu cookies: ** `PLATFORM_SPECS` joins Xueqiu, detects the existence of `xq_a_token` before saving
- **Correction of misleading documentation:** "No configuration required"/"public API, no login required" in README/SKILL.md → Accurate description requires browser cookie
- **Improve error message:** When `check()` fails, prompt `configure --from-browser chrome` instead of "Proxy may be required"

---

## [1.3.0] - 2026-03-12

### 🆕 New Channels

#### 💻 V2EX
- Hot topics, node topics, topic detail + replies, user profile via public JSON API
- Zero config — no auth, no proxy, no API key required
- `get_hot_topics(limit)`, `get_node_topics(node_name, limit)`, `get_topic(id)`, `get_user(username)`
- Obtain popular posts, node posts, post details + replies, and user information through public JSON API
- Zero configuration, no authentication, no proxy, no API Key required

### 📈 Improvements

- Channel count: 14 → 15
- Number of channels: 14 → 15

---

## [1.1.0] - 2025-02-25

### 🆕 New Channels

#### ~~📷 Instagram~~ (removed — upstream blocked)
- ~~Read public posts and profiles via [instaloader](https://github.com/instaloader/instaloader)~~
- **Removed:** Instagram's aggressive anti-scraping measures broke all available open-source tools (instaloader, etc.). See [instaloader#2585](https://github.com/instaloader/instaloader/issues/2585). Will re-add when upstream recovers.
- **Removed:** Instagram anti-crawling blockade causes all open source tools (instaloader, etc.) to fail. It will be added back after the upstream is restored.

#### 💼 LinkedIn
- Read person profiles, company pages, and job details via [linkedin-scraper-mcp](https://github.com/stickerdaniel/linkedin-mcp-server)
- Search people and jobs via MCP, with Exa fallback
- Fallback to Jina Reader when MCP is not configured
- Read personal profile, company page, and job details through linkedin-scraper-mcp
- Search for talent and jobs through MCP, Exa has the answer
- Automatically fallback to Jina Reader when MCP is not configured

#### 🏢Boss Zhipin
- QR code login via [mcp-bosszp](https://github.com/mucsbr/mcp-bosszp)
- Job search and recruiter greeting via MCP
- Fallback to Jina Reader for reading job pages
- Scan the QR code to log in via mcp-bosszp
- MCP search jobs, say hello to HR
- Jina Reader reads the job page in detail

### 📈 Improvements

- Channel count: 9 → 12
- `agent-reach doctor` now detects all 12 channels
- CLI: added `search-linkedin`, `search-bosszhipin` subcommands
- Updated install guide with setup instructions for new channels
- Number of channels: 9 → 11
- `agent-reach doctor` now detects all 11 channels
- CLI: Added `search-linkedin`, `search-bosszhipin` subcommands
- Added channel configuration instructions in the installation guide

---

## [1.0.0] - 2025-02-24

### 🎉 Initial Release / First release

- 9 channels: Web, Twitter/X, YouTube, Bilibili, GitHub, Reddit, XiaoHongShu, RSS, Exa Search
- CLI with `read`, `search`, `doctor`, `install` commands
- Unified channel interface — each platform is a single pluggable Python file
- Auto-detection of local vs server environments
- Built-in diagnostics via `agent-reach doctor`
- Skill registration for Claude Code / OpenClaw / Cursor
- 9 channels: web page, Twitter/X, YouTube, Bilibili, GitHub, Reddit, XiaoHongShu, RSS, Exa search
- CLI supports `read`, `search`, `doctor`, `install` commands
- Unified Channel Interface — an independent pluggable Python file for each platform
- Automatic detection of local/server environment
- Built-in diagnostics `agent-reach doctor`
- Skill registration supports Claude Code / OpenClaw / Cursor

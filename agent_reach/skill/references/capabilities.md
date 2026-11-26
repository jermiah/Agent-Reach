# Capability scope

Read this when the user asks what can be fetched or how complete a result is.
These are declared capabilities, not guarantees across every network, account, or piece of content.

## Three levels of evidence

- **Public access to try:** existing agent tools, native tools, or public APIs may already satisfy the request without a browser installation or login. Answer from retrieved evidence.
- **Reach capabilities:** declared actions appear in `agent-reach channels`. Reuse saved sessions first; ask the user to log in only when the selected path actually requires it.
- **Locally verified:** list only specific actions that recently passed local acceptance. Installation, saved sessions, and network reachability are not functional acceptance.

## Channels

| Channel | Public routes to try | Reach actions and limits |
|---|---|---|
| GitHub | Public repositories, READMEs, issues/PRs | Repository search, repository/issue/PR reading and returned comments; assess private permissions separately |
| YouTube | Search, titles, descriptions; native tools may return comments/subtitles | search/read/subtitle/transcribe; no unified comments action. Track listings are not subtitle text; transcription requires its tools |
| Bilibili | Search, descriptions; some APIs return comments and parent IDs | search/read/hot/subtitle; no unified comments action. Subtitles depend on the video and access path |
| Reddit | Search, bodies, some comments and public JSON reply relationships | Browser search/read/subreddit; login depends on the path. No complete comment-tree guarantee or posting |
| X/Twitter | Public posts indexed by search; some official embeds return full text | search/profile/tweets/thread; post access does not imply access to every reply |
| XiaoHongShu | Public lists may expose IDs, authors, and titles; never invent missing fields | search/read/comments; text and loaded comments/replies only. No full-export guarantee or claim to understand images/video |
| Instagram | Some indexes and shallow profile data; an app shell is not post content | search finds users, profile reads profiles, posts reads a user's descriptions. No unified comments action or image/video comprehension |
| Facebook | Indexes and possibly truncated HTML snippets | search/profile; no unified detail/comments action. Do not present snippets as full posts |
| LinkedIn | Public job search and descriptions | jobs/read try public pages first; an explicit opencli backend goes directly to the site. Not all jobs are guaranteed readable |
| Boss Zhipin | Indexed job snippets | search/read returns jobs and descriptions. Do not guess salary amounts from encoded values; detail fallbacks follow the channel declaration |
| V2EX | Topics, bodies, and public replies | hot/node/read/user; report the returned scope, not hidden or missing replies |
| Xueqiu | Some public quotes and indexes | quote/search/hot_posts/hot_stocks; verify market-data and community paths separately |
| Web | The agent's own search/read tools | Reach web search/read is an anonymous fallback. Snippets, app shells, and verification pages are not complete bodies |
| Xiaoyuzhou | Episode titles and descriptions | transcribe converts an episode to text; requires a user-provided Groq key (`agent-reach configure groq-key`) |

After login, say the listed browser actions can be enabled or attempted; never promise all comments.
If the user skips login, deliver the public evidence already collected.

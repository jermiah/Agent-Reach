"""Read-only session discovery and explicit connection choices. Never logs a user in."""
import json
import urllib.request
from datetime import datetime
from urllib.parse import urlsplit

from agent_reach.utils.url import host_matches

from .result import BAD_INPUT, ReachError

# These describe public routes an agent can try, not authenticated Reach readiness.
# A successful sample depends on the tool, network exit, content and platform response.
_PUBLIC_ACCESS = {
    'web': 'Use existing public web tools first; Reach fills remaining gaps.',
    'github': 'Try public web pages or APIs for repositories, READMEs, issues, PRs, and public comments.',
    'youtube': 'Try public search and descriptions first; native tools can sometimes fetch comments, subtitles, and timestamps.',
    'bilibili': 'Try public search, descriptions, and statistics first; some public APIs return comments and reply relationships.',
    'xiaoyuzhou': 'Podcast transcription requires a Groq key; installation does not require login.',
    'v2ex': 'Read public topics and available replies first; verify completeness and pagination separately.',
    'reddit': 'Try public search, post bodies, and comments first; some public JSON includes comments and parent_id.',
    'twitter': 'Try public search snippets and individual posts first; public embeds do not provide reply streams.',
    'xiaohongshu': 'Public discovery pages may provide note IDs and authors; this does not prove body or comment access.',
    'instagram': 'Try public search and profiles first; HTML may be only an app shell. Captions and comments are not consistently verified.',
    'facebook': 'Try public search snippets first; post bodies and comments depend on the page and access method.',
    'linkedin': 'Try public job search and descriptions first. Login-free samples worked on 2026-10-21; not all jobs are guaranteed readable.',
    'boss': 'Try public job indexes and pages first; anonymous access was not acceptance-tested in this round.',
    'xueqiu': 'Try public stock quotes and name searches first; community access depends on the chosen backend.',
}

_CAPABILITY_LIMITS = {
    'youtube': ['read returns metadata and descriptions; there is no separate comments action.',
                'Subtitles require available tracks. Transcription needs a configured provider and quota; login does not guarantee subtitles.'],
    'bilibili': ['read returns metadata and descriptions; there is no separate comments action.',
                 'subtitle reads existing subtitles for the first part, possibly requiring login; it does not cover every part.'],
    'reddit': ['read covers returned posts and comments only; no complete comment-tree guarantee or comment-posting action.'],
    'twitter': ['thread covers returned replies only; no complete reply-stream guarantee or posting action.'],
    'xiaohongshu': ['Report only retrieved bodies and loaded comments/replies; no complete-export guarantee.'],
    'instagram': ['search finds users; there is no arbitrary-post read or separate comments action.'],
    'facebook': ['Only search/profile are declared; no separate post reading or comment export is promised.'],
    'linkedin': ['Only job search and job-description reading are declared; no contact or feed scraping is promised.'],
    'boss': ['Only job search and job-description reading are declared; login does not guarantee ongoing platform access.'],
    'v2ex': ['Verify pagination and returned counts before claiming replies are complete.'],
}


# Public web options and authenticated Reach actions; detailed limits stay in capability_summary.
_QUICK_ACCESS = {
    'xiaoyuzhou': ('🔑 Transcription requires a key', '—'),
    'github': ('✅ Find projects, read docs, discussions, and comments', '—'),
    'youtube': ('✅ Find videos, read descriptions and subtitles', '—'),
    'bilibili': ('✅ Find videos and read descriptions', '❌ Read subtitles'),
    'v2ex': ('✅ Read posts and replies', '—'),
    'web': ('✅ Search and read web pages', '—'),
    'reddit': ('✅ Search posts, read bodies and comments', '—'),
    'twitter': ('✅ Search snippets and try full posts', '❌ Search tweets, timelines, and replies'),
    'xiaohongshu': ('✅ Search snippets and find links', '❌ Search the site, read bodies and comments'),
    'instagram': ('✅ Search descriptions', '❌ Find users, profiles, and posts'),
    'facebook': ('✅ Search snippets', '❌ Search the site and view profiles'),
    'linkedin': ('✅ Find jobs and public descriptions', '❌ Search the site'),
    'boss': ('✅ Search titles and find links', '❌ Search the site and read details'),
    'xueqiu': ('✅ Find stocks and quotes', '❌ View trending posts and stocks'),
}

_DISPLAY_NAMES = {
    'xiaoyuzhou': 'Xiaoyuzhou',
    'github': 'GitHub', 'youtube': 'YouTube', 'bilibili': 'Bilibili', 'v2ex': 'V2EX',
    'web': 'Web page', 'reddit': 'Reddit', 'twitter': 'X / Twitter', 'facebook': 'Facebook',
    'instagram': 'Instagram', 'xiaohongshu': 'XiaoHongShu', 'linkedin': 'LinkedIn',
    'boss': 'Boss Zhipin', 'xueqiu': 'Xueqiu',
}

_STATUS_LABELS = {
    'not_added': 'Not added; add when needed', 'needs_setup': 'Needs setup', 'unverified': 'Added; awaiting live verification',
    'ready': 'Verified by acceptance testing', 'search_ready': 'Only search is verified',
    'needs_login': 'Tested action requires login', 'cooldown': 'Access paused',
    'needs_user_action': 'Awaiting human verification', 'broken': 'Current backend failed',
}


def _local_greeting():
    """Use the installing computer's clock and timezone, without a network lookup."""
    hour = datetime.now().hour
    if 5 <= hour < 11:
        return 'Good morning! What would you like to search for? ☀️'
    if 11 <= hour < 14:
        return 'Hello! What would you like to search for?'
    if 14 <= hour < 18:
        return 'Good afternoon! What would you like to search for?'
    if 18 <= hour < 22:
        return 'Good evening! What would you like to search for?'
    return 'Up late? What would you like to search for? 🌙'

def _upgrade_lines(result):
    """Only for users coming from 1.5: what was kept, what changed, what is left to do."""
    migration = result.get('migration')
    if not migration:
        return []
    lines = ['**Upgraded from the older version (1.5):**', '',
             '- Your keys and settings were preserved.',
             '- RSS and Exa are no longer separate channels; use the web channel for searching and reading.',
             '- Platforms such as X and XiaoHongShu now use a dedicated Reach browser; first use tries to reuse your Chrome session.',
             '- Previously installed CLI tools, such as twitter-cli and bili, were kept unchanged.']
    suggested = [_DISPLAY_NAMES.get(n, n) for n in migration.get('suggested_channels') or []]
    if suggested:
        lines.append('- You previously used: ' + ', '.join(suggested) + '. To keep using one, ask me to add it.')
    old = result.get('old_copies') or {}
    if old.get('removed'):
        lines.append('- The old program was removed to avoid conflicts with the new version.')
    for item in old.get('failed') or []:
        from .legacy import manual_command
        lines.append(f"- The old program could not be removed. Run: `{manual_command(item)}`")
    return lines + ['']



def installation_report(result):
    """Render one short receipt; keep detailed evidence in the structured summary."""
    def cell(value):
        return str(value).replace('|', r'\|').replace('\n', ' ')

    entries = result['capability_summary']['channels']
    installs = {row['channel']: row for row in result['default_channels']}
    installed = sum(bool(row['ok']) for row in installs.values())
    completed = all(row['ok'] for row in installs.values())
    lines = [
        _local_greeting(), '',
        f"**Agent Reach {result['version']} {'installation complete' if completed else 'installation needs another step'}.** "
        f'Default features: {installed}/{len(installs)} prepared successfully.', '',
        *_upgrade_lines(result),
        '✅ No login needed; ❌ Try after login; 🔑 Key required; — No additional login needed.', '',
        '| Platform | Available without login | Try after login |', '|---|---|---|',
    ]
    for entry in sorted(entries, key=lambda item: item['level'] != 'default'):
        name = entry['channel']
        label = _DISPLAY_NAMES.get(name, name)
        item = installs.get(name)
        if entry['level'] == 'default':
            if item and not item['ok']:
                label += ' (installation failed: ' + item.get('error', {}).get('code', 'UNKNOWN') + ')'
            elif not item:
                label += ' (User removal preserved)'
        elif entry['reach_status'] in {'needs_setup', 'needs_login', 'cooldown', 'needs_user_action', 'broken'}:
            label += ' (' + _STATUS_LABELS[entry['reach_status']] + ')'
        public, login = _QUICK_ACCESS.get(name, (entry['public_access'], '—'))
        lines.append('| ' + ' | '.join(cell(value) for value in (label, public, login)) + ' |')
    verified = [entry for entry in entries if entry['verified_actions']]
    if verified:
        names = '; '.join(_DISPLAY_NAMES.get(entry['channel'], entry['channel']) + ': ' +
                         '/'.join(entry['verified_actions']) for entry in verified)
        lines += ['', 'Verified: ' + names + '. Other actions have not been individually tested online.']
    else:
        lines += ['', 'Actions have not been individually tested online.']
    lines += ['Use search engines for snippets, titles, and links. Report only retrieved comments; subtitles must exist on the video.', '',
              '**Tell me what you want to look up.** Existing sessions are tried first; a login window opens only when needed.']
    return '\n'.join(lines) + '\n'



def capability_summary(channels, statuses):
    """Describe public options, declared actions and local evidence without any I/O.

    Management supplies status records so this summary cannot initiate discovery,
    installation, login or a live request. Actions always come from the registry.
    """
    by_name = {entry['channel']: entry for entry in statuses}
    entries = []
    for ch in channels:
        current = by_name.get(ch.name, {})
        names = [action.name for action in ch.actions]
        can_login = bool(ch.login_url or ch.login_argv)
        auth_actions = {'bilibili': ['subtitle'], 'xueqiu': ['hot_posts', 'hot_stocks']}.get(
            ch.name, names if can_login else [])
        entries.append({
            'channel': ch.name,
            'level': ch.level,
            'reach_status': current.get('status', 'unverified'),
            'verified_actions': current.get('verified_actions', []),
            'actions': [{'action': action.name, 'detail': action.help} for action in ch.actions],
            'public_access': _PUBLIC_ACCESS.get(ch.name, 'Try existing public web tools first.'),
            'authentication': {
                'when': 'only_if_required',
                'may_enable_actions': [name for name in auth_actions if name in names],
                'note': 'If the remaining task requires authentication, reuse an authorized session before asking the user to log in; verify the action afterward.',
            },
            'limits': _CAPABILITY_LIMITS.get(ch.name, []),
        })
    message = ['Use existing public web tools first; Reach fills gaps without requiring login to every platform.']
    for entry in entries:
        actions = '/'.join(action['action'] for action in entry['actions'])
        status_label = _STATUS_LABELS.get(entry['reach_status'], entry['reach_status'])
        limits = ' '.join(entry['limits'])
        message.append(f"{entry['channel']}: {entry['public_access']} Reach {actions} ({status_label}).{limits}")
    return {
        'policy': 'public_first; login_only_for_remaining_task_when_required',
        'evidence_note': 'Public-access descriptions reflect samples and conditions, not local Reach acceptance. Network errors, HTTP 403, timeouts, or CAPTCHAs alone do not prove login is needed.',
        'channels': entries,
        'message': '\n'.join(message),
    }


def cdp_url():
    from .browser import CDP_URL
    return validate_cdp(CDP_URL)


def validate_cdp(value):
    try:
        u = urlsplit(value)
        valid = (u.scheme == 'http' and u.hostname in {'localhost', '127.0.0.1', '::1'}
                 and u.port and not u.username and not u.password and not u.query
                 and not u.fragment and u.path in ('', '/'))
    except (TypeError, ValueError):
        valid = False
    if not valid:
        raise ReachError(BAD_INPUT, 'CDP must be a loopback HTTP address with an explicit port')
    return value.rstrip('/')


def cdp_status():
    url = cdp_url()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(url + '/json/list', timeout=2) as resp:
            tabs = json.loads(resp.read(1024 * 1024))
        found = isinstance(tabs, list) and any(
            isinstance(t, dict) and t.get('type') == 'page'
            and host_matches(t.get('url', ''), 'zhipin.com') for t in tabs)
        return {'endpoint': url, 'connected': isinstance(tabs, list), 'boss_tab_present': bool(found)}
    except (OSError, ValueError):
        return {'endpoint': url, 'connected': False, 'boss_tab_present': False}


def require_boss_cdp():
    from . import browser, session_reuse
    session_reuse.prepare("boss")
    if not cdp_status()['boss_tab_present']:
        browser.open_url('https://www.zhipin.com/web/geek/jobs')
    browser.touch()
    return browser.CDP_URL

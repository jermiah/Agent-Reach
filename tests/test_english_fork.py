"""The English fork stays English and never updates itself from upstream."""

import io
import re

import pytest

from agent_reach.runtime import manage, update_notice


def test_update_reads_version_from_fork_without_releases(monkeypatch):
    requests = []

    def read(req, timeout):
        requests.append(req.full_url)
        return io.BytesIO(b'__version__ = "1.6.1"\n')

    monkeypatch.setattr(update_notice.urllib.request, "urlopen", read)
    result = update_notice.fetch_latest()
    assert result["latest"] == "1.6.1"
    assert requests == [
        "https://raw.githubusercontent.com/jermiah/Agent-Reach/main/agent_reach/__init__.py"
    ]
    assert "jermiah/Agent-Reach" in result["notes"]
    assert manage.upgrade_command(result["latest"])[-1] == (
        "https://github.com/jermiah/Agent-Reach/archive/refs/heads/main.zip"
    )


def test_update_rejects_non_version_content(monkeypatch):
    monkeypatch.setattr(update_notice.urllib.request, "urlopen",
                        lambda *a, **kw: io.BytesIO(b'<html>not a version</html>'))
    with pytest.raises(ValueError, match="valid Agent Reach version"):
        update_notice.fetch_latest()


def test_skill_is_english_even_on_a_chinese_locale(monkeypatch):
    for key in ("AGENT_REACH_LANG", "LC_ALL", "LC_MESSAGES", "LANG"):
        monkeypatch.setenv(key, "zh_CN.UTF-8")
    assert manage._skill_lang() == "en"
    assert not re.search(r"[\u3400-\u9fff]", manage.render_skill())

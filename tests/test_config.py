from pathlib import Path

import pytest

from llmw.config import Config, ConfigError, load_config, save_config


def test_default_wiki_guard_is_deny():
    assert Config().hooks_wiki_guard == "deny"


def test_wiki_guard_round_trips_through_toml(tmp_path: Path):
    config_path = tmp_path / "config.toml"
    save_config(config_path, Config(hooks_wiki_guard="ask"))
    assert load_config(config_path).hooks_wiki_guard == "ask"


def test_wiki_guard_off_round_trips(tmp_path: Path):
    config_path = tmp_path / "config.toml"
    save_config(config_path, Config(hooks_wiki_guard="off"))
    assert load_config(config_path).hooks_wiki_guard == "off"


def test_extra_root_pages_with_control_chars_round_trips_through_toml(tmp_path: Path):
    # A literal newline/quote/backslash embedded raw in a TOML basic
    # string produces a file tomllib can't parse back — must be escaped.
    config_path = tmp_path / "config.toml"
    values = ["weird\nname.md", 'quote"file.md', "back\\slash.md", "tab\ttab.md"]
    save_config(config_path, Config(extra_root_pages=values))
    assert load_config(config_path).extra_root_pages == values


def test_invalid_wiki_guard_value_falls_back_to_default(tmp_path: Path):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[llmw]\nschema_version = 1\ncreated = \"\"\n\n"
        "[hooks]\nwiki_guard = \"nonsense\"\n",
        encoding="utf-8",
    )
    assert load_config(config_path).hooks_wiki_guard == "deny"


def test_missing_hooks_section_defaults_to_deny(tmp_path: Path):
    config_path = tmp_path / "config.toml"
    config_path.write_text("[llmw]\nschema_version = 1\ncreated = \"\"\n", encoding="utf-8")
    assert load_config(config_path).hooks_wiki_guard == "deny"


def test_malformed_toml_raises_clear_config_error_not_raw_toml_exception(tmp_path: Path):
    config_path = tmp_path / "config.toml"
    config_path.write_text("[llmw\nthis is not valid toml", encoding="utf-8")
    with pytest.raises(ConfigError) as excinfo:
        load_config(config_path)
    message = str(excinfo.value)
    assert "config.toml" in message or str(config_path) in message
    assert "llmw health" in message


def test_scalar_section_raises_clear_config_error_not_attribute_error(tmp_path: Path):
    # Valid TOML, wrong shape: `hooks = "off"` parses fine but is a string,
    # not a table, so hooks.get(...) would previously raise AttributeError.
    config_path = tmp_path / "config.toml"
    config_path.write_text('hooks = "off"\n', encoding="utf-8")
    with pytest.raises(ConfigError) as excinfo:
        load_config(config_path)
    message = str(excinfo.value)
    assert "hooks" in message
    assert "llmw health" in message

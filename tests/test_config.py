from pathlib import Path

from llmw.config import Config, load_config, save_config


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

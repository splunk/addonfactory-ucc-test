import runpy
import sys
from pathlib import Path
from types import ModuleType

import pytest


TEMPLATE_PATH = (
    Path(__file__).parents[2]
    / "splunk_add_on_ucc_modinput_test"
    / "resources"
    / "templates"
    / "splunk_forges.tmpl"
)


def load_template(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    client_module = ModuleType("tests.ucc_modinput_functional.splunk.client")
    client_module.SplunkClient = object
    client_module.SplunkApiError = RuntimeError
    monkeypatch.setitem(
        sys.modules,
        "tests.ucc_modinput_functional.splunk.client",
        client_module,
    )
    return runpy.run_path(str(TEMPLATE_PATH))


class LogLevelClient:
    def __init__(self) -> None:
        self.loglevel = "INFO"
        self.read_count = 0
        self.updates: list[str] = []

    def get_settings_logging(self) -> dict[str, str]:
        self.read_count += 1
        if self.read_count == 2:
            raise RuntimeError("failed to read updated log level")
        return {"loglevel": self.loglevel}

    def update_settings_logging(self, loglevel: str) -> None:
        self.updates.append(loglevel)
        self.loglevel = loglevel


@pytest.mark.parametrize(
    "forge_name", ["try_to_set_loglevel", "set_loglevel"]
)
def test_loglevel_forge_restores_state_when_post_update_read_fails(
    monkeypatch: pytest.MonkeyPatch, forge_name: str
) -> None:
    template = load_template(monkeypatch)
    client = LogLevelClient()
    forge = template[forge_name]

    with pytest.raises(RuntimeError, match="failed to read updated log level"):
        next(forge(client, "DEBUG"))

    assert client.loglevel == "INFO"
    assert client.updates == ["DEBUG", "INFO"]

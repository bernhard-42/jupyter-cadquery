"""Unit tests for jupyter_cadquery.comms — ocp_vscode 3.x compatibility."""

import os
import pytest
from enum import Enum
from unittest.mock import MagicMock, patch, call

os.environ["JUPYTER_CADQUERY"] = "1"

import jupyter_cadquery.comms as comms


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_data_payload(collapse=None, reset_camera=None, orbit_control=None):
    """Build a minimal send_data payload."""
    config = {"viewer": None, "anchor": None}
    if collapse is not None:
        config["collapse"] = collapse
    if reset_camera is not None:
        config["reset_camera"] = reset_camera
    if orbit_control is not None:
        config["orbit_control"] = orbit_control
    return {"type": "data", "data": b"fake", "config": config, "count": 1}


def _make_viewer_mock(collapse="R", reset_camera="reset"):
    """Fake SidecarViewer returned by get_sidecar."""
    widget = MagicMock()
    widget.collapse = collapse
    widget.reset_camera = reset_camera
    viewer = MagicMock()
    viewer.status.return_value = {
        "collapse": collapse,
        "reset_camera": reset_camera,
        "position": None,
        "quaternion": None,
        "target": None,
        "zoom": None,
    }
    viewer._splash = False
    viewer.widget = widget
    return viewer


# ---------------------------------------------------------------------------
# send_data — collapse mapping
# ---------------------------------------------------------------------------

class TestSendDataCollapse:
    """Collapse integers/enums from ocp_vscode 3.x must map to cad_viewer_widget strings."""

    EXPECTED = {0: "C", 1: "R", 2: "E", -1: "1"}

    @pytest.mark.parametrize("int_val,expected_str", EXPECTED.items())
    def test_integer_collapse(self, int_val, expected_str):
        payload = _make_data_payload(collapse=int_val)
        captured = {}

        with patch("jupyter_cadquery.comms.show") as mock_show, \
             patch("jupyter_cadquery.comms.viewer_args", return_value={}), \
             patch("jupyter_cadquery.comms.display_args", return_value={}):
            mock_show.return_value = _make_viewer_mock()
            comms.send_data(payload)
            captured["collapse"] = payload["config"]["collapse"]

        assert captured["collapse"] == expected_str, (
            f"int {int_val} should map to '{expected_str}', got '{captured['collapse']}'"
        )

    @pytest.mark.parametrize("int_val,expected_str", EXPECTED.items())
    def test_enum_collapse(self, int_val, expected_str):
        """Collapse values passed as Enum objects (e.g. Collapse.ROOT) are also mapped."""
        class FakeCollapse(Enum):
            pass

        # Build a one-off enum member with the right .value
        member = object.__new__(FakeCollapse)
        member._value_ = int_val
        member._name_ = f"VAL_{int_val}"

        payload = _make_data_payload(collapse=member)
        with patch("jupyter_cadquery.comms.show") as mock_show, \
             patch("jupyter_cadquery.comms.viewer_args", return_value={}), \
             patch("jupyter_cadquery.comms.display_args", return_value={}):
            mock_show.return_value = _make_viewer_mock()
            comms.send_data(payload)

        assert payload["config"]["collapse"] == expected_str

    def test_string_collapse_passthrough(self):
        """String collapse codes should be left unchanged (no double-conversion)."""
        payload = _make_data_payload(collapse="R")
        with patch("jupyter_cadquery.comms.show") as mock_show, \
             patch("jupyter_cadquery.comms.viewer_args", return_value={}), \
             patch("jupyter_cadquery.comms.display_args", return_value={}):
            mock_show.return_value = _make_viewer_mock()
            comms.send_data(payload)

        assert payload["config"]["collapse"] == "R"

    def test_none_collapse_untouched(self):
        """None collapse should not be modified."""
        payload = _make_data_payload()  # no collapse key
        with patch("jupyter_cadquery.comms.show") as mock_show, \
             patch("jupyter_cadquery.comms.viewer_args", return_value={}), \
             patch("jupyter_cadquery.comms.display_args", return_value={}):
            mock_show.return_value = _make_viewer_mock()
            comms.send_data(payload)

        assert "collapse" not in payload["config"]


# ---------------------------------------------------------------------------
# send_data — "clear" type
# ---------------------------------------------------------------------------

class TestSendDataClear:
    def test_clear_resets_widget_shapes(self):
        viewer = _make_viewer_mock()
        with patch("jupyter_cadquery.comms.get_default_sidecar", return_value="MyViewer"), \
             patch("jupyter_cadquery.comms.get_sidecar", return_value=viewer):
            result = comms.send_data({"type": "clear"})

        assert viewer.widget.shapes is None
        assert result is None

    def test_clear_no_viewer_returns_none(self):
        with patch("jupyter_cadquery.comms.get_default_sidecar", return_value=None):
            result = comms.send_data({"type": "clear"})
        assert result is None

    def test_clear_no_sidecar_returns_none(self):
        with patch("jupyter_cadquery.comms.get_default_sidecar", return_value="V"), \
             patch("jupyter_cadquery.comms.get_sidecar", return_value=None):
            result = comms.send_data({"type": "clear"})
        assert result is None

    def test_unknown_type_raises(self):
        with pytest.raises(TypeError, match="Wrong data type"):
            comms.send_data({"type": "unknown"})


# ---------------------------------------------------------------------------
# send_data — reset_camera
# ---------------------------------------------------------------------------

class TestSendDataResetCamera:
    def test_enum_reset_camera_converted_to_value(self):
        class FakeCam(Enum):
            RESET = "reset"

        payload = _make_data_payload(reset_camera=FakeCam.RESET)
        with patch("jupyter_cadquery.comms.show") as mock_show, \
             patch("jupyter_cadquery.comms.viewer_args", return_value={}), \
             patch("jupyter_cadquery.comms.display_args", return_value={}):
            mock_show.return_value = _make_viewer_mock()
            comms.send_data(payload)

        assert payload["config"]["reset_camera"] == "reset"

    def test_string_reset_camera_passthrough(self):
        payload = _make_data_payload(reset_camera="keep")
        with patch("jupyter_cadquery.comms.show") as mock_show, \
             patch("jupyter_cadquery.comms.viewer_args", return_value={}), \
             patch("jupyter_cadquery.comms.display_args", return_value={}):
            mock_show.return_value = _make_viewer_mock()
            comms.send_data(payload)

        assert payload["config"]["reset_camera"] == "keep"


# ---------------------------------------------------------------------------
# send_command("status") — collapse string → integer
# ---------------------------------------------------------------------------

class TestSendCommandStatus:
    """The widget returns collapse as a string; ocp_vscode 3.x needs an integer."""

    EXPECTED = {"R": 1, "C": 0, "E": 2, "1": -1}

    @pytest.mark.parametrize("str_val,int_val", EXPECTED.items())
    def test_collapse_converted_to_int(self, str_val, int_val):
        viewer = _make_viewer_mock(collapse=str_val)
        with patch("jupyter_cadquery.comms.get_sidecar", return_value=viewer):
            result = comms.send_command("status", title="V")
        assert result["collapse"] == int_val

    def test_no_viewer_returns_empty(self):
        with patch("jupyter_cadquery.comms.get_sidecar", return_value=None):
            result = comms.send_command("status", title="missing")
        assert result == {}

    def test_non_string_collapse_passthrough(self):
        """If collapse is already an int (shouldn't happen, but be safe), leave it."""
        viewer = _make_viewer_mock(collapse=1)
        with patch("jupyter_cadquery.comms.get_sidecar", return_value=viewer):
            result = comms.send_command("status", title="V")
        assert result["collapse"] == 1


# ---------------------------------------------------------------------------
# send_command("config")
# ---------------------------------------------------------------------------

class TestSendCommandConfig:
    def test_returns_user_defaults(self):
        fake_defaults = {"collapse": "1", "_splash": False}
        with patch("jupyter_cadquery.comms.get_user_defaults", return_value=fake_defaults), \
             patch("jupyter_cadquery.comms.get_default_sidecar", return_value=None):
            result = comms.send_command("config")
        assert result["collapse"] == "1"

    def test_splash_taken_from_viewer(self):
        viewer = _make_viewer_mock()
        viewer._splash = True
        fake_defaults = {"collapse": "1", "_splash": False}
        with patch("jupyter_cadquery.comms.get_user_defaults", return_value=dict(fake_defaults)), \
             patch("jupyter_cadquery.comms.get_default_sidecar", return_value="V"), \
             patch("jupyter_cadquery.comms.get_sidecar", return_value=viewer):
            result = comms.send_command("config")
        assert result["_splash"] is True

    def test_unknown_command_raises(self):
        with pytest.raises(ValueError):
            comms.send_command("bogus")


# ---------------------------------------------------------------------------
# send_config — title resolution and collapse mapping
# ---------------------------------------------------------------------------

class TestSendConfig:
    def _run(self, cfg_dict, title_kwarg=None, viewer=None):
        payload = {"type": "ui", "config": cfg_dict}
        mock_viewer = viewer or _make_viewer_mock()
        with patch("jupyter_cadquery.comms.get_sidecar", return_value=mock_viewer), \
             patch("jupyter_cadquery.comms.get_default_sidecar", return_value="Default"):
            comms.send_config(payload, title=title_kwarg)
        return mock_viewer

    def test_title_kwarg_used_when_provided(self):
        viewer = _make_viewer_mock()
        with patch("jupyter_cadquery.comms.get_sidecar", return_value=viewer) as mock_gs:
            comms.send_config({"type": "ui", "config": {"axes": True}}, title="MyViewer")
        mock_gs.assert_called_once_with("MyViewer")

    def test_viewer_key_used_as_fallback(self):
        viewer = _make_viewer_mock()
        with patch("jupyter_cadquery.comms.get_sidecar", return_value=viewer) as mock_gs:
            comms.send_config({"type": "ui", "config": {"viewer": "FromKey", "axes": True}})
        mock_gs.assert_called_once_with("FromKey")

    def test_title_key_used_as_fallback(self):
        viewer = _make_viewer_mock()
        with patch("jupyter_cadquery.comms.get_sidecar", return_value=viewer) as mock_gs:
            comms.send_config({"type": "ui", "config": {"title": "FromTitle", "axes": True}})
        mock_gs.assert_called_once_with("FromTitle")

    def test_default_sidecar_used_when_no_title(self):
        viewer = _make_viewer_mock()
        with patch("jupyter_cadquery.comms.get_sidecar", return_value=viewer) as mock_gs, \
             patch("jupyter_cadquery.comms.get_default_sidecar", return_value="DefaultV"):
            comms.send_config({"type": "ui", "config": {"axes": True}})
        mock_gs.assert_called_once_with("DefaultV")

    def test_viewer_key_excluded_from_setattr(self):
        viewer = _make_viewer_mock()
        with patch("jupyter_cadquery.comms.get_sidecar", return_value=viewer), \
             patch("jupyter_cadquery.comms.get_default_sidecar", return_value="V"):
            comms.send_config({"type": "ui", "config": {"viewer": "V", "axes": True}})
        # setattr should be called for "axes" but NOT for "viewer"
        set_calls = [c for c in viewer.mock_calls if "viewer" in str(c)]
        assert not any("viewer" in str(c) for c in viewer.mock_calls
                       if c != call.status() and "get_sidecar" not in str(c))

    @pytest.mark.parametrize("int_val,expected_str", {0: "C", 1: "R", 2: "E", -1: "1"}.items())
    def test_collapse_int_converted_in_setattr(self, int_val, expected_str):
        viewer = _make_viewer_mock()
        with patch("jupyter_cadquery.comms.get_sidecar", return_value=viewer), \
             patch("jupyter_cadquery.comms.get_default_sidecar", return_value="V"):
            comms.send_config({"type": "ui", "config": {"collapse": int_val}}, title="V")
        # setattr(cv, 'collapse', value) on a MagicMock sets the attribute directly
        assert viewer.collapse == expected_str

    def test_no_sidecar_returns_silently(self):
        with patch("jupyter_cadquery.comms.get_sidecar", return_value=None), \
             patch("jupyter_cadquery.comms.get_default_sidecar", return_value="V"):
            # should not raise
            comms.send_config({"type": "ui", "config": {"axes": True}})

    def test_no_title_and_no_default_returns_silently(self):
        with patch("jupyter_cadquery.comms.get_default_sidecar", return_value=None):
            comms.send_config({"type": "ui", "config": {"axes": True}})

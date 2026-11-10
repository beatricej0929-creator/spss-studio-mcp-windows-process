import asyncio

import pytest
from pydantic import ValidationError

from spss_mcp import config, server
from spss_mcp.method_templates import render_process
from spss_mcp.method_validation import ProcessParams


def test_process_params_support_parallel_mediators():
    params = ProcessParams(
        x="autonomy",
        y="performance",
        mediators=["satisfaction", "trust"],
        bootstrap_samples=5000,
    )
    assert params.model == 4
    assert params.mediators == ["satisfaction", "trust"]


def test_process_params_reject_overlapping_roles():
    with pytest.raises(ValidationError):
        ProcessParams(x="x", y="y", mediators=["x"])


def test_process_params_reject_syntax_injection_variable():
    with pytest.raises(ValidationError):
        ProcessParams(x="x /model=6", y="y", mediators=["m"])


def test_render_process_model4_parallel_syntax():
    params = ProcessParams(
        x="x",
        y="y",
        mediators=["m1", "m2"],
        covariates=["age"],
        pairwise_contrasts=True,
        standardized_coefficients=True,
        seed=2026,
    )
    syntax = render_process(r"C:\data\study.sav", params)
    assert "GET FILE='C:/data/study.sav'" in syntax
    assert "PROCESS y=y" in syntax
    assert "vars=" not in syntax.lower()
    assert "/model=4" in syntax
    assert "/m=m1 m2" in syntax
    assert "/cov=age" in syntax
    assert "/contrast=1" in syntax
    assert "/stand=1" in syntax
    assert "/seed=2026." in syntax


def test_render_process_disables_pairwise_contrast_for_one_mediator():
    syntax = render_process(
        r"C:\data\study.sav", ProcessParams(x="x", y="y", mediators=["m"])
    )
    assert "/contrast=0" in syntax
    assert "/seed=" not in syntax
    assert syntax.endswith(".\n")


def test_process_macro_config_and_version(tmp_path, monkeypatch):
    macro = tmp_path / "process.sps"
    macro.write_text("/* PROCESS version 5.1 */.\n", encoding="windows-1252")
    monkeypatch.setenv("SPSS_PROCESS_MACRO_PATH", str(macro))
    assert config.get_process_macro_path() == str(macro.resolve())
    assert config.get_process_macro_version() == "5.1"


def test_process_tool_loads_trusted_macro(monkeypatch, tmp_path):
    macro = tmp_path / "process.sps"
    macro.write_text(
        "/* PROCESS version 5.1 */.\nDEFINE PROCESS (vars=!charend('/')).\n!ENDDEFINE.",
        encoding="windows-1252",
    )
    captured = {}

    async def fake_run_syntax(syntax, **kwargs):
        captured["syntax"] = syntax
        captured["kwargs"] = kwargs
        return {
            "error": None,
            "output_markdown": "PROCESS output",
            "output_raw": "PROCESS output",
            "summary": {"text": ""},
            "viewer_output_file": None,
            "syntax_file": None,
            "viewer_error": None,
        }

    monkeypatch.setattr(server, "_require_spss", lambda ctx: None)
    monkeypatch.setattr(config, "get_process_macro_path", lambda: str(macro))
    monkeypatch.setattr(config, "get_process_macro_version", lambda path=None: "5.1")
    import spss_mcp.spss_runner as runner

    monkeypatch.setattr(runner, "run_syntax", fake_run_syntax)
    output = asyncio.run(
        server.spss_process(
            file_path=r"C:\data\study.sav",
            x="x",
            y="y",
            mediators=["m1", "m2"],
            save_viewer_output=False,
            save_syntax_file=False,
        )
    )
    assert captured["kwargs"]["prelude_syntax"].startswith("/* PROCESS version 5.1 */")
    assert captured["kwargs"]["prelude_as_lines"] is True
    assert captured["kwargs"]["submit_as_lines"] is True
    assert "PROCESS y=y" in captured["syntax"]
    assert "vars=" not in captured["syntax"].lower()
    assert "Hayes PROCESS v5.1" in output


def test_process_tool_surfaces_macro_error(monkeypatch, tmp_path):
    macro = tmp_path / "process.sps"
    macro.write_text("/* PROCESS version 5.1 */.\n", encoding="windows-1252")

    async def fake_run_syntax(syntax, **kwargs):
        return {
            "error": None,
            "output_markdown": "ERROR: Variable X was not found.",
            "output_raw": "ERROR: Variable X was not found.",
            "summary": {"text": ""},
            "viewer_output_file": None,
            "syntax_file": None,
            "viewer_error": None,
        }

    monkeypatch.setattr(server, "_require_spss", lambda ctx: None)
    monkeypatch.setattr(config, "get_process_macro_path", lambda: str(macro))
    import spss_mcp.spss_runner as runner

    monkeypatch.setattr(runner, "run_syntax", fake_run_syntax)
    output = asyncio.run(
        server.spss_process(
            file_path=r"C:\data\study.sav", x="x", y="y", mediators=["m"]
        )
    )
    assert output.startswith("Error: Hayes PROCESS reported an analysis error")


def test_engine_script_can_preserve_process_line_boundaries():
    from spss_mcp.spss_engine import _make_engine_script

    script = _make_engine_script(r"C:\Program Files\IBM\SPSS Statistics\32")
    assert "submit_as_lines = req.get('submit_as_lines', False)" in script
    assert "syntax.splitlines() if submit_as_lines else syntax" in script
    assert "prelude_syntax = req.get('prelude_syntax')" in script
    assert "prelude_syntax.splitlines()" in script

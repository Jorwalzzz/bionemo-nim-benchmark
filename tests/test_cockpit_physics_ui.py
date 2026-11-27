"""
TDD verification tests for Task 8: Cockpit Interactive 3D Contacts, Multi-Pose Selector,
Plausibility Pills, Retro Tree, & CSP-Safe Action Delegation.
Copyright (C) 2026 Jorwalzzz.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_viewer3d_tracks_and_clears_contact_shapes_and_supports_pose_switching() -> None:
    viewer_js = (REPO_ROOT / "js" / "cockpit" / "viewer3d.js").read_text(encoding="utf-8")
    assert "focusContactIn3D" in viewer_js
    assert "selectDockedPose" in viewer_js
    assert "activeContactShapes" in viewer_js
    assert "removeShape" in viewer_js
    assert "removeLabel" in viewer_js


def test_ui_controls_renders_plausibility_contacts_and_retro_tree_safely() -> None:
    ui_js = (REPO_ROOT / "js" / "cockpit" / "ui-controls.js").read_text(encoding="utf-8")
    main_js = (REPO_ROOT / "js" / "cockpit" / "main.js").read_text(encoding="utf-8")
    api_js = (REPO_ROOT / "js" / "cockpit" / "api.js").read_text(encoding="utf-8")

    assert "retro-tree" in ui_js
    assert "pose_validation" in ui_js
    assert "interaction_contacts" in ui_js
    assert "data-action=\"focus-contact\"" in ui_js or "data-action='focus-contact'" in ui_js
    assert "data-action=\"select-docked-pose\"" in ui_js or "data-action='select-docked-pose'" in ui_js

    assert "select-docked-pose" in main_js
    assert "focus-contact" in main_js

    # Ensure zero inline event handlers were introduced in ui-controls templates
    assert "onclick=" not in ui_js

    # Ensure static fallback envelope supplies v2.3 deterministic schema keys
    assert "pose_validation" in api_js
    assert "route_tree" in api_js

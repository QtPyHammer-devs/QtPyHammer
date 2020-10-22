from QtPyHammer.ui.user_preferences import SettingsEditor


def test_settings_editor(qtbot):
    settings_editor = SettingsEditor()
    qtbot.addWidget(settings_editor)
    assert settings_editor.tabText(0) == "Theme"

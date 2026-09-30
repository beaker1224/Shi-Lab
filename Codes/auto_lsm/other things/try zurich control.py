from pywinauto import Application
import sys


app = Application(backend="uia").connect(
    title_re=".*Zurich.*"
)

window = app.top_window()

window.restore()
window.set_focus()

with open("zurich_controls.txt", "w", encoding="utf-8") as f:
    old_stdout = sys.stdout
    sys.stdout = f

    app.print_control_identifiers()

    sys.stdout = old_stdout
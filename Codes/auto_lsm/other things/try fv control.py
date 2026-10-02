try:
    from pywinauto import Desktop
    import sys
except ImportError:
    input("pywinauto is not installed. Please install it using 'pip install pywinauto' and try again.")
    sys.exit(1)

windows = Desktop(backend="uia").windows()

for window in windows:
    try:
        print(window.window_text())
    except:
        pass


fv = Desktop(backend="uia").window(
    title_re="OLYMPUS FV31S-SW"
)

fv.print_control_identifiers()

with open("fv_control_identifiers.txt", "w") as f:
    old_stdout = sys.stdout
    sys.stdout = f

    fv.print_control_identifiers()

    sys.stdout = old_stdout

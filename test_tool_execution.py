import webbrowser
import subprocess
import platform
import os

print("Testing open_url function...")
try:
    url = "https://youtube.com"
    print(f"Attempting to open: {url}")
    webbrowser.open(url)
    print("webbrowser.open called!")
except Exception as e:
    print(f"ERROR with webbrowser: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting open_file_or_app with notepad...")
try:
    if platform.system() == "Windows":
        print("Calling os.startfile('notepad')...")
        os.startfile("notepad")
    elif platform.system() == "Darwin":
        subprocess.call(["open", "-a", "TextEdit"])
    else:
        subprocess.call(["gedit"])
    print("Open app called!")
except Exception as e:
    print(f"ERROR opening app: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

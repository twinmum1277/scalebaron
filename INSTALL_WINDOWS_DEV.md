# Windows: Development Installation Guide

This guide is for anyone who wants to run the **development version** of ScaleBarOn on Windows (e.g. from a clone of the GitHub repo). It covers installing Python, dependencies, and the package in editable mode so you can run the latest code and make changes.

---

## Prerequisites

- **Python 3.8 or newer**  
  - Download from [python.org/downloads](https://www.python.org/downloads/).  
  - During setup, check **“Add Python to PATH”** so you can use `python` and `pip` from Command Prompt or PowerShell.

- **Git** (to clone the repo)  
  - Download from [git-scm.com/download/win](https://git-scm.com/download/win) if you don’t have it.

---

## 1. Clone the repository

Open **Command Prompt** or **PowerShell** and go to the folder where you keep projects. Then clone the repo:

```cmd
cd C:\Users\YourName\Documents
git clone https://github.com/twinmum1277/scalebaron.git
cd scalebaron
```

(Use your actual path and the correct GitHub URL if the repo is under a different org or fork.)

---

## 2. Create a virtual environment (recommended)

Using a virtual environment keeps this project’s dependencies separate from the rest of your system.

```cmd
python -m venv venv
venv\Scripts\activate
```

Your prompt should show `(venv)`. All following commands assume this environment is activated.

---

## 3. Install dependencies

From the project root (the `scalebaron` folder that contains `requirements.txt` and `setup.py`):

```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:

- numpy, pandas, matplotlib, openpyxl, Pillow (PIL), cairosvg, scipy, requests  

If any package fails (e.g. `cairosvg` on some Windows setups), see [Troubleshooting](#troubleshooting) below.

---

## 4. Install the package in development (editable) mode

So the app runs from your local source and picks up code changes without reinstalling:

```cmd
pip install -e .
```

This uses `setup.py` and installs the `scalebaron`, `muaddata`, and `download_test_elemental_images` commands.

---

## 5. Run the application

With the virtual environment still activated:

**ScaleBarOn (main GUI):**

```cmd
scalebaron
```

**Muad'Data:**

```cmd
muaddata
```

**Download test elemental images:**

```cmd
download_test_elemental_images
```

Alternatively you can run the main app as a module:

```cmd
python -m scalebaron.scalebaron
```

---

## Quick reference: full setup from scratch

```cmd
cd C:\Users\YourName\Documents
git clone https://github.com/twinmum1277/scalebaron.git
cd scalebaron
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
scalebaron
```

---

## Troubleshooting

- **“python” or “pip” not found**  
  - Reinstall Python and ensure **“Add Python to PATH”** is checked, or use the full path to `python.exe` (e.g. `C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe -m venv venv`).  
  - You can also try `py -m venv venv` and `py -m pip install -r requirements.txt` if the Python Launcher is installed.

- **Permission or path length errors**  
  - Run Command Prompt or PowerShell as a normal user (no need for “Run as administrator” for a user install). If you hit path length limits, clone the repo to a short path (e.g. `C:\dev\scalebaron`).

- **`cairosvg` fails to install or import**  
  - ScaleBarOn may still run if it doesn’t use SVG in your workflow. You can try installing the rest and run the app; if a specific feature fails, we can document a minimal install without `cairosvg` or suggest a Windows-friendly alternative.

- **Changes to the code don’t appear**  
  - You must have run `pip install -e .` from the repo root so the package is in editable mode. After that, just close and restart the app (e.g. run `scalebaron` again) to see changes.

- **Antivirus or Windows Defender blocking scripts**  
  - If `venv\Scripts\activate` or running `scalebaron` is blocked, add an exclusion for the project folder or allow the script in the security prompt.

---

## Summary

| Step              | Command / action                          |
|-------------------|-------------------------------------------|
| Clone repo        | `git clone <repo-url>` then `cd scalebaron` |
| Create venv       | `python -m venv venv`                     |
| Activate venv     | `venv\Scripts\activate`                   |
| Install deps      | `pip install -r requirements.txt`         |
| Install dev pkg   | `pip install -e .`                        |
| Run ScaleBarOn    | `scalebaron`                              |

After this, you’re on the development version: dependencies are installed and the app runs from your local clone.

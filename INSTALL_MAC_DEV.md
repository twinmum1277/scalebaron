# macOS: Development Installation Guide

This guide is for anyone who wants to run the **development version** of ScaleBarOn and Muad'Data on macOS (e.g. from a clone of the GitHub repo). It covers installing Python, dependencies, and the package in editable mode so you can run the latest code and make changes.

---

## Prerequisites

- **Python 3.8 or newer**  
  - Download from [python.org/downloads](https://www.python.org/downloads/) (macOS installer), or install via Homebrew: `brew install python@3.11` (or another version).  
  - On macOS you’ll usually run `python3` and `pip3`; the commands below use `python3` and `pip` (pip often points to the same Python as `python3` after setup).

- **Git** (to clone the repo)  
  - Often pre-installed with Xcode Command Line Tools (`xcode-select --install`), or install via [git-scm.com](https://git-scm.com/download/mac) or Homebrew: `brew install git`.  
  - A **GitHub account is not required** to clone this public repo; the clone command works without logging in.

---

## 1. Clone the repository

Open **Terminal** and go to the folder where you keep projects. Then clone the repo:

```bash
cd ~/Documents
git clone https://github.com/twinmum1277/scalebaron.git
cd scalebaron
```

(Use your actual path and the correct GitHub URL if the repo is under a different org or fork.)

---

## 2. Create a virtual environment (recommended)

Using a virtual environment keeps this project’s dependencies separate from the rest of your system.

```bash
python3 -m venv venv
source venv/bin/activate
```

Your prompt should show `(venv)`. All following commands assume this environment is activated.

---

## 3. Install dependencies

From the project root (the `scalebaron` folder that contains `requirements.txt` and `setup.py`):

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:

- numpy, pandas, matplotlib, openpyxl, Pillow (PIL), cairosvg, scipy, requests  

If any package fails (e.g. `cairosvg` on some setups), see [Troubleshooting](#troubleshooting) below.

---

## 4. Install the package in development (editable) mode

So the app runs from your local source and picks up code changes without reinstalling:

```bash
pip install -e .
```

This uses `setup.py` and installs the `scalebaron`, `muaddata`, and `download_test_elemental_images` commands.

---

## 5. Run the application

With the virtual environment still activated:

**ScaleBarOn (main GUI):**

```bash
scalebaron
```

**Muad'Data:**

```bash
muaddata
```

**Download test elemental images:**

```bash
download_test_elemental_images
```

Alternatively you can run the main app as a module:

```bash
python -m scalebaron.scalebaron
```

---

## Quick reference: full setup from scratch

```bash
cd ~/Documents
git clone https://github.com/twinmum1277/scalebaron.git
cd scalebaron
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
scalebaron
```

---

## Troubleshooting

- **“python3” or “pip” not found**  
  - Install Python from [python.org](https://www.python.org/downloads/) or run `brew install python@3.11` (or another version).  
  - Use `python3` and `pip3` explicitly if your system still has an older or different default `python`.

- **“xcrun: error: invalid active developer path”**  
  - Install the Xcode Command Line Tools: run `xcode-select --install` in Terminal and follow the prompts.

- **Permission errors**  
  - Don’t use `sudo` for pip installs into a virtual environment; run `pip install` with the venv activated. If you get permission errors outside the venv, use a venv (steps above) or install Python via Homebrew under your user.

- **`cairosvg` fails to install or import**  
  - You may need `cairo` and `pkg-config` first: `brew install cairo pkg-config`, then `pip install -r requirements.txt` again.  
  - ScaleBarOn may still run if it doesn’t use SVG in your workflow; if a specific feature fails, we can document a minimal install without `cairosvg`.

- **Changes to the code don’t appear**  
  - You must have run `pip install -e .` from the repo root so the package is in editable mode. After that, just close and restart the app (e.g. run `scalebaron` or `muaddata` again) to see changes.

- **Dock icon shows Python instead of app icon**  
  - Run the app from Terminal (e.g. `scalebaron` or `muaddata`) rather than from an IDE; the custom dock icon is set when the app starts. If you run from an IDE, the IDE’s process may own the dock icon.

- **Gatekeeper or “unidentified developer”**  
  - If you run a script or binary and macOS blocks it, you can allow it in **System Settings → Privacy & Security** or right‑click the app/script and choose **Open** once.

---

## Summary

| Step              | Command / action                            |
|-------------------|---------------------------------------------|
| Clone repo        | `git clone <repo-url>` then `cd scalebaron` |
| Create venv       | `python3 -m venv venv`                      |
| Activate venv     | `source venv/bin/activate`                  |
| Install deps      | `pip install -r requirements.txt`           |
| Install dev pkg   | `pip install -e .`                          |
| Run ScaleBarOn    | `scalebaron`                                |
| Run Muad'Data     | `muaddata`                                  |

After this, you’re on the development version: dependencies are installed and the apps run from your local clone.

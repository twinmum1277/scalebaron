import os
import requests
import tkinter as tk
from tkinter import filedialog

def download_file(url, dest_folder):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    # Replace %20 with space in the filename
    filename = url.split('/')[-1].replace('%20', ' ')
    local_filename = os.path.join(dest_folder, filename)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"Downloaded {local_filename}")

def main():
    # Use a file dialog to select the output directory
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    output_dir = filedialog.askdirectory(title="Select directory to download files into")
    root.destroy()

    if not output_dir:
        print("No directory selected. Exiting.")
        return

    # List of files to download from GitHub (example URLs)
    github_files = []
    for element in ["Ca44","Fe56","Mn55","Na23","Se80","Zn66"]:
        for name in ['LetoII','duncan', 'paul']:
            github_files.append(f"https://github.com/twinmum1277/scalebaron/raw/refs/heads/main/test/testdata/{name}%20{element}_ppm%20matrix.xlsx")
            
    os.makedirs(os.path.join(output_dir,"testdata"),exist_ok=True)

    for url in github_files:
        download_file(url, os.path.join(output_dir,"testdata"))

if __name__ == "__main__":
    main()
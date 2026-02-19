# -*- coding: utf-8 -*-
"""
Custom modal dialogs that display the app icon (instead of the Python logo).
Drop-in replacements for tkinter.messagebox.showinfo, showerror, showwarning, askyesno.
Uses Toplevel windows so they inherit iconphoto() from the root.
"""
import tkinter as tk
from tkinter import ttk


def _show(parent, title, message, icon_type='info'):
    """Show a modal message dialog. icon_type: 'info', 'error', 'warning'."""
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(False, False)

    f = ttk.Frame(dialog, padding=20)
    f.pack(fill=tk.BOTH, expand=True)

    lbl = ttk.Label(f, text=message, wraplength=400, justify=tk.LEFT)
    lbl.pack(fill=tk.X, pady=(0, 15))

    def ok():
        dialog.destroy()

    btn = ttk.Button(f, text="OK", command=ok, width=10)
    btn.pack(anchor=tk.CENTER)
    btn.focus_set()
    dialog.bind("<Return>", lambda e: ok())
    dialog.bind("<Escape>", lambda e: ok())
    dialog.protocol("WM_DELETE_WINDOW", ok)

    dialog.geometry(f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 80}")
    dialog.wait_window()


def _ask_yesno(parent, title, message):
    """Show a modal Yes/No dialog. Returns True for Yes, False for No."""
    result = [None]

    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.resizable(False, False)

    f = ttk.Frame(dialog, padding=20)
    f.pack(fill=tk.BOTH, expand=True)

    lbl = ttk.Label(f, text=message, wraplength=400, justify=tk.LEFT)
    lbl.pack(fill=tk.X, pady=(0, 15))

    btn_f = ttk.Frame(f)
    btn_f.pack(anchor=tk.CENTER)

    def yes():
        result[0] = True
        dialog.destroy()

    def no():
        result[0] = False
        dialog.destroy()

    ttk.Button(btn_f, text="Yes", command=yes, width=8).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_f, text="No", command=no, width=8).pack(side=tk.LEFT, padx=5)
    dialog.bind("<Return>", lambda e: yes())
    dialog.bind("<Escape>", lambda e: no())
    dialog.protocol("WM_DELETE_WINDOW", no)

    dialog.geometry(f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 80}")
    dialog.wait_window()
    return result[0]


def showinfo(parent, title, message):
    _show(parent, title, message, 'info')


def showerror(parent, title, message):
    _show(parent, title, message, 'error')


def showwarning(parent, title, message):
    _show(parent, title, message, 'warning')


def askyesno(parent, title, message):
    return _ask_yesno(parent, title, message)

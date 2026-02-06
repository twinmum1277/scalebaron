# Scalebaron vs Muad'data – what causes the halo and grey box

## Buttons (e.g. "Load Red", "Load Green", "Input", "Pixel Sizes")

| | **Scalebaron** | **Muad'data (before fix)** |
|--|----------------|----------------------------|
| **Widget** | `ttk.Button(...)` | `tk.Button(...)` |
| **Effect** | Themed, flat look; no visible border/halo | Classic tk: 2px border + relief → "lighter halo" around the label |

Scalebaron uses **ttk.Button** for all text buttons (Input, Output, Pixel Sizes, Refresh Progress Table, 💾 Matrix, etc.). It uses **tk.Button** only for **icon** buttons (image=...) where it sets `padx=2, pady=8, bg='#f0f0f0', relief='raised'`.

Muad'data uses **tk.Button** for almost everything (Load Matrix, Load Red/Green/Blue, View Map, Save PNG, Add, Clear, etc.). Classic **tk.Button** always draws a border and relief, which shows as the halo.

## Input fields (e.g. "Pixel size (µm)", "Length (µm)", "Slider max")

| | **Scalebaron** | **Muad'data (before fix)** |
|--|----------------|----------------------------|
| **Widget** | `ttk.Entry(...)` | `tk.Entry(...)` |
| **Effect** | Themed, flat field; no extra box | Classic tk: inset border + background → "light grey box" around the text |

Scalebaron uses **ttk.Entry** for Pixel Size, Scale bar length, Rows, Scale max, etc. Muad'data uses **tk.Entry** for pixel size, scale length, slider max, and RGB entries. Classic **tk.Entry** has a visible border and often a different background, which looks like a light grey box.

## Summary

- **Halo around buttons** = Muad'data uses `tk.Button`; Scalebaron uses `ttk.Button` for text buttons.
- **Grey box around inputs** = Muad'data uses `tk.Entry`; Scalebaron uses `ttk.Entry`.

Fix: use **ttk.Button** for every text button that doesn’t need a custom background (e.g. Load R/G/B, Load Matrix, View Map, Add, Clear, …), and use **ttk.Entry** for all single-line text/numeric fields. Keep **tk.Button** only where you set `bg=` (e.g. scale bar "Pick", channel "Color", Map Math green, Select region blue, Clear Data red, Ratio map purple).

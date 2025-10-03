---
title: "ScaleBarOn and Muad'Data: Simple Python tools for Elemental Imaging Data Visualization and Comparative Scaling."
tags:
  - elemental imaging
  - LA-ICP-TOF-MS
  - image processing
  - Python
  - scaling
authors:
  - name: Tracy Punshon
    orcid: 0000-0003-0782-446X
    affiliation: 1
  - name: Joshua Levy
    orcid: 0000-0001-8050-1291
    affiliation: 2
affiliations:
  - name: Biomedical National Elemental Imaging Resource, Dartmouth College, Hanover, NH, USA
    index: 1
  - name: Cedars Sinai Medical Center, Los Angeles, CA, USA
    index: 2
date: 2025-05-01
bibliography: paper.bib
---

# Summary  

Elemental imaging techniques, e.g., laser ablation inductively coupled plasma time of flight mass spectrometry (LA-ICP-TOF-MS) or X-ray fluorescence microscopy (XFM), collect spatially resolved elemental data, consisting of multiple channels (or elements) and the coordinates (X and Y values) for each pixel. For interoperability, elemental imaging data is therefore reducible to matrix format data files. Originating in geochemistry, elemental imaging has become an important tool in the biological sciences, where experiments require between-sample comparisons and replication. The Biomedical National Elemental Imaging Resource (BNEIR) operates as a shared resource that enables users in the biomedical sciences to gain rapid access to elemental imaging, offering analysis via LA-ICP-TOF-MS. In general, elemental imaging software tends to work with a single multi-channel data file at a time, and has technique-specific functions for peak fitting, background correction and quantification to optimize the final data output. In our experience of operating an elemental imaging shared resource, where quality control and quantification are carried out by resource staff prior to releasing data, users need intuitive stand-alone image manipulation software modules that specifically allow them to show multiple maps on the same quantitative (parts per million, ppm or counts per second, CPS) and spatial scale, so they can quick assess their experimental results. 

# Statement of Need

There are many software applications for manipulating and visualizing LA-ICP-MS, SXRF, and XRF data [@Weiskirchen2019]. To our knowledge, only two - The MicroAnalysis Toolkit [@Webb2011] and HDIP from Teledyne can load multiple datasets for comparison. With each LA-ICP-TOF-MS data file in the GB range, loading the entire multi-channel dataset rapidly becomes impractical for biological experiments that can have up to 20 or more specimens for comparison. Additionally, loading fluorescence images for coregistration can triple file sizes, making whole experiments too computationally heavy for users to work with. Experiences at the Biomedical National Elemental Imaging Resource (BNEIR), an elemental imaging shared resource, uncovered a need for simple, *technique-independent* intuitive data visualization tools to compare multiple maps on the same abundance and spatial scale and to explore single imaging data files. 

**ScaleBarOn and Muad'Data** are lightweight, Python general user interfaces (GUIs) that work with Microsoft Excel matrix files exported from technique-specific software that were created in direct response to BNEIR user needs. 

Prior to developing ScaleBarOn, a typical workflow for producing a scaled elemental image series for a complete experiment would involve opening individual datasets, collecting upper or 99th percentile pixel values for each element (8-10 elements on average), deciding an appropriate scaling value or strategy for each element, and then opening data sets again to apply scaling values, and save individual image files for compilation in a separate application such as Microsoft Power Point. This was a time consuming process for biological experiments which can comprise >20 data sets, with additional or re-run samples necessitating repeat processing.

ScaleBarOn produces a single scaled and labeled composite image. It iterates through matrix files, calculates the 99th percentile pixel value for each element and produces a summary table as a .csv file, accepting user input on scaling and organization of the composite. Users may also set their own scaling value and choose a color scheme from a range of visually uniform MatPlotLib options. ScaleBarOn also produces a set of individual .png files, plus the unified color bar for users to assemble their own composite, for instance if sample rotation is needed to make sure specimens are aligned with respect to their anatomic features. ScaleBarOn labels specimens and optionally will add an element and unit label. Future versions will implement guidance on appropriate scaling strategies, such a log or empirical cumulative distribution function scale, to avoid data loss associated with large dynamic ranges of elemental concentrations, helpful hints that appear when users hover over buttons, and batch processing that will generate composites for all elements using default settings. 

Summary of ScaleBarOn's functions:

- Consistent application of spatial and color scale bars across multiple datasets.
- Batch image generation with automatic detection of unit types (ppm or CPS).
- Support for composite figure layouts that preserve biological replicate groupings.
- Optional support for variable pixel sizes and log scaling.

Muad'Data Element Viewer tab produces a single scaled and labeled single-element image. A dynamic data visualization window above the scale bar shows the frequency histogram of the data, allowing users to constrain the maximum value, distributing data bins in the color scheme to the highest frequency data, rather than outliers. The scaling is dynamic and users sliders to change the maximum value. Like ScaleBarOn, users can choose from the full range of MatPlotlib color schemes. The Red-Green-Blue (RGB) Overlay tab allows users to load three different element matrix files and manipulation and assign each its own color channel, using the same intuitive dynamic scaling. It generates the three color legend using user-selected colors for each channel. Both tabs allow placement of a spatial scale bar.

Summary of Muad'Data functions:

- Application of spatial and color scale bars on a single data set for one element
- Application of spatial and three-color overlay scale bars on a single data set for three elements
- Option to constrain the maximum value for outliers
- Ability to perform simple mathematical functions on each pixel and save the resultant image output.


ScaleBarOn and Muad'Dada are not intended to replace sophisticated software packages needed to fit spectra, perform background correction, normalization or quantify elemental data from detector counts per second to parts per million, but rather to be user-friendly stand-alone composite and single image generator modules that work with final quantified data sets independent of elemental imaging technique. They are meant to bridge the knowledge gap that exists between users of advance elemental imaging techniques and those that operate and develop them.

# Artificial Intelligence Use and Provenance Statement
In developing ScaleBarOn and its GUI, we occasionally used large language models (LLMs, e.g., ChatGPT) as programming assistants. Their role was limited to:

- Syntax help and boilerplate: generating small snippets of Python/Tkinter code (e.g., GUI layout scaffolding, file dialog setup) that were   then adapted and integrated manually.
- Debugging assistance: interpreting error messages and suggesting corrections, which were verified and implemented by the authors.
- Documentation and formatting: producing draft explanations or docstring templates, which were edited by the authors for accuracy and clarity.

All scientific logic, algorithm design, data workflows, and domain-specific features (e.g., percentile scaling of elemental maps, pixel-size metadata handling, composite image layouts, and integration with matrix file structures) were conceived, implemented, and tested by the authors. We have validated and tested all code to ensure correctness, reproducibility, and maintainability. No AI-generated code was included without human review and adaptation.

# Citations

# Acknowledgements

The Biomedical National Elemental Imaging Resource (BNEIR) is funded by the National Institute of General Medical Sciences grant # 1R24GM141194. 

# Installation

To install ScaleBarOn:

```bash
pip install scalebaron
```

To install the latest version:

```bash
pip install git+https://github.com/twinmum1277/scalebaron
```

# Running the GUI

To run ScaleBaron, call:

```bash
scalebaron
```

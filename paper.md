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

Elemental imaging techniques (e.g., laser ablation inductively coupled plasma time of flight mass spectrometry (LA-ICP-TOF-MS) or synchrotron X-ray fluorescence (SXRF)) collect spatially resolved elemental data in the form of maps (matrix format files). Originating in geochemistry, these techniques have become more common in the biological sciences, where experiments rely on between-sample comparisons. The Biomedical National Elemental Imaging Resource (BNEIR) operates as a shared resource for users in the biomedical sciences to gain rapid access to elemental imaging, using LA-ICP-TOF-MS analysis. Available elemental imaging software has incredibly rich functionality for generating as well manipulating elemental imaging data that deter inexperienced users, who need intuitive stand-alone image manipulation and comparison modules that show multiple maps on the same quantitative (parts per million, ppm) and spatial scale. 

# Statement of Need

There are many software applications for manipulating and visualizing LA-ICP-MS, SXRF, and XRF data [@Weiskirchen2019]. To our knowledge, only two - The MicroAnalysis Toolkit [@Webb2011] and HDIP from Teledyne can load multiple datasets for comparison. With each LA-ICP-TOF-MS data file in the GB range, this rapidly becomes impractical for biological experiments, where data sets can have up to 20 or more specimens for direct comparison. Encouraging users new to elemental imaging to use functionally rich X-ray software to visualize LA-ICP-TOF-MS data has been unsuccessful. Experiences at the Biomedical National Elemental Imaging Resource (BNEIR), a elemental imaging shared resource uncovered a need for simple, *technique-independent* intuitive data visualization tools to compare multiple maps on the same abundance and spatial scale and to explore single imaging data files. 

**ScaleBarOn and Muad'Data** are lightweight, Python general user interfaces (GUIs) that work with Microsoft Excel matrix files exported from technique-specific software that were created in direct response to BNEIR user needs. 

Prior to developing ScaleBarOn, a typical workflow for producing a scaled elemental image series would involve opening individual datasets, collecting upper or 99th percentile pixel values for each element for 8-10 elements on average, deciding an appropriate scaling value or strategy for each element, opening data sets a second time to apply scaling values, saving individual image files for compilation in a separate application such as Microsoft Power Point. This was a time consuming process for biological experiments which can comprise >20 data sets, with additional or re-run samples necessitating repeat processing.

ScaleBarOn produces a single scaled and labeled composite image. It iterates through matrix files, calculates the 99th percentile pixel value for each element and produces a summary table as a .csv file, accepting user input on scaling and organization of the composite. Users may also set their own scaling value and choose a color scheme from a range of visually uniform MatPlotLib options. ScaleBarOn also produces a set of individual .png files, plus the unified color bar for users to assemble their own composite, for instance if sample rotation is needed. Future versions of the code will implement guidance on appropriate scaling strategies, such a log or empirical cumulative distribution function scale, to avoid data loss associated with large dynamic ranges of elemental concentrations. 

Summary of ScaleBarOn's functions:

- Consistent application of spatial and color scale bars across multiple datasets.
- Batch image generation with automatic detection of unit types (ppm or CPS).
- Support for composite figure layouts that preserve biological replicate groupings.
- Optional support for variable pixel sizes, ECDF-based scaling, and metadata-aware workflows.

Muad'Data Element Viewer tab produces a single scaled and labeled single-element image. A dynamic data visualization window above the scale bar shows the frequency histogram of the data, allowing users to constrain the maximum value, distributing data bins in the color scheme to the highest frequency data, rather than outliers. The scaling is dynamic and users sliders to change the maximum value. Users can choose from the full range of Mat Plot lib color schemes to show their data. The Red-Green-Blue (RGB) Overlay tab allows users to load three different element matrix files and manipulation and assign each its own color channel, using the same intuitive dynamic scaling. It generates the three color legend using user-selected colors for each channel. Both tabs allow placement of a spatial scale bar.

Summary of Muad'Data functions:

- Application of spatial and color scale bars on a single data set for one element
- Application of spatial and three-color overlay scale bars on a single data set for three elements
- Option to constrain the maximum value for outliers


ScaleBarOn and Muad'Dada are not intended to replace sophisticated software packages needed to fit spectra, background correct, normalize or quantify elemental data from detector counts per second to parts per million, but rather to be user-friendly composite and single image generator modules that work with final quantified data sets independent of elemental imaging technique.  

# Citations

# Acknowledgements

The Biomedical National Elemental Imaging Resource (BNEIR) is funded by the National Institute of General Medical Sciences grant # 1R24GM141194. We acknowledge the assistance of AI tools (e.g., ChatGPT) in drafting and refining documentation for this submission. All software and editorial decisions were made by the author.

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
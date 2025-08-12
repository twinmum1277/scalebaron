---
title: 'ScaleBarOn: A Python Tool for Scaling Multiple Elemental Maps'
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

Elemental imaging techniques (e.g., laser ablation inductively coupled plasma time of flight mass spectrometry (LA-ICP-TOF-MS) or synchrotron X-ray fluorescence (SXRF)) collect spatially resolved elemental data in the form of maps. These techniques are becoming more common in biological sciences, where experiments use replicated, between-sample comparisons. The Biomedical National Elemental Imaging Resource (BNEIR) operates as a shared resource for users in the biomedical sciences to gain rapid access to elemental imaging, offering LA-ICP-TOF-MS analysis to almost 40 users nationwide. Users generally are new to elemental imaging, and most, if not all, are unfamiliar with software designed to generate or manipulate elemental images. Giving users a meaningful first look at their results therefore requires preparing a data summary that shows maps on the same quantitative (parts per million, ppm) and spatial scale. 

# Statement of Need

There are many software applications for manipulating and visualizing LA-ICP-MS, SXRF, and XRF data [@Weiskirchen2019]. To our knowledge, only two - The MicroAnalysis Toolkit [@Webb2011] and HDIP from Teledyne can load multiple datasets for comparison. With each LA-ICP-TOF-MS data set in the GB range, this rapidly becomes impractical for biological experiments. Encouraging users new to elemental imaging to use X-ray software to visualize LA-ICP-TOF-MS data has been unsuccessful. Users need a simple, *technique-independent* data visualization tool to compare multiple maps on the same abundance and spatial scale. 

Prior to developing ScaleBarOn, a typical workflow for producing a scaled elemental image series would involve opening individual datasets, collecting upper or 99th percentile pixel values for each element for 8-10 elements on average, deciding an appropriate scaling value or strategy for each element, opening data sets a second time to apply scaling values, saving individual image files for compilation in a separate application such as Microsoft Power Point. This was a time consuming process for biological experiments which can comprise >20 data sets, with additional or re-run samples necessitating repeat processing.

**ScaleBarOn** is a lightweight, command-line Python tool that works with Microsoft Excel matrix files exported from technique-specific software to produce a single scaled and labeled composite image. It iterates through matrix files, calculates the 99th percentile pixel value for each element and produces a summary table as a .csv file, accepting user input on scaling and organization of the composite. Users may also set their own scaling value and choose a color scheme from a range of visually uniform MatPlotLib options. ScaleBarOn also produces a set of individual .png files, plus the unified color bar for users to assemble their own composite, for instance if sample rotation is needed. Future versions of the code will implement guidance on appropriate scaling strategies, such a log or empirical cumulative distribution function scale, to avoid data loss associated with large dynamic ranges of elemental concentrations. 

ScaleBarOn is not intended to replace the sophisticated software packages needed to fit spectra, background correct, normalize or quantify elemental data from detector counts per second to parts per million, but rather to be a user-friendly composite image generator module that works with final quantified data sets independent of elemental imaging technique.  

To summarize ScaleBarOn's functions:

- Consistent application of spatial and color scale bars across multiple datasets.
- Batch image generation with automatic detection of unit types (ppm or CPS).
- Support for composite figure layouts that preserve biological replicate groupings.
- Optional support for variable pixel sizes, ECDF-based scaling, and metadata-aware workflows.

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
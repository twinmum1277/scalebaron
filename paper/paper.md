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
Bibliography: paper.bib
---

# Summary

Elemental imaging techniques (e.g., laser ablation inductively coupled plasma time of flight mass spectrometry (LA-ICP-TOF-MS) or synchrotron X-ray fluorescence (SXRF)) collect spatially resolved elemental data in the form of maps. These techniques are becoming more common in biological sciences, where experiments use replicated, between-sample comparisons. The Biomedical National Elemental Imaging Resource (BNEIR) operates as a shared resource for users in the biomedical sciences to gain rapid access to elemental imaging, offering LA-ICP-TOF-MS analysis to almost 40 users nationwide. Users generally are new to elemental imaging, and most, if not all, are unfamiliar with software designed to generate or manipulate elemental images. Giving users a meaningful first look at their results therefore requires preparing a data summary that shows maps on the same quantitative (parts per million, ppm) and spatial scale. 

# Statement of Need

There are many software applications for manipulating and visualizing LA-ICP-MS, SXRF, and XRF data (Weiskirchen et al., 2019) [@Weiskirchen2019]. To our knowledge, only one (The MicroAnalysis Toolkit)(Webb, 2011) [@Webb2011] has the capability to load multiple datasets for comparison. Encouraging users unfamiliar with elemental imaging to use X-ray software to visualize their LA-ICP-MS data has so far been resoundingly unsuccessful. Users need a simple, *technique-independent* tool to visually compare multiple maps on the same abundance and spatial scale so they can make preliminary observations. 

Prior to development of ScaleBarOn, a typical workflow for producing a scaled elemental imaging summary would involve opening every individual dataset (typically 2-4 GB each), collecting 99th percentile values for each element (typically 8-10 elements), deciding on an appropriate scaling value/strategy for each element, then opening all datasets a second time to apply the values, save .jpgs or .pngs for assembly in an application such as Microsoft Power Point. This would typically take several days for larger data sets comprising 20+ samples, with additional or re-run samples necessitating a repeat process.

**ScaleBarOn** is a lightweight, command-line Python tool that works with Microsoft Excel matrix files exported from technique-specific software to produce a single scaled and labeled composite image. It iterates through matrix files, calculates the 99th percentile pixel value for each element and produces a summary table as a .csv file, asks for user input on the scaling and organization of the composite. Users may also set their own scaling value and choose their own color scheme from a range of visually uniform MatPlotLib options. ScaleBarOn also produces a set of labeled and unlabeled individual .png files, plus the unified color bar for users to assemble their own figures. Future versions of the code will implement guidance on appropriate scaling strategies, such a log or empirical cumulative distribution function scale, to avoid the data loss associated with large dynamic ranges of elemental concentrations. 

ScaleBarOn is not intended to replace sophisticated software packages needed to fit spectra, background correct, normalize or quantify elemental data from detector counts per second in to parts per million, but rather to be a user-friendly scaled image generator that works with the final quantified datasets independent of elemental imaging technique.  

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
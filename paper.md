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
affiliations:
  - name: Dartmouth College
    index: 1
date: 2025-04-30
---

# Summary

Elemental imaging techniques (e.g., laser ablation inductively coupled plasma time of flight mass spectrometry (LA-ICP-TOF-MS) or synchrotron X-ray fluorescence (SXRF)) collect spatially resolved elemental data in the form of maps. These techniques are becoming more common in biological sciences, where experiments use replicated, between-sample comparisons. While the methods of ionization and detection differ across techniques, the final quantified data is the same: a matrix of values with X and Y coordinates for each mass or channel.  

**ScaleBarOn** is a lightweight, command-line Python tool designed to visualize elemental imaging datasets across multiple samples. It enables batch processing of matrix-formatted elemental data (e.g., ppm or counts per second), applies visually uniform color scaling based on calculated 99th percentiles, and adds spatial scale bars and sample identifiers to a user-defined composite image. It supports customizable layout rules based on biological replicates, ensuring comparability and clarity in scientific communication.

# Statement of Need

There are many software applications for LA-ICP-MS, SXRF, and XRF data (Weiskerchen et al., 2019). Only one (the excellent Sam's MicroAnalysis Toolkit) has the capability to load multiple datasets for comparison, but users at the Biomedical National Elemental Imaging Resource (BNEIR) working with LA-ICP-MS data are unwilling to learn X-ray software to interact with their data. Users need a simple, technique-independent tool to visually compare data on the same abundance and spatial scale.

ScaleBarOn fills this gap by enabling:

- Consistent application of spatial and color scale bars across multiple datasets.
- Batch image generation with automatic detection of unit types (ppm or CPS).
- Support for composite figure layouts that preserve biological replicate groupings.
- Optional support for variable pixel sizes, ECDF-based scaling, and metadata-aware workflows.

ScaleBarOn works with matrix files in the file format .xlsx. It is useful for researchers in biomedicine, molecular genetics, or environmental sciences who routinely compare dozens of samples in an experiment and need to compare them on an equal visual footing.

# Installation

To install ScaleBarOn:

```bash
pip install scalebaron
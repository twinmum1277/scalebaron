"""
HDF5 session reader for laser-imaging exports.

Reads session metadata (samples, elements, imaging model, pixel geometry) and
reconstructs spot-resolution rasters. Supports CellSpace first; FromSelections
follows the same dispatch pattern.
"""

from __future__ import annotations

import base64
import json
import math
import struct
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

try:
    import h5py
except ImportError:  # pragma: no cover - exercised via tests when h5py installed
    h5py = None

IMAGING_PLUGIN = "UIPlugins/Imaging"
SELECTION_GROUPS = "SelectionGroups"
OUTPUTS = "Outputs"
INDEX_TIME = "Special/IndexTime"

SAMPLE_GROUP_TYPE = "Sample"
SKIP_GROUP_TYPES = frozenset({"Reference Material", "Baseline"})


class ImagingModel(str, Enum):
    CELLSPACE = "CellSpace"
    FROM_SELECTIONS = "FromSelections"
    UNKNOWN = "Unknown"


@dataclass
class SampleGeometry:
    name: str
    n_selections: int
    spot_width_um: float | None = None
    spot_height_um: float | None = None
    scan_speed_um_s: float | None = None
    pixel_size_x_um: float | None = None
    pixel_size_y_um: float | None = None
    grid_rows: int | None = None
    grid_cols: int | None = None


@dataclass
class SessionMetadata:
    path: str
    imaging_model: ImagingModel
    active_group: str | None = None
    physical_size_um: tuple[float, float] | None = None
    pixel_grid: tuple[int, int] | None = None
    physical_min_um: tuple[float, float] | None = None
    cell_space_placement: str | None = None
    samples: list[SampleGeometry] = field(default_factory=list)
    ppm_channels: list[str] = field(default_factory=list)
    cps_channels: list[str] = field(default_factory=list)
    channels_by_sample: dict[str, list[str]] = field(default_factory=dict)


def _require_h5py():
    if h5py is None:
        raise ImportError(
            "h5py is required for HDF5 session import. Install with: pip install h5py"
        )


def _as_str(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _load_json_attr(group: "h5py.Group", key: str) -> dict | None:
    if key not in group.attrs:
        return None
    return json.loads(_as_str(group.attrs[key]))


def _decode_qt_size(b64_value: str) -> tuple[int, int]:
    raw = base64.b64decode(b64_value)
    return struct.unpack(">ii", raw)


def _decode_qt_sizef(b64_value: str) -> tuple[float, float]:
    raw = base64.b64decode(b64_value)
    return struct.unpack(">dd", raw)


def _parse_imaging_model(value: str | None) -> ImagingModel:
    if not value:
        return ImagingModel.UNKNOWN
    try:
        return ImagingModel(value)
    except ValueError:
        return ImagingModel.UNKNOWN


def _element_from_channel(channel: str, unit: str) -> str | None:
    suffix = f"_{unit}"
    if channel.endswith(suffix):
        return channel[: -len(suffix)]
    return None


def _median_step(values: list[float]) -> float | None:
    uniq = sorted(set(values))
    if len(uniq) < 2:
        return None
    diffs = [uniq[i + 1] - uniq[i] for i in range(len(uniq) - 1) if uniq[i + 1] > uniq[i]]
    if not diffs:
        return None
    return float(np.median(diffs))


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _microns_per_cell(imaging_global: dict) -> float:
    ppm = _float_or_none(imaging_global.get("pixelsPerMicron"))
    if ppm and ppm > 0:
        return 1.0 / ppm
    if imaging_global.get("physicalSize") and imaging_global.get("pixelSize"):
        pw, ph = _decode_qt_sizef(imaging_global["physicalSize"])
        cw, ch = _decode_qt_size(imaging_global["pixelSize"])
        if cw > 0 and ch > 0:
            return ((pw / cw) + (ph / ch)) / 2.0
    return 1.0


def _fill_cellspace_grid(
    selections: list[dict],
    index_time: np.ndarray,
    values: np.ndarray,
    origin_x: float,
    origin_y: float,
    um: float,
    n_rows: int,
    n_cols: int,
) -> np.ndarray:
    grid = np.full((n_rows, n_cols), np.nan, dtype=float)
    for selection in selections:
        props = selection.get("Properties") or {}
        coords = props.get("Coords") or []
        if len(coords) < 2:
            continue
        x0, y0 = float(coords[0][0]), float(coords[0][1])
        x1, y1 = float(coords[1][0]), float(coords[1][1])
        start = float(selection.get("StartTime", 0))
        end = float(selection.get("EndTime", start))
        i0 = int(np.searchsorted(index_time, start))
        i1 = int(np.searchsorted(index_time, end, side="right"))
        if i1 <= i0:
            continue
        segment = values[i0:i1]
        n_pts = len(segment)
        for k, value in enumerate(segment):
            t = k / max(n_pts - 1, 1)
            x = x0 + t * (x1 - x0)
            y = y0 + t * (y1 - y0)
            row = int(round((y - origin_y) / um))
            col = int(round((x - origin_x) / um))
            if 0 <= row < n_rows and 0 <= col < n_cols:
                grid[row, col] = float(value)
    return grid


def _local_grid_bounds(
    selections: list[dict],
    index_time: np.ndarray,
    origin_x: float,
    origin_y: float,
    um: float,
) -> tuple[int, int]:
    max_row = 0
    max_col = 0
    for selection in selections:
        props = selection.get("Properties") or {}
        coords = props.get("Coords") or []
        if len(coords) < 2:
            continue
        x0, y0 = float(coords[0][0]), float(coords[0][1])
        x1, y1 = float(coords[1][0]), float(coords[1][1])
        start = float(selection.get("StartTime", 0))
        end = float(selection.get("EndTime", start))
        i0 = int(np.searchsorted(index_time, start))
        i1 = int(np.searchsorted(index_time, end, side="right"))
        if i1 <= i0:
            continue
        n_pts = i1 - i0
        for k in range(n_pts):
            t = k / max(n_pts - 1, 1)
            x = x0 + t * (x1 - x0)
            y = y0 + t * (y1 - y0)
            max_row = max(max_row, int(round((y - origin_y) / um)))
            max_col = max(max_col, int(round((x - origin_x) / um)))
    return max_row + 3, max_col + 3


def _coords_extent(selections: list[dict]) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for selection in selections:
        props = selection.get("Properties") or {}
        for point in props.get("Coords") or []:
            xs.append(float(point[0]))
            ys.append(float(point[1]))
    return min(xs), min(ys), max(xs), max(ys)


def _global_grid_fits(
    selections: list[dict],
    index_time: np.ndarray,
    origin_x: float,
    origin_y: float,
    um: float,
    n_rows: int,
    n_cols: int,
) -> bool:
    total = 0
    inside = 0
    for selection in selections:
        props = selection.get("Properties") or {}
        coords = props.get("Coords") or []
        if len(coords) < 2:
            continue
        x0, y0 = float(coords[0][0]), float(coords[0][1])
        x1, y1 = float(coords[1][0]), float(coords[1][1])
        start = float(selection.get("StartTime", 0))
        end = float(selection.get("EndTime", start))
        i0 = int(np.searchsorted(index_time, start))
        i1 = int(np.searchsorted(index_time, end, side="right"))
        if i1 <= i0:
            continue
        for k in range(i1 - i0):
            t = k / max(i1 - i0 - 1, 1)
            x = x0 + t * (x1 - x0)
            y = y0 + t * (y1 - y0)
            row = int(round((y - origin_y) / um))
            col = int(round((x - origin_x) / um))
            total += 1
            if 0 <= row < n_rows and 0 <= col < n_cols:
                inside += 1
    return total > 0 and inside / total >= 0.5


def is_hdf5_session(path: str) -> bool:
    """Return True if path opens as HDF5 and looks like an imaging session."""
    _require_h5py()
    try:
        with h5py.File(path, "r") as handle:
            return OUTPUTS in handle and SELECTION_GROUPS in handle
    except OSError:
        return False


def read_session_metadata(path: str) -> SessionMetadata:
    """Read samples, ppm channels, imaging model, and geometry from an HDF5 session."""
    _require_h5py()
    if not is_hdf5_session(path):
        raise ValueError(f"Not a recognized HDF5 imaging session: {path}")

    with h5py.File(path, "r") as handle:
        imaging_global: dict = {}
        active_group = None
        physical_size_um = None
        pixel_grid = None
        physical_min_um = None
        cell_space_placement = None
        channels_by_sample: dict[str, list[str]] = {}

        if IMAGING_PLUGIN in handle:
            imaging = handle[IMAGING_PLUGIN]
            imaging_global = _load_json_attr(imaging, "Global") or {}
            if "Group" in imaging.attrs:
                active_group = _as_str(imaging.attrs["Group"])
            if imaging_global.get("physicalSize"):
                physical_size_um = _decode_qt_sizef(imaging_global["physicalSize"])
            if imaging_global.get("physicalMin"):
                physical_min_um = _decode_qt_sizef(imaging_global["physicalMin"])
            if imaging_global.get("pixelSize"):
                pixel_grid = _decode_qt_size(imaging_global["pixelSize"])
            cell_space_placement = imaging_global.get("cellSpacePlacement")
            for group_name, channels in (imaging_global.get("groupChannelNames") or {}).items():
                elements = []
                for ch in channels:
                    elem = _element_from_channel(ch, "ppm")
                    if elem:
                        elements.append(elem)
                    elif ch.endswith("_CPS"):
                        pass
                    elif not ch.endswith("_ppm") and not ch.endswith("_CPS"):
                        elements.append(ch)
                if elements:
                    channels_by_sample[group_name] = sorted(set(elements))

        imaging_model = _parse_imaging_model(imaging_global.get("imageType"))
        um = _microns_per_cell(imaging_global)

        ppm_channels = sorted(
            _element_from_channel(name, "ppm")
            for name in handle[OUTPUTS].keys()
            if name.endswith("_ppm") and _element_from_channel(name, "ppm")
        )
        cps_channels = sorted(
            _element_from_channel(name, "CPS")
            for name in handle[OUTPUTS].keys()
            if name.endswith("_CPS") and _element_from_channel(name, "CPS")
        )

        samples: list[SampleGeometry] = []
        selection_root = handle[SELECTION_GROUPS]
        for group_name in sorted(selection_root.keys()):
            payload = json.loads(_as_str(selection_root[group_name][()]))
            props = payload.get("Properties") or {}
            group_type = props.get("Group Type") or props.get("Type") or ""
            if group_type in SKIP_GROUP_TYPES:
                continue
            if group_type != SAMPLE_GROUP_TYPE:
                continue

            selections = payload.get("Selections") or []
            geom = _sample_geometry_from_selections(
                group_name,
                selections,
                imaging_model=imaging_model,
                physical_size_um=physical_size_um,
                pixel_grid=pixel_grid,
                physical_min_um=physical_min_um,
                um=um,
                index_time=np.asarray(handle[INDEX_TIME][:], dtype=float) if INDEX_TIME in handle else None,
            )
            samples.append(geom)

    return SessionMetadata(
        path=path,
        imaging_model=imaging_model,
        active_group=active_group,
        physical_size_um=physical_size_um,
        pixel_grid=pixel_grid,
        physical_min_um=physical_min_um,
        cell_space_placement=cell_space_placement,
        samples=samples,
        ppm_channels=ppm_channels,
        cps_channels=cps_channels,
        channels_by_sample=channels_by_sample,
    )


def _sample_geometry_from_selections(
    name: str,
    selections: list[dict],
    *,
    imaging_model: ImagingModel,
    physical_size_um: tuple[float, float] | None,
    pixel_grid: tuple[int, int] | None,
    physical_min_um: tuple[float, float] | None,
    um: float,
    index_time: np.ndarray | None,
) -> SampleGeometry:
    spot_width = spot_height = scan_speed = None
    pixel_x = pixel_y = um
    grid_rows = grid_cols = None

    if selections:
        p0 = selections[0].get("Properties") or {}
        spot_width = _float_or_none(p0.get("Spot Width"))
        spot_height = _float_or_none(p0.get("Spot Height"))
        scan_speed = _float_or_none(p0.get("Scan Speed"))

        if imaging_model == ImagingModel.CELLSPACE and index_time is not None and physical_min_um and pixel_grid:
            cw, ch = pixel_grid
            if _global_grid_fits(selections, index_time, physical_min_um[0], physical_min_um[1], um, ch, cw):
                grid_rows, grid_cols = ch, cw
            else:
                xmin, ymin, _, _ = _coords_extent(selections)
                origin_x = math.floor(xmin)
                origin_y = math.floor(ymin)
                grid_rows, grid_cols = _local_grid_bounds(
                    selections, index_time, origin_x, origin_y, um
                )
        else:
            xs = [_selection_coord_xy(s.get("Properties") or {})[0] for s in selections]
            ys = [_selection_coord_xy(s.get("Properties") or {})[1] for s in selections]
            grid_cols = len(set(xs))
            grid_rows = len(set(ys))
            pixel_x = _median_step(xs) or spot_width or um
            pixel_y = _median_step(ys) or spot_height or um

    return SampleGeometry(
        name=name,
        n_selections=len(selections),
        spot_width_um=spot_width,
        spot_height_um=spot_height,
        scan_speed_um_s=scan_speed,
        pixel_size_x_um=pixel_x,
        pixel_size_y_um=pixel_y,
        grid_rows=grid_rows,
        grid_cols=grid_cols,
    )


def _selection_coord_xy(properties: dict) -> tuple[float, float]:
    coords = properties.get("Coords") or []
    if not coords:
        return (0.0, 0.0)
    return float(coords[0][0]), float(coords[0][1])


def reconstruct_raster(path: str, sample: str, element: str, unit: str = "ppm") -> np.ndarray:
    """Build a 2D raster for one sample and element, dispatching on imaging model."""
    meta = read_session_metadata(path)
    if meta.imaging_model == ImagingModel.CELLSPACE:
        return reconstruct_cellspace_raster(path, sample, element, unit=unit, meta=meta)
    if meta.imaging_model == ImagingModel.FROM_SELECTIONS:
        raise NotImplementedError(
            "FromSelections raster reconstruction is not implemented yet."
        )
    raise ValueError(f"Unsupported imaging model: {meta.imaging_model.value}")


def reconstruct_cellspace_raster(
    path: str,
    sample: str,
    element: str,
    unit: str = "ppm",
    meta: SessionMetadata | None = None,
) -> np.ndarray:
    """
    Reconstruct a CellSpace raster by mapping each acquisition point along the
    selection segment onto the session µm grid (global or per-sample ROI).
    """
    _require_h5py()
    channel = f"{element}_{unit}"
    meta = meta or read_session_metadata(path)

    with h5py.File(path, "r") as handle:
        if sample not in handle[SELECTION_GROUPS]:
            raise KeyError(f"Sample group not found: {sample}")
        if channel not in handle[OUTPUTS]:
            raise KeyError(f"Output channel not found: {channel}")

        imaging_global = {}
        if IMAGING_PLUGIN in handle:
            imaging_global = _load_json_attr(handle[IMAGING_PLUGIN], "Global") or {}

        payload = json.loads(_as_str(handle[SELECTION_GROUPS][sample][()]))
        selections = payload.get("Selections") or []
        if not selections:
            raise ValueError(f"No selections for sample: {sample}")

        index_time = np.asarray(handle[INDEX_TIME][:], dtype=float)
        values = np.asarray(handle[f"{OUTPUTS}/{channel}"][:], dtype=float)
        um = _microns_per_cell(imaging_global)

        physical_min = (0.0, 0.0)
        n_cols = n_rows = 0
        if imaging_global.get("physicalMin") and imaging_global.get("pixelSize"):
            physical_min = _decode_qt_sizef(imaging_global["physicalMin"])
            n_cols, n_rows = _decode_qt_size(imaging_global["pixelSize"])

        if n_rows > 0 and n_cols > 0 and _global_grid_fits(
            selections, index_time, physical_min[0], physical_min[1], um, n_rows, n_cols
        ):
            origin_x, origin_y = physical_min
        else:
            xmin, ymin, _, _ = _coords_extent(selections)
            origin_x = math.floor(xmin)
            origin_y = math.floor(ymin)
            n_rows, n_cols = _local_grid_bounds(
                selections, index_time, origin_x, origin_y, um
            )

        grid = _fill_cellspace_grid(
            selections,
            index_time,
            values,
            origin_x,
            origin_y,
            um,
            n_rows,
            n_cols,
        )

        placement = imaging_global.get("cellSpacePlacement") or meta.cell_space_placement
        if placement == "Interpolated":
            grid = _interpolate_cellspace_gaps(grid)

        return grid


def _interpolate_cellspace_gaps(grid: np.ndarray) -> np.ndarray:
    """Fill gaps between laser spots (iolite Interpolated placement)."""
    if not np.any(np.isfinite(grid)):
        return grid
    try:
        from scipy.interpolate import griddata
    except ImportError:
        return grid

    rows, cols = grid.shape
    row_idx, col_idx = np.where(np.isfinite(grid))
    if len(row_idx) < 4:
        return grid
    values = grid[row_idx, col_idx]
    rr, cc = np.mgrid[0:rows, 0:cols]
    filled = griddata(
        np.column_stack([row_idx, col_idx]),
        values,
        (rr, cc),
        method="linear",
    )
    out = grid.copy()
    fill_mask = np.isfinite(filled)
    out[fill_mask] = filled[fill_mask]
    return out


def output_channel_name(element: str, unit: str) -> str:
    if unit == "raw":
        return element
    return f"{element}_{unit}"

"""Deterministic open 3D AUTO-Bezier centerlines, without Blender.

Numerical handle rules follow Blender 5.0.1's legacy curve implementation,
``calchandleNurb_intern`` with HD_AUTO and is_fcurve=false:
https://github.com/blender/blender/blob/v5.0.1/source/blender/blenkernel/intern/curve.cc#L2882
The Curve default resolution is 12 (DNA_curve_defaults.h, same tag):
https://github.com/blender/blender/blob/v5.0.1/source/blender/makesdna/DNA_curve_defaults.h#L20
Sources checked 2026-10-26. Blender sources are GPL-2.0-or-later.

This module evaluates only non-cyclic centerlines. It does not reproduce
Blender's float32 forward differences, tube frames or bevel tessellation.
Inputs and outputs retain the caller's axes and units; use metres when the
result feeds the geometry evaluator. Adjacent duplicate points are rejected.
"""
from __future__ import annotations

import operator

import numpy as np


_AUTO_HANDLE_FACTOR = 2.5614


def auto_bezier_points(points, resolution=12):
    """Sample each AUTO-Bezier span in ``resolution`` intervals.

    ``points`` is an Nx3 finite array, N >= 2. The result contains
    ``(N-1)*resolution+1`` samples, with every input knot included exactly
    once. Open endpoints use reflected virtual neighbours. Each handle uses
    its adjacent chord length, clamped to five times the opposite chord.
    A reversal with zero summed direction has collapsed handles at its knot.
    """
    if isinstance(resolution, (bool, np.bool_)):
        raise ValueError('resolution must be a positive integer')
    try:
        resolution = operator.index(resolution)
    except TypeError as exc:
        raise ValueError('resolution must be a positive integer') from exc
    if resolution < 1:
        raise ValueError('resolution must be a positive integer')
    knots = np.asarray(points, dtype=np.float64)
    if knots.ndim != 2 or knots.shape[1] != 3 or len(knots) < 2:
        raise ValueError('points must be an Nx3 array with N >= 2')
    if not np.isfinite(knots).all():
        raise ValueError('points must contain only finite coordinates')
    chords = np.diff(knots, axis=0)
    if np.any(np.linalg.norm(chords, axis=1) == 0):
        raise ValueError('adjacent points must be distinct')

    # Reflect the first/last neighbour across the endpoint, giving the same
    # forward chord on both sides there, rather than using a cyclic wrap.
    previous = np.concatenate((chords[:1], chords), axis=0)
    following = np.concatenate((chords, chords[-1:]), axis=0)
    left_length = np.linalg.norm(previous, axis=1)
    right_length = np.linalg.norm(following, axis=1)
    direction = previous/left_length[:, None]+following/right_length[:, None]
    divisor = np.linalg.norm(direction, axis=1)*_AUTO_HANDLE_FACTOR
    active = divisor != 0
    left_length = np.minimum(left_length, 5*right_length)
    right_length = np.minimum(right_length, 5*left_length)
    left = knots.copy()
    right = knots.copy()
    left[active] -= direction[active]*(left_length[active]/divisor[active])[:, None]
    right[active] += direction[active]*(right_length[active]/divisor[active])[:, None]

    # Direct cubic evaluation avoids accumulated forward-difference drift.
    # t=0 copies each original knot exactly; the final knot is appended once.
    t = np.arange(resolution, dtype=np.float64)[:, None]/resolution
    s = 1-t
    spans = [s**3*knots[i]+3*s**2*t*right[i]
             +3*s*t**2*left[i+1]+t**3*knots[i+1]
             for i in range(len(knots)-1)]
    return np.concatenate((*spans, knots[-1:]), axis=0)

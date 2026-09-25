from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve


def asysm(y: np.ndarray, lambda_: float, p: float, d: int) -> np.ndarray:
    y = np.asarray(y, dtype=float).reshape(-1)
    m = y.size
    w = np.ones(m, dtype=float)
    while True:
        z = difsmw(y, lambda_, w, d)
        updated = p * (y > z) + (1 - p) * (y <= z)
        if np.array_equal(updated, w):
            return z
        w = updated


def difsm(y: np.ndarray, lambda_: float, d: int) -> np.ndarray:
    y = np.asarray(y, dtype=float).reshape(-1)
    m = y.size
    identity = sparse.eye(m, format="csc")
    difference = _difference_matrix(m, d)
    system = identity + lambda_ * (difference.T @ difference)
    return np.asarray(spsolve(system, y), dtype=float)


def difsmw(y: np.ndarray, lambda_: float, w: np.ndarray, d: int) -> np.ndarray:
    y = np.asarray(y, dtype=float).reshape(-1)
    w = np.asarray(w, dtype=float).reshape(-1)
    m = y.size
    weights = sparse.diags(w, offsets=0, shape=(m, m), format="csc")
    difference = _difference_matrix(m, d)
    system = weights + lambda_ * (difference.T @ difference)
    rhs = w * y
    return np.asarray(spsolve(system, rhs), dtype=float)


def interpol(t: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    t = np.asarray(t, dtype=float).reshape(-1)
    y = np.asarray(y, dtype=float).reshape(-1)
    m = y.size
    sel = np.flatnonzero((1 < t) & (t < m))
    ti = np.floor(t[sel]).astype(int)
    tr = t[sel] - ti
    gradient = y[ti] - y[ti - 1]
    fitted = y[ti - 1] + tr * gradient
    return fitted, sel, gradient


def quadwarp(
    x: np.ndarray,
    y: np.ndarray,
    astart: np.ndarray | None = None,
    max_iter: int = 40,
    tolerance: float = 1e-6,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray(x, dtype=float).reshape(-1)
    y = np.asarray(y, dtype=float).reshape(-1)
    m = max(x.size, y.size)
    t = np.arange(1, m + 1, dtype=float)
    basis = np.column_stack([np.ones(m), t, (t / m) ** 2])
    coefficients = np.array([0.0, 1.0, 0.0], dtype=float)
    if astart is not None:
        coefficients = np.asarray(astart, dtype=float).reshape(3)

    rms_old = 0.0
    for _ in range(max_iter):
        warp = basis @ coefficients
        fitted, sel, gradient = interpol(warp, x)
        residual = y[sel] - fitted
        rms = float(np.sqrt(np.dot(residual, residual) / m))
        drms = abs((rms - rms_old) / (rms + 1e-10))
        if drms < tolerance:
            break
        rms_old = rms
        regression = gradient[:, None] * basis[sel, :]
        delta = np.linalg.lstsq(regression, residual, rcond=None)[0]
        coefficients = coefficients + delta

    coefficients[2] = coefficients[2] / (m**2)
    warp = basis @ np.array([coefficients[0], coefficients[1], coefficients[2] * (m**2)])
    return warp, sel, coefficients


def _difference_matrix(m: int, d: int) -> sparse.csc_matrix:
    identity = sparse.eye(m, format="csc")
    difference = identity
    for _ in range(d):
        difference = difference[1:] - difference[:-1]
    return difference.tocsc()

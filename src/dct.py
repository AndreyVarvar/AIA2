import numpy as np


# ---------------------------------------------------------------------------
# Internal functions
# ---------------------------------------------------------------------------

def _reorder_forward(x: np.ndarray) -> np.ndarray:
    """Even indices first, then odd indices in reverse order."""
    n = x.shape[-1]
    v = np.empty_like(x)
    v[..., : (n + 1) // 2] = x[..., 0::2]               # even: 0,2,4,...
    v[..., (n + 1) // 2 :] = x[..., 1::2][..., ::-1]    # odd reversed
    return v


def _dct1d_vec(x: np.ndarray, axis: int) -> np.ndarray:
    """
    Vectorised ortho DCT-II along the given axis.

    Algorithm
    ---------
    1. Shuffle samples: even indices first, odd indices reversed  -> v
    2. Full n-point FFT of v  -> V
    3. Multiply by twiddle  e^{-j pi k / 2N}
    4. Take 2x the real part
    5. Orthonormal scaling: divide by sqrt(2N), DC also by sqrt(2)
    """
    x = np.moveaxis(x, axis, -1)
    n = x.shape[-1]

    v    = _reorder_forward(x)
    V    = np.fft.fft(v, axis=-1)
    k    = np.arange(n)
    twig = np.exp(-1j * np.pi * k / (2 * n))
    out  = 2.0 * (V * twig).real
    out[..., 0] /= np.sqrt(2)
    out *= 1.0 / np.sqrt(2 * n)

    return np.moveaxis(out, -1, axis)


def _idct1d_vec(Y: np.ndarray, axis: int) -> np.ndarray:
    """
    Vectorised ortho IDCT-II (= DCT-III) along the given axis.

    We recover the complex FFT array V from the real DCT coefficients by
    exploiting the Hermitian symmetry of the FFT of a real signal:

        V[k] and V[N-k] = conj(V[k]) are recovered from raw[k] and raw[N-k]
        via a 2x2 rotation-matrix inversion.

    Then IFFT(V) gives the shuffled signal, which we unshuffle.
    """
    Y = np.moveaxis(Y, axis, -1)
    n = Y.shape[-1]

    # Undo orthonormal scaling to recover raw = 2 * Re(twig[k] * V[k])
    raw = Y.copy().astype(float)
    raw[..., 0] *= np.sqrt(2)
    raw *= np.sqrt(2 * n)

    k_arr = np.arange(n, dtype=float)
    c = np.cos(-np.pi * k_arr / (2 * n))
    s = np.sin(-np.pi * k_arr / (2 * n))

    # raw[n-k] for every k (with self-pairing at k=0)
    raw_nk = np.empty_like(raw)
    raw_nk[..., 0]  = raw[..., 0]
    raw_nk[..., 1:] = raw[..., -1:0:-1]

    # Rotation-matrix inverse:
    #   [[c,-s],[s,c]] [R,I]^T = [raw/2, -raw_nk/2]^T
    R = ( c * raw  - s * raw_nk) / 2.0
    I = -(s * raw  + c * raw_nk) / 2.0

    I[..., 0] = 0.0          # DC bin is real
    if n % 2 == 0:
        I[..., n // 2] = 0.0                                     # Nyquist bin is real
        R[..., n // 2] = raw[..., n // 2] / (2.0 * c[n // 2])   # re-derive R

    V_rec = R + 1j * I
    v     = np.fft.ifft(V_rec, axis=-1).real

    # Undo even/odd shuffle
    x    = np.empty_like(v)
    half = (n + 1) // 2
    x[..., 0::2] = v[..., :half]
    x[..., 1::2] = v[..., half:][..., ::-1]

    return np.moveaxis(x, -1, axis)


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def dct2d(x: np.ndarray) -> np.ndarray:
    """
    Orthonormal 2D DCT-II.

    Parameters
    ----------
    x : array_like, shape (M, N)

    Returns
    -------
    X : ndarray, shape (M, N)
    """
    x = np.asarray(x, dtype=float)
    tmp = _dct1d_vec(x,   axis=1)   # DCT along rows
    return _dct1d_vec(tmp, axis=0)  # DCT along columns


def idct2d(X: np.ndarray) -> np.ndarray:
    """
    Orthonormal 2D IDCT (inverse of dct2d).

    Parameters
    ----------
    X : array_like, shape (M, N)

    Returns
    -------
    x : ndarray, shape (M, N)
    """
    X = np.asarray(X, dtype=float)
    tmp = _idct1d_vec(X,   axis=0)   # IDCT along columns
    return _idct1d_vec(tmp, axis=1)  # IDCT along rows
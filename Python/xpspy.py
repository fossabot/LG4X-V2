# from numpy import amax, amin
# make x and y lists (arrays) in the range between xmin and xmax
import numpy as np


def fit_range(x, y, xmin, xmax):
    # print(xmin, xmax)
    if xmin > xmax:
        xmin0 = xmin
        xmin = xmax
        xmax = xmin0

    if x[0] < x[-1]:
        # XAS in photon energy scale or XPS in kinetic energy scale
        if x[0] < xmin or xmax < x[len(x) - 1]:
            if xmax < x[len(x) - 1]:
                for i in range(len(x) - 1, -1, -1):
                    if x[i] <= xmax:
                        rmidx = i
                        break
            else:
                rmidx = len(x) - 1

            if x[0] < xmin:
                for i in range(0, len(x) - 1):
                    if x[i] >= xmin:
                        lmidx = i
                        break
            else:
                lmidx = 0

            xn = x[lmidx:rmidx + 1].copy()
            yn = y[lmidx:rmidx + 1].copy()
        # print(len(x), len(xn), xn[0], xn[len(xn)-1])
        else:
            xn = x
            yn = y
    else:
        # XPS in binding energy scale
        if x[len(x) - 1] < xmin or xmax < x[0]:
            if xmax < x[0]:
                for i in range(0, len(x) - 1):
                    if x[i] <= xmax:
                        lmidx = i
                        break
            else:
                lmidx = 0

            if x[len(x) - 1] < xmin:
                for i in range(len(x) - 1, -1, -1):
                    if x[i] >= xmin:
                        rmidx = i
                        break
            else:
                rmidx = len(x) - 1

            xn = x[lmidx:rmidx + 1].copy()
            yn = y[lmidx:rmidx + 1].copy()
        # print(len(x), len(xn), xn[0], xn[len(xn)-1])
        else:
            xn = x
            yn = y

    # return [array(xn), array(yn)]
    return [xn, yn]


def shirley_calculate(x, y, tol=1e-5, maxit=10):
    # https://github.com/kaneod/physics/blob/master/python/specs.py

    # Make sure we've been passed arrays and not lists.
    # x = array(x)
    # y = array(y)
    n=len(y)
    # Sanity check: Do we actually have data to process here?
    # print(any(x), any(y), (any(x) and any(y)))
    if not (any(x) and any(y)):
        print("One of the arrays x or y is empty. Returning zero background.")
        return x * 0

    # Next ensure the energy values are *decreasing* in the array,
    # if not, reverse them.
    if x[0] < x[-1]:
        is_reversed = True
        x = x[::-1]
        y = y[::-1]
    else:
        is_reversed = False


    yl = y[0]
    yr = y[-1]

    # Initial value of the background shape B. The total background S = yr + B,
    # and B is equal to (yl - yr) below lmidx and initially zero above.
    B = y * 0

    Bnew = B.copy()

    it = 0
    while it < maxit:
        # Calculate new k = (yl - yr) / (int_(xl)^(xr) J(x') - yr - B(x') dx')
        ksum = 0.0
        for i in range(n-1):
            ksum += (x[i] - x[i + 1]) * 0.5 * (y[i] + y[i + 1] - 2 * yr - B[i] - B[i + 1])
        k = (yl - yr) / ksum
        # Calculate new B
        for i in range(n):
            ysum = 0.0
            for j in range(i, n-1):
                ysum += (x[j] - x[j + 1]) * 0.5 * (y[j] + y[j + 1] - 2 * yr - B[j] - B[j + 1])
            Bnew[i] = k * ysum
        # If Bnew is close to B, exit.
        # if norm(Bnew - B) < tol:
        B = Bnew - B
        # print(it, (B**2).sum(), tol**2)
        if (B ** 2).sum() < tol ** 2:
            B = Bnew.copy()
            break
        else:
            B = Bnew.copy()
        it += 1

    if it >= maxit:
        print("Max iterations exceeded before convergence.")
    if is_reversed:
        # print("Shirley BG: tol (ini = ", tol, ") , iteration (max = ", maxit, "): ", it)
        return (yr + B)[::-1]
    else:
        # print("Shirley BG: tol (ini = ", tol, ") , iteration (max = ", maxit, "): ", it)
        return yr + B

def shirley(y, k, const):
    """
    Calculates the Shirley background of an X-ray photoelectron spectroscopy (XPS) spectrum.
    This implementation calculates the Shirley background by integrating the step characteristic of the spectrum.

    Parameters
    ----------
    y : array-like
        1D-array containing the y-values (intensities) of the spectrum.
    k : float
        Slope of the step characteristic.
    const : float
        Constant offset of the step characteristic.

    Returns
    -------
    array-like
        The Shirley background of the XPS spectrum.
    """
    n = len(y)
    y_right = const
    y_temp = y - y_right  # step characteristic is better approximated if only the step without background is integrated
    bg = []
    for i in range(n):
        bg.append(np.sum(y_temp[i:]))
    return np.asarray([k * elem + y_right for elem in bg])
def tougaard_calculate(x, y, tb=2866, tc=1643, tcd=1, td=1, maxit=100):
    # https://warwick.ac.uk/fac/sci/physics/research/condensedmatt/surface/people/james_mudd/igor/

    # Sanity check: Do we actually have data to process here?
    if not (any(x) and any(y)):
        print("One of the arrays x or y is empty. Returning zero background.")
        return [np.asarray(x * 0), tb]

    # KE in XPS or PE in XAS
    if x[0] < x[-1]:
        is_reversed = True
    # BE in XPS
    else:
        is_reversed = False

    Btou = y * 0

    it = 0
    while it < maxit:
        if not is_reversed:
            for i in range(len(y) - 1, -1, -1):
                Bint = 0
                for j in range(len(y) - 1, i - 1, -1):
                    Bint += (y[j] - y[len(y) - 1]) * (x[0] - x[1]) * (x[i] - x[j]) / (
                            (tc + tcd * (x[i] - x[j]) ** 2) ** 2 + td * (x[i] - x[j]) ** 2)
                Btou[i] = Bint * tb

        else:
            for i in range(len(y) - 1, -1, -1):
                Bint = 0
                for j in range(len(y) - 1, i - 1, -1):
                    Bint += (y[j] - y[len(y) - 1]) * (x[1] - x[0]) * (x[j] - x[i]) / (
                            (tc + tcd * (x[j] - x[i]) ** 2) ** 2 + td * (x[j] - x[i]) ** 2)
                Btou[i] = Bint * tb

        Boffset = Btou[0] - (y[0] - y[len(y) - 1])
        # print(Boffset, Btou[0], y[0], tb)
        if abs(Boffset) < (0.000001 * Btou[0]) or maxit == 1:
            break
        else:
            tb = tb - (Boffset / Btou[0]) * tb * 0.5
        it += 1

    print("Tougaard B:", tb, ", C:", tc, ", C':", tcd, ", D:", td)

    return [np.asarray(y[len(y) - 1] + Btou), tb]


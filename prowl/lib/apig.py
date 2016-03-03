from __future__ import absolute_import, division, print_function

from itertools import combinations
import numpy as np
from scipy.misc import comb
from ..utils import permanent
from ..utils import slater


def generate_guess(self):
    """
    Generate an appropriate random guess for the coefficient vector `x`.

    Returns
    -------
    x : 1-index np.ndarray

    """

    # `np.complex128` arrays are partitioned into columns like this:
    # [[Re][Im][Re][Im]...]; generate an array to handle this
    x = np.zeros((self.p, self.k), dtype=self.dtype)

    # Add the real identity
    x[:, :] += np.eye(self.p, self.k)

    # Add random noise
    x[:, :] += (0.2 / x.size) * (np.random.rand(self.p, self.k) - 0.5)
    if self.dtype == np.complex128:
        x[:, :] += (0.2 / x.size) * (np.random.rand(self.p, self.k) - 0.5) * 1j

    # Normalize
    x[:, :] /= np.max(x)

    # Make it a vector
    x = x.ravel()

    return x


def generate_pspace(self):
    """
    Generate an appropriate projection space for solving the coefficient vector `x`.

    Returns
    -------
    pspace : list
        List of Python ints representing Slater determinants.

    """

    # Determine the minimum length of `pspace`, and the ground state
    params = self.x.size
    ground = sum(2 ** i for i in range(self.n))
    pspace = [ground]

    # Get occupied (HOMOs first!) and virtual indices
    occ = list(range(self.n // 2 - 1, -1, -1))
    vir = list(range(self.n // 2, self.k))

    # Add pair excitations
    nexc = 1
    nocc = len(occ) + 1
    nvir = len(vir) + 1
    while params > len(pspace) and nexc < nocc:
        # Determine the smallest usable set of frontier orbitals
        for i in range(2, nocc):
            if comb(i, 2, exact=True) ** 2 >= params - len(pspace):
                nfrontier = i
                break
        else:
            nfrontier = max(nocc, nvir)
        # Add excitations from all combinations of `nfrontier` HOMOs...
        for i in combinations(occ[:nfrontier], nexc):
            # ...to all combinations of `nfrontier` LUMOs
            for j in combinations(vir[:nfrontier], nexc):
                sd = ground
                for k, l in zip(i, j):
                    sd = slater.excite_pair(sd, k, l)
                pspace.append(sd)
        nexc += 1

    # Add single excitations (some betas to alphas) if necessary
    # (usually only for very small systems)
    if params > len(pspace):
        for i in occ:
            for j in vir:
                sd = slater.excite(ground, i * 2 + 1, j * 2)
                pspace.append(sd)

    # Return the sorted `pspace`
    pspace.sort()
    return pspace


def generate_view(self):
    """
    Generate a view of `x` corresponding to the shape of the coefficient array.

    Returns
    -------
    view : 2-index np.ndarray

    """

    return self.x.reshape(self.p, self.k)


def hamiltonian(self, sd):
    """
    Compute the Hamiltonian of the wavefunction projected against `sd`.

    Parameters
    ----------
    sd : int
        The Slater Determinant against which to project.

    Returns
    -------
    energy : tuple
        Tuple of floats corresponding to the one electron, coulomb, and exchange
        energies.

    """

    olp = self.overlap(sd)

    one_electron = 0.0
    coulomb = 0.0
    coulomb_tmp = 0.0
    exchange = 0.0

    for i in range(self.k):
        if slater.occupation_pair(sd, i):
            one_electron += 2 * self.H[i, i]
            coulomb += self.G[i, i, i, i]
            for j in range( i + 1, self.k):
                if slater.occupation_pair(sd, j):
                    coulomb += 4 * self.G[i, j, i, j]
                    exchange -= 2 * self.G[i, j, j, i]
            for j in range(self.k):
                if not slater.occupation_pair(sd, j):
                    exc = slater.excite_pair(sd, i, j)
                    coulomb_tmp += self.G[i, i, j, j] * self.overlap(exc)

    one_electron *= olp
    exchange *= olp
    coulomb = coulomb * olp + coulomb_tmp

    return one_electron, coulomb, exchange


def hamiltonian_deriv(self, sd, x, y):
    """
    Compute the partial derivative of the Hamiltonian with respect to parameter `(x, y)`.

    Parameters
    ----------
    sd : int
        The Slater Determinant against which to project.
    x : int
    y : int

    Returns
    -------
    energy : tuple
        Tuple of floats corresponding to the one electron, coulomb, and exchange
        energies.

    """

    olp = self.overlap_deriv(sd, x, y)

    one_electron = 0.0
    coulomb = 0.0
    coulomb_tmp = 0.0
    exchange = 0.0

    for i in range(self.k):
        if slater.occupation_pair(sd, i):
            one_electron += 2 * self.H[i, i]
            coulomb += self.G[i, i, i, i]
            for j in range( i + 1, self.k):
                if slater.occupation_pair(sd, j):
                    coulomb += 4 * self.G[i, j, i, j]
                    exchange -= 2 * self.G[i, j, j, i]
            for j in range(self.k):
                if not slater.occupation_pair(sd, j):
                    exc = slater.excite_pair(sd, i, j)
                    coulomb_tmp += self.G[i, i, j, j] * self.overlap_deriv(exc, x, y)

    one_electron *= olp
    exchange *= olp
    coulomb = coulomb * olp + coulomb_tmp

    return one_electron, coulomb, exchange


def jacobian(self, x):
    """
    Compute the partial derivative of the objective function.

    Parameters
    ----------
    x : 1-index np.ndarray
        The coefficient vector.

    """

    # Update the coefficient vector
    self.x[:] = x
    jac = np.empty((len(self.pspace) + 2, self.x.size), dtype=x.dtype)

    # Loop through all coefficients
    c = 0
    for i in range(self.p):
        for j in range(self.k):

            # Intialize needed variables
            energy = sum(self.hamiltonian(self.ground))
            d_olp = self.overlap_deriv(self.ground, i, j)
            d_energy = sum(self.hamiltonian_deriv(self.ground, i, j))

            # Impose d<HF|Psi> == 1 + 0j
            jac[-1, c] = d_olp

            # Impose dC[0, 0] == 1 + 0j
            if c == 0:
                jac[-2, c] = 1
            else:
                jac[-2, c] = 0

            # Impose (for all SDs in `pspace`) <SD|H|Psi> - E<SD|H|Psi> == 0
            for k, sd in enumerate(self.pspace):
                d_tmp = sum(self.hamiltonian_deriv(sd, i, j)) \
                    - energy * self.overlap_deriv(sd, i, j) - d_energy * self.overlap(sd)
                jac[k, c] = d_tmp

            # Move to the next coefficient
            c += 1

    # The Jacobian was exactly half of what finite difference told me it should
    # have been... so I fixed it... don't know why though.
    return jac * 0.5


def objective(self, x):
    """
    Compute the objective function for solving the coefficient vector.
    The function is of the form "<sd|H|Psi> - E<sd|Psi> == 0 for all sd in pspace".

    Parameters
    ----------
    x : 1-index np.ndarray
        The coefficient vector.

    """

    # Update the coefficient vector
    self.x[:] = x

    # Intialize needed variables
    olp = self.overlap(self.ground)
    energy = sum(self.hamiltonian(self.ground))
    obj = np.empty((len(self.pspace) + 2), dtype=x.dtype)

    # Impose <HF|Psi> == 1
    obj[-1] = olp - 1.0

    # Impose C[0, 0] == 1 + 0j
    obj[-2] = self.x[0] - 1.0

    # Impose (for all SDs in `pspace`) <SD|H|Psi> - E<SD|H|Psi> == 0
    for i, sd in enumerate(self.pspace):
        obj[i] = sum(self.hamiltonian(sd)) - energy * self.overlap(sd)

    return obj


def overlap(self, sd):
    """
    Compute the overlap of the wavefunction with `sd`.

    Parameters
    ----------
    sd : int
        The Slater Determinant against which to project.

    """

    # If the Slater determinant is bad
    if sd is None:
        return 0
    # If the SD and the wavefunction have a different number of electrons
    elif slater.number(sd) != self.n:
        return 0
    # If the SD is not a closed-shell singlet
    elif any(slater.occupation(sd, 2 * i) != slater.occupation(sd, 2 * i + 1) for i in range(self.k)):
        return 0

    # Evaluate the overlap
    occ = [i for i in range(self.k) if slater.occupation_pair(sd, i)]
    return permanent.dense(self.C[:, occ])


def overlap_deriv(self, sd, x, y):
    """
    Compute the partial derivative of the overlap of the wavefunction with `sd`.

    Parameters
    ----------
    sd : int
        The Slater Determinant against which to project.

    """

    # If the Slater determinant is bad
    if sd is None:
        return 0
    # If the SD and the wavefunction have a different number of electrons
    elif slater.number(sd) != self.n:
        return 0
    # If the SD is not a closed-shell singlet
    elif any(slater.occupation(sd, 2 * i) != slater.occupation(sd, 2 * i + 1) for i in range(self.k)):
        return 0

    # Evaluate the overlap
    occ = [i for i in range(self.k) if slater.occupation_pair(sd, i)]
    if y not in occ:
        return 0
    else:
        return permanent.dense_deriv(self.C[:, occ], x, occ.index(y))

def truncate(self, coeffs, val_threshold=1e-5, err_threshold=1e-6, num_threshold=1000):
    """ Truncates the CI expansion of wavefunction such that the overlap between the
    truncated and the original wavefunction is close enough to 1

    Uses "inequality of Hadamard type for permanents"
    ..math::
        | A |^+ \leq \frac{N!} {N^{N/2}} \prod_{j=1}^N || \vec{A}^j ||
    where :math: `\vec{A}^j` is the jth column vector of A.

    Parameters
    ----------
    coeffs : np.ndarray(self.p, self.k)
        Coefficient matrix of the geminals
    val_threshold : float
        Limit for the estimated absolute contribution of the slater determinant to the
        wavefunction
    num_threshold : int
        Limit for the number of determinants
    err_threshold : float
        Limit for the estimated absolute difference between 1 and the overlap between the
        truncated and original wavefunction

    Returns
    -------
    slater_dets : list(M,)
        slater determinants (in integer form) in the truncated wavefunction
    error : float
        error associated with the truncation

    References
    ----------
     * http://arxiv.org/pdf/math/0508096v1.pdf

    """
    assert coeffs.shape==(self.p, self.k), 'Shape of the coefficient matrix is not P*K'
    print('Truncating AP1roG Wavefunction...')
    # norms of each column
    col_norms = np.sum(np.abs(coeffs), axis=0)
    # orbital indices sorted from largest to smallest norm
    orb_indices = np.argsort(col_norms)[::-1].tolist()
    # order column norms from largest to smallest norm
    col_norms = col_norms[orb_indices].tolist()

    # list of slater determinants
    sds = []

    # copied from combination code from itertools
    n = self.k
    r = self.p
    assert r <= n
    indices = range(r)

    upper_lim = np.prod([col_norms[j] for j in indices])
    assert upper_lim > val_threshold
    sds.append(slater.create_multiple_pairs(0, *(orb_indices[j] for j in indices)))
    last_limit_over_threshold = False
    while len(sds) <= num_threshold:
        # find the index to iterate
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            break
        # find next set of indices
        if not last_limit_over_threshold or i == 0:
            indices[i] += 1
            for j in range(i+1, r):
                indices[j] = indices[j-1] + 1
        elif i >= 1:
            indices[i-1] += 1
            for j in range(i, r):
                indices[j] = indices[j-1] + 1
        last_limit_over_threshold = False
        # append
        upper_lim = np.prod([col_norms[j] for j in indices])
        if upper_lim > val_threshold:
            sds.append(slater.create_multiple_pairs(0, *(orb_indices[j] for j in indices)))
        else:
            last_limit_over_threshold = True
    else: # if len(sds) > num_threshold
        print('Warning: Limit for the number of Slater Determinants, '+
              '{0}, was reached. '.format(num_threshold)+
              'You might want to have a higher num_threshold or a lower val_threshold')
    num_remaining = comb(n, r) - len(sds)
    # TODO: need a smarter way of estimating the error
    overlap_error = num_remaining*val_threshold**2
    if overlap_error > err_threshold:
        print('Warning: Estimated error exceeds the err_threshold, {0}.'.format(err_threshold))
    return sds

def density_matrix(self, val_threshold=1e-4):
    """
    Returns the second order density matrix

    Parameters
    ----------
    a : int
    b : int
    c : int
    d : int
    val_threshold : float

    """
    # assume wavefunction is converged
    # i'm guessing the generate_view gives the converged coefficients
    coeffs = self.generate_view()
    coeffs = np.hstack((np.identity(self.p), self.generate_view())) # this is the only part that is different
    # norms of each column
    col_norms = np.linalg.norm(coeffs, axis=0)

    largest_val = np.prod(col_norms[np.argpartition(col_norms, -self.p)][-self.p:])
    #sds = self.truncate(val_threshold=val_threshold/largest_val,
    #                           num_threshold=num_threshold)
    sds = (slater.create_multiple_pairs(0, *i) for i in combinations(range(self.k), self.p))

    # TODO: check!
    density_matrix = np.zeros([self.k]*4)
    for a in range(self.k):
        for c in range(self.k):
            # number of terms used to get density matrix element
            num_used = 0
            for sd in sds:
                if slater.occupation_pair(sd, a):
                    shared_sd_indices = [i for i in range(self.k) if slater.occupation_pair(sd, i) and i!=a]
                    upper_lim = np.prod(col_norms[shared_sd_indices])**2
                    upper_lim *= col_norms[a]
                    upper_lim *= col_norms[c]
                    if upper_lim > val_threshold:
                        if not slater.occupation_pair(sd, c):
                            density_matrix[a, a, c, c] += self.overlap(sd)*self.overlap(slater.excite_pair(sd, a, c))
                        else:
                            density_matrix[a, c, c, a] += self.overlap(sd)**2
                            density_matrix[a, c, a, c] += density_matrix[a, c, c, a]
                            density_matrix[c, a, c, a] += density_matrix[a, c, c, a]
                            density_matrix[c, a, a, c] += density_matrix[a, c, c, a]
                        num_used += 1
            # number of double excitations available
            num_avail = self.p*(self.k-self.p)*comb(self.k, self.p)
            #TODO: need a better way of calculating error
            error = (num_avail-num_used)*val_threshold
    return density_matrix

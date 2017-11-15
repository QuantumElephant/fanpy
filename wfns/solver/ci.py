"""Solver for CI wavefunctions."""
from __future__ import absolute_import, division, print_function
import numpy as np
import scipy.linalg
from wfns.wfn.ci.base import CIWavefunction
from wfns.ham.base import BaseHamiltonian

__all__ = []


def brute(wfn, ham, savefile=''):
    """Solve the wavefunction by eigenvalue decomposition of the CI matrix.

    Parameters
    ----------
    wfn : CIWavefunction
        CI wavefunction.
    ham : BaseHamiltonian
        Hamiltonian.
    savefile : str
        File to which the eigenvectors and the eigenvalue will be saved.
        File is saved as a numpy array where the first row corresponds to the energies and the
        subsequent rows correspond to the coefficients for these energies.

    Returns
    -------
    eigval : np.ndarray(K,)
        Energy of each excited state.
    eigvec : np.ndarray(K, K)
        CI coefficients of each excited state.
        Column `eigvec[:, i]` corresponds to the eigenvalue `eigval[i]`.

    Raises
    ------
    TypeError
        If wavefunction is not an instance (or instance of a child) of CIWavefunction.
        If Hamiltonian is not an instance (or instance of a child) of ChemicalHamiltonian.
    ValueError
        If wavefunction and Hamiltonian do not have the same data type.
        If wavefunction and Hamiltonian do not have the same number of spin orbitals.

    """
    # check parameters
    if not isinstance(wfn, CIWavefunction):
        raise TypeError('Given wavefunction is not an instance of BaseWavefunction (or its child).')
    elif not isinstance(ham, BaseHamiltonian):
        raise TypeError('Given Hamiltonian is not an instance of BaseHamiltonian (or its child).')
    elif wfn.dtype != ham.dtype:
        raise ValueError('Wavefunction and Hamiltonian do not have the same data type.')
    elif wfn.nspin != ham.nspin:
        raise ValueError('Wavefunction and Hamiltonian do not have the same number of spin '
                         'orbitals')
    elif not isinstance(savefile, str):
        raise TypeError('The save file must be given as a string.')

    ci_matrix = np.zeros((wfn.nsd, wfn.nsd), dtype=wfn.dtype)
    for i, sd1 in enumerate(wfn.sd_vec):
        for j, sd2 in enumerate(wfn.sd_vec[i:]):
            ci_matrix[i, i+j] += sum(ham.integrate_sd_sd(sd1, sd2))
    # ci_matrix += ci_matrix.T - np.diag(np.diag(ci_matrix))

    eigval, eigvec = scipy.linalg.eigh(ci_matrix, lower=False, overwrite_a=True, turbo=False, type=1)
    del ci_matrix

    if savefile != '':
        np.save(savefile, np.vstack(eigval, eigvec))

    return eigval, eigvec

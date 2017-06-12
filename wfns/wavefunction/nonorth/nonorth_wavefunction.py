"""Wavefunction with nonorthonormal orbitals.

A parameterized multideterminantal wavefunction can be written as

..math::
    \ket{\Psi} = \sum_{\mathbf{m}} f(\mathbf{m}) \ket{\mathbf{m}}

where :math:`\ket{mathbf{m}}` is a Slater determinant. If the Slater determinants are constructed
from nonorthonormal orbitals, then each Slater determinant can be expressed as a linear combination
of Slater determinants constructed from orthonormal orbitals.

..math::
    \ket{\Psi}
    &= \sum_{\mathbf{n}} f(\mathbf{n}) \ket{\mathbf{n}}\\
    &= \sum_{\mathbf{n}} f(\mathbf{n}) \sum_{\mathbf{m}}
    |C(\mathbf{n}, \mathbf{m})|^- \ket{\mathbf{m}}\\
    &= \sum_{\mathbf{n}} \sum_{\mathbf{m}}
    |f(\mathbf{n}) C(\mathbf{n}, \mathbf{m})|^- \ket{\mathbf{m}}
"""
from __future__ import absolute_import, division, print_function
import itertools as it
import numpy as np
from ...backend import slater
from ..base_wavefunction import BaseWavefunction
from ..ci.ci_wavefunction import CIWavefunction

__all__ = []


class NonorthWavefunction(BaseWavefunction):
    """Wavefunction with nonorthonormal orbitals expressed with respect to orthonormal orbitals.

    Nonorthonormal orbitals are expressed with respect to orthonormal orbitals.

    Attributes
    ----------
    nelec : int
        Number of electrons
    dtype : {np.float64, np.complex128}
        Data type of the wavefunction
    memory : float
        Memory available for the wavefunction
    nspin : int
        Number of orthonormal spin orbitals (alpha and beta)

    Properties
    ----------
    nparams : int
        Number of parameters
    params_shape : 2-tuple of int
        Shape of the parameters
    nspatial : int
        Number of orthonormal spatial orbitals
    spin : float, None
        Spin of the wavefunction
        :math:`\frac{1}{2}(N_\alpha - N_\beta)` (Note that spin can be negative)
        None means that all spins are allowed
    seniority : int, None
        Seniority (number of unpaired electrons) of the wavefunction
        None means that all seniority is allowed
    template_params : np.ndarray
        Template of the wavefunction parameters
        Depends on the attributes given

    Methods
    -------
    __init__(self, nelec, nspin, dtype=None, memory=None)
        Initializes wavefunction
    assign_nelec(self, nelec)
        Assigns the number of electrons
    assign_nspin(self, nspin)
        Assigns the number of spin orbitals
    assign_dtype(self, dtype)
        Assigns the data type of parameters used to define the wavefunction
    assign_memory(self, memory=None)
        Assigns the memory allocated for the wavefunction
    assign_params(self, params)
        Assigns the parameters of the wavefunction
    get_overlap(self, sd, deriv=None)
        Gets the overlap from cache and compute if not in cache
        Default is no derivatization
    """
    def __init__(self, nelec, nspin, dtype=None, memory=None, wfn=None, orth_to_nonorth=None):
        """Initialize the wavefunction.

        Parameters
        ----------
        nelec : int
            Number of electrons
        nspin : int
            Number of spin orbitals
        dtype : {float, complex, np.float64, np.complex128, None}
            Numpy data type
            Default is `np.float64`
        memory : {float, int, str, None}
            Memory available for the wavefunction
            Default does not limit memory usage (i.e. infinite)
        wfn : BaseWavefunction
            Wavefunction that will be built up using nonorthnormal orbitals
        orth_to_nonorth : np.ndarray
            Transformation matrix from orthonormal orbitals to nonorthonormal orbitals
            :math:`\ket{\tilde{\phi}_i} = \sum_{j} \ket{\phi_j} T_{ji}`
            Default is an identity matrix.
        """
        super().__init__(nelec, nspin, dtype=dtype, memory=memory)
        self.assign_wfn(wfn)
        self.assign_params(orth_to_nonorth)

    @property
    def spin(self):
        """Spin of the wavefunction.

        Since the orbitals may mix regardless of the spin, the spin of the wavefunction is hard to
        determine.

        Returns
        -------
        spin
            Spin of the (composite) wavefunction if the orbitals are restricted or unrestricted
            None if the orbital is generalized
        """
        if self.orbtype in ['restricted', 'unrestricted']:
            return self.wfn.spin
        else:
            return None

    @property
    def seniority(self):
        """Seniority of the wavefunction."""
        if self.orbtype in ['restricted', 'unrestricted']:
            return self.wfn.seniority
        else:
            return None

    @property
    def template_params(self):
        """Return the shape of the wavefunction parameters.

        The orbital transformations are the wavefunction parameters.
        """
        return (np.eye(self.nspatial, self.wfn.nspatial, dtype=self.dtype), )

    @property
    def nparams(self):
        """Return the number of wavefunction parameters."""
        return tuple(i.size for i in self.params)

    @property
    def params_shape(self):
        """Return the shape of the wavefunction parameters."""
        return tuple(i.shape for i in self.params)

    @property
    def orbtype(self):
        """Return the orbital type."""
        if len(self.params) == 1 and self.params[0].shape[0] == self.nspatial:
            return 'restricted'
        elif len(self.params) == 2:
            return 'unrestricted'
        elif len(self.params) == 1 and self.params[0].shape[0] == self.nspin:
            return 'generalized'

    def assign_wfn(self, wfn=None):
        """Assign the wavefunction.

        Parameters
        ----------
        wfn : BaseWavefunction
            Wavefunction that will be built up using nonorthnormal orbitals

        Raises
        ------
        ValueError
            If the given wavefunction is not an instance of BaseWavefunction
            If the given wavefunction does not have the same number of electrons as the instantiated
            NonorthWavefunction
            If the given wavefunction does not have the same data type as the instantiated
            NonorthWavefunction.
            If the given wavefunction does not have the same memory as the instantiated
            NonorthWavefunction.
        """
        if wfn is None:
            wfn = CIWavefunction(self.nelec, self.nspin, dtype=self.dtype, memory=self.memory)
        elif not isinstance(wfn, BaseWavefunction):
            raise ValueError('Given wavefunction must be an instance of BaseWavefunction (or its'
                             ' child).')

        if wfn.nelec != self.nelec:
            raise ValueError('Given wavefunction does not have the same number of electrons as the'
                             ' the instantiated NonorthWavefunction.')
        elif wfn.dtype != self.dtype:
            raise ValueError('Given wavefunction does not have the same data type as the '
                             'instantiated NonorthWavefunction.')
        elif wfn.memory != self.memory:
            raise ValueError('Given wavefunction does not have the same memory as the '
                             'instantiated NonorthWavefunction.')
        self.wfn = wfn

    def assign_params(self, params=None):
        """Assign the orbital transformation matrix.

        Parameters
        ----------
        params : np.ndarray
            Transformation matrix

        Raises
        ------
        TypeError
            If transformation matrix is not a numpy array or 1- or 2-tuple/list of numpy arrays
            If transformation matrix is not a two dimension numpy array
            If transformation matrix is not a two dimension numpy array
        """
        if params is None:
            params = self.template_params

        if isinstance(params, np.ndarray):
            params = (params, )
        elif not (isinstance(params, (tuple, list)) and len(params) in [1, 2]):
            # FIXME: set orbtype? right now, the orbital type depends on the number of
            #        transformation matrices and they must match up with the hamiltonian
            # NOTE: maybe it's not a problem b/c orbital transformation is the only part that'll
            #       touch the different types of orbitals
            raise TypeError('Transformation matrix must be a two dimensional numpy array or a '
                            '1- or 2-tuple/list of two dimensional numpy arrays. Only one numpy '
                            'arrays indicate that the orbitals are restricted or generalized and '
                            'two numpy arrays indicate that the orbitals are unrestricted.')
        params = tuple(params)

        for i in params:
            if not (isinstance(i, np.ndarray) and len(i.shape) == 2):
                raise TypeError('Transformation matrix must be a two-dimensional numpy array.')
            elif i.dtype != self.dtype:
                raise TypeError('Transformation matrix must have the same data type as the given '
                                'wavefunction.')

            if (len(params) == 1 and
                not ((i.shape[0] == self.nspatial and i.shape[1] == self.wfn.nspatial) or
                     (i.shape[0] == self.nspin and i.shape[1] == self.wfn.nspin))):
                raise ValueError('Given the type of transformation, the numpy matrix has the '
                                 'wrong shape. If only one numpy array is given, the '
                                 'orbitals are transformed either from orthonormal spatial '
                                 'orbitals to nonorthonormal spatial orbitals or from '
                                 'orthonormal spin orbitals to nonorthonormal spin orbitals.')

            elif (len(params) == 2 and
                  not (i.shape[0] == self.nspatial and i.shape[1] == self.wfn.nspatial)):
                raise ValueError('Given the type of transformation, the numpy matrix has the '
                                 'wrong shape. If two numpy arrays are given, the orbitals are '
                                 'transformed from orthonormal spatial orbitals to nonorthonormal '
                                 'spatial orbitals.')

        self.params = params

    # FIXME: incredibly slow/bad approach
    def get_overlap(self, sd, deriv=None):
        """Return the overlap of the wavefunction with an orthonormal Slater determinant.

        A wavefunction built using nonorthonormal Slater determinants, :math:`\mathbf{n}`, can be
        expressed with respect to orthonormal Slater determinants, :math:`\mathbf{m}`:
        ..math::
            \ket{\Psi}
            &= \sum_{\mathbf{n}} f(\mathbf{n}) \sum_{\mathbf{m}} |U(\mathbf{m}, \mathbf{n})|^+
            \ket{\mathbf{m}}\\
            &= \sum_{\mathbf{m}} \sum_{\mathbf{n}} f(\mathbf{n}) |U(\mathbf{m}, \mathbf{n})|^+
            \ket{\mathbf{m}}
        Then, the overlap with an orthonormal Slater determinant is
        ..math::
            \braket{\Phi_i | \Psi}
            &= \sum_{\mathbf{n}} f(\mathbf{n}) |U(\Phi_i, \mathbf{n})|^+
        where :math:`U(\Phi_i, \mathbf{n})` is the transformation matrix with rows and columns that
        correspond to the Slater determinants :math:`\Phi_i` and :math:`\mathbf{n}`, respectively.

        Parameters
        ----------
        sd : int, mpz
            Slater Determinant against which to project.
        deriv : int
            Index of the parameter to derivatize
            Default does not derivatize

        Returns
        -------
        overlap : float

        Raises
        ------
        TypeError
            If given Slater determinant is not compatible with the format used internally
        """
        output = 0.0
        if self.orbtype == 'generalized':
            row_inds = slater.occ_indices(sd)
            all_col_inds = range(self.wfn.nspin)
            for col_inds in it.combinations(all_col_inds, self.nelec):
                nonorth_sd = slater.create(0, *col_inds)
                wfn_coeff = self.get_overlap(nonorth_sd, deriv=None)
                nonorth_coeff = np.linalg.det(self.params[0][row_inds, :][:, col_inds])
                output += wfn_coeff * nonorth_coeff
        else:
            alpha_sd, beta_sd = slater.split_spin(sd, self.nspatial)
            alpha_row_inds = slater.occ_indices(alpha_sd)
            beta_row_inds = slater.occ_indices(beta_sd)
            for alpha_col_inds in it.combinations(all_col_inds, len(alpha_row_inds)):
                alpha_coeff = np.linalg.det(self.params[0][alpha_row_inds, :][:, alpha_col_inds])
                for beta_col_inds in it.combinations(all_col_inds, len(beta_row_inds)):
                    if self.orbtype == 'restricted':
                        i = 0
                    elif self.orbtype == 'unrestricted':
                        i = 1
                    beta_coeff = np.linalg.det(self.params[i][beta_row_inds, :][:, beta_col_inds])
                    output += alpha_coeff * beta_coeff

        return output
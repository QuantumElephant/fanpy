from __future__ import absolute_import, division, print_function
from abc import ABCMeta, abstractproperty
import re

import numpy as np

# TODO: add custom exception class
class Wavefunction(object):
    """ Wavefunction class

    Contains the necessary information to projectively solve the wavefunction

    Attributes
    ----------
    dtype : {np.float64, np.complex128}
        Numpy data type
    H : np.ndarray(K,K)
        One electron integrals for the spatial orbitals
    Ha : np.ndarray(K,K)
        One electron integrals for the alpha spin orbitals
    Hb : np.ndarray(K,K)
        One electron integrals for the beta spin orbitals
    G : np.ndarray(K,K,K,K)
        Two electron integrals for the spatial orbitals
    Ga : np.ndarray(K,K,K,K)
        Two electron integrals for the alpha spin orbitals
    Gb : np.ndarray(K,K,K,K)
        Two electron integrals for the beta spin orbitals
    nuc_nuc : float
        Nuclear nuclear repulsion value
    nspatial : int
        Number of spatial orbitals
    nspin : int
        Number of spin orbitals (alpha and beta)
    nelec : int
        Number of electrons
    npair : int
        Number of electron pairs
        Assumes that the number of electrons is even
    nparticle : int
        Number of quasiparticles (electrons)
    ngeminal : int
        Number of geminals
    nproj : int
        Dimension of the projection space
    orb_type : {'restricted', 'unrestricted', 'generalized'}
        Type of the orbital used in obtaining the one-electron and two-electron integrals

    Private
    -------
    _nproj_default : int
        Default dimension of projection space
    _energy
    """
    __metaclass__ = ABCMeta

    #
    # Default attribute values
    #
    @abstractproperty
    def _methods(self):
        """ Dictionary of methods for solving the wavefunction

        Returns
        -------
        methods : dict
            Dictionary of the form {'method name':method}
            Must have key "default"
        """
        # this is an example
        def example_method():
            pass
        return {"default": example_method}

    #
    # Special methods
    #

    def __init__(
        self,
        # Mandatory arguments
        nelec=None,
        H=None,
        G=None,
        # Arguments handled by base Wavefunction class
        dtype=None,
        nuc_nuc=None,
        nparticle=None,
        odd_nelec=None,
        orb_type=None,
    ):
        """

        Required Parameters
        -------------------
        nelec : int
            Number of electrons
            Assumes that the number of electrons is even
        H : np.ndarray(K,K) or tuple np.ndarray(K,K)
            If np.ndarray, one electron integrals for the spatial orbitals
            If tuple of np.ndarray (length 2), one electron integrals for the alpha orbitals
            and one electron integrals for the alpha orbitals
        G : np.ndarray(K,K,K,K) or tuple np.ndarray(K,K)
            If np.ndarray, two electron integrals for the spatial orbitals
            If tuple of np.ndarray (length 2), two electron integrals for the alpha orbitals
            and two electron integrals for the alpha orbitals

        Optional Parameters
        -------------------
        dtype : {np.float64, np.complex128}
            Numpy data type
        nuc_nuc : float
            Nuclear nuclear repulsion value
        odd_nelec : int
            Odd number of electrons "remaining"
            Only when nelec is even
        nproj : int
            Number of projection states
        naproj : FIXME
        nrproj : FIXME
        orb_type : {'restricted', 'unrestricted', 'generalized'}
            Type of the orbital used in obtaining the one-electron and two-electron integrals
            Default is 'restricted'

        """
        # TODO: Implement loading H, G, and x from various file formats
        self.assign_dtype(dtype)
        self.assign_integrals(H, G, nuc_nuc=nuc_nuc)
        self.assign_particles(nelec, nparticle=nparticle, odd_nelec=odd_nelec)
        self.assign_orb_type(orb_type)

    def __call__(self,  method="default", **kwargs):
        """ Optimize coefficients
        """
        if method in self._methods:
            optimizer = self._methods[method.lower()]
            return optimizer(**kwargs)
        else:
            raise ValueError("method must be one of {0}".format(self._methods.keys()))

    #
    # Assignment methods
    #

    def assign_dtype(self, dtype):
        """ Sets the data type of the parameters

        Parameters
        ----------
        dtype : {np.float64, np.complex128}
            Numpy data type
        """

        if dtype is None:
            dtype = np.float64
        elif dtype not in (float, complex, np.float64, np.complex128):
            raise TypeError("dtype must be one of {0}".format((float, complex, np.float64, np.complex128)))

        self.dtype = dtype

    def assign_integrals(self, H, G, nuc_nuc=None):
        """ Sets one electron and two electron integrals, nuclear nuclear repulsion,
        number of spatial and pin orbitals, and renames unrestricted methods

        Parameters
        ----------
        H : np.ndarray(K,K) or tuple np.ndarray(K,K)
            If np.ndarray, one electron integrals for the spatial orbitals
            If tuple of np.ndarray (length 2), one electron integrals for the alpha orbitals
            and one electron integrals for the alpha orbitals
        G : np.ndarray(K,K,K,K) or tuple np.ndarray(K,K)
            If np.ndarray, two electron integrals for the spatial orbitals
            If tuple of np.ndarray (length 2), two electron integrals for the alpha orbitals
            and two electron integrals for the alpha orbitals
        nuc_nuc : float
            Nuclear nuclear repulsion value

        """

        # If unrestricted, H will be the tuple (Ha(lpha), Hb(eta)), and G, (Ga(lpha), Gb(eta))
        if not isinstance(H, (np.ndarray, tuple)):
            raise TypeError("H must be one of {0}".format((np.ndarray, tuple)))

        if not isinstance(G, type(H)):
            raise TypeError("G must be of the same type as H")

        matrices = []
        if isinstance(H, np.ndarray):
            unrestricted = False
            Ha = H
            Hb = H
            Ga = G
            Gb = G
            matrices = [H, G]
        else:
            unrestricted = True
            Ha, Hb = H
            Ga, Gb = G
            matrices = [Ha, Hb, Ga, Gb]

        for matrix in matrices:
            if not isinstance(matrix, np.ndarray):
                raise TypeError("Integral matrices must be of type {0}".format(np.ndarray))
            if not matrix.dtype in (float, complex, np.float64, np.complex128):
                raise TypeError("Integral matrices' dtypes must be one of {0}".format((float, complex, np.float64, np.complex128)))
            if not np.all(np.array(matrix.shape) == matrix.shape[0]):
                raise ValueError("Integral matrices' dimensions must all be equal")
            # NOTE: check symmetry?
            # NOTE: assumes number of alpha and beta spin orbitals are equal

        if not Ha.shape + Hb.shape == Ga.shape == Gb.shape:
            raise ValueError("Integral matrices shapes ({0}) are incompatible".format([matrix.shape for matrix in matrices]))

        # NOTE: why Ha? is self.H and self.G only going to be used in the restricted case?
        # NOTE: is Ha and Hb and Ga and Gb redundant?
        self.H = Ha
        self.Ha = Ha
        self.Hb = Hb
        self.G = Ga
        self.Ga = Ga
        self.Gb = Gb

        if nuc_nuc is None:
            nuc_nuc = 0.0
        elif not isinstance(nuc_nuc, (float, np.float64)):
            raise TypeError("nuc_nuc integral must be one of {0}".format((float, np.float64)))

        self.nuc_nuc = nuc_nuc

        # FIXME: turn into properties
        nspatial = Ha.shape[0]
        nspin = 2 * nspatial

        self.nspatial = nspatial
        self.nspin = nspin

        # Indicate that the object is to use its "_unrestricted_*" methods where available
        if unrestricted:
            self._configure_unrestricted()

    def assign_particles(self, nelec, nparticle=None, odd_nelec=None):
        """ Sets the number of electrons and particles

        Parameters
        ----------
        nelec : int
            Number of electrons
            Assumes that the number of electrons is even
        nparticle : int
            Number of quasiparticles (electrons)
        odd_nelec : int
            Odd number of electrons "remaining"
            Only when nelec is even
        """
        # NOTE: should this be moved to proj_wavefunction?

        if not isinstance(nelec, int):
            raise TypeError("nelec must be of type {0}".format(int))
        elif nelec < 0:
            raise ValueError("nelec must be a positive integer")
        elif odd_nelec is None and nelec % 2 != 0:
            raise ValueError("nelec must be even unless odd_nelec is set")

        # NOTE: what is this business with the odd_nelec?
        self.nelec = nelec
        # NOTE: discards odd electrons here
        # FIXME: turn into property
        self.npair = nelec // 2

        # NOTE: why?
        if nparticle is None:
            nparticle = nelec
        elif not isinstance(nparticle, int):
            raise TypeError("nparticle must be of type {0}".format(int))
        elif nparticle < 0:
            raise ValueError("nparticle must be a positive integer")
        elif nparticle % 2 != 0:
            raise ValueError("nparticle must be even")

        self.nparticle = nparticle
        # FIXME: turn into property
        self.ngeminal = nparticle // 2

    def assign_orb_type(self, orb_type):
        """ Assigns the orbital type use to construct the one-electron and two-electron
        integrals

        Parameters
        ----------
        orb_type : {'restricted', 'unrestricted', 'generalized'}
            Type of the orbital used in obtaining the one-electron and two-electron integrals
            Default is 'restricted'
        """
        if orb_type is None:
            orb_type = 'restricted'
        assert orb_type in ['restricted', 'unrestricted', 'generalized'], ''
        'Unsupported orbital type {0}'.format(orb_type)
        self.orb_type = orb_type


    #
    # Other methods
    #

    def _configure_unrestricted(self):
        """ Rename methods and attributes with "_restricted_" to "_unrestricted_"

        """
        regex = re.compile(r'^_restricted_')

        for attr in dir(self):
            if regex.match(attr):
                eval("self.{0} = self._unrestricted_{0}".format(attr))


    #
    # View methods
    #
    def compute_energy(self, sd=None, nuc_nuc=True, deriv=None):

        nuc_nuc = self.nuc_nuc if nuc_nuc else 0.0

        if sd is None:
            return self._energy + nuc_nuc

        else:
            # TODO: ADD HAMILTONIANS
            raise NotImplementedError

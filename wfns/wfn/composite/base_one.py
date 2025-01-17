"""Base class for composite wavefunctions that modifies one wavefunction."""
from wfns.wfn.base import BaseWavefunction


class BaseCompositeOneWavefunction(BaseWavefunction):
    """Base class for composite wavefunction that uses only one wavefunction.

    Attributes
    ----------
    nelec : int
        Number of electrons.
    nspin : int
        Number of spin orbitals (alpha and beta).
    dtype : {np.float64, np.complex128}
        Data type of the wavefunction.
    params : np.ndarray
        Parameters of the wavefunction.
    memory : float
        Memory available for the wavefunction.
    wfn : BaseWavefunction
        Wavefunction that is being modified.

    Properties
    ----------
    nparams : int
        Number of parameters.
    nspatial : int
        Number of spatial orbitals
    param_shape : tuple of int
        Shape of the parameters.
    spin : int
        Spin of the wavefunction.
    seniority : int
        Seniority of the wavefunction.

    Methods
    -------
    __init__(self, nelec, nspin, dtype=None, memory=None)
        Initialize the wavefunction.
    assign_nelec(self, nelec)
        Assign the number of electrons.
    assign_nspin(self, nspin)
        Assign the number of spin orbitals.
    assign_dtype(self, dtype)
        Assign the data type of the parameters.
    assign_memory(self, memory=None):
        Assign memory available for the wavefunction.
    assign_params(self, params)
        Assign parameters of the wavefunction.
    load_cache(self)
        Load the functions whose values will be cached.
    clear_cache(self)
        Clear the cache.

    Abstract Properties
    -------------------
    template_params : np.ndarray
        Default parameters of the wavefunction.

    Abstract Methods
    ----------------
    get_overlap(self, sd, deriv=None) : float
        Return the overlap of the wavefunction with a Slater determinant.

    """

    # pylint: disable=W0223
    def __init__(self, nelec, nspin, wfn, dtype=None, memory=None, params=None):
        """Initialize the wavefunction.

        Parameters
        ----------
        nelec : int
            Number of electrons.
        nspin : int
            Number of spin orbitals.
        dtype : {float, complex, np.float64, np.complex128, None}
            Numpy data type.
            Default is `np.float64`.
        memory : {float, int, str, None}
            Memory available for the wavefunction.
            Default does not limit memory usage (i.e. infinite).
        wfn : BaseWavefunction
            Wavefunction that will be modified.

        """
        super().__init__(nelec, nspin, dtype=dtype, memory=memory)
        self.assign_wfn(wfn)
        self.assign_params(params)
        self._cache_fns = {}
        self.load_cache()

    def assign_wfn(self, wfn):
        """Assign the wavefunction.

        Parameters
        ----------
        wfn : BaseWavefunction
            Wavefunction that will be modified.

        Raises
        ------
        TypeError
            If the given wavefunction is not an instance of BaseWavefunction.
        ValueError
            If the given wavefunction does not have the same number of electrons as the initialized
            value.
            If the given wavefunction does not have the same data type as the initialized value.
            If the given wavefunction does not have the same memory as the initialized value.

        """
        if not isinstance(wfn, BaseWavefunction):
            raise TypeError("Given wavefunction must be an instance of BaseWavefunction.")
        if wfn.nelec != self.nelec:
            raise ValueError(
                "Given wavefunction does not have the same number of electrons as the"
                " the instantiated NonorthWavefunction."
            )
        if wfn.dtype != self.dtype:
            raise ValueError(
                "Given wavefunction does not have the same data type as the "
                "instantiated NonorthWavefunction."
            )
        if wfn.memory != self.memory:
            raise ValueError(
                "Given wavefunction does not have the same memory as the "
                "instantiated NonorthWavefunction."
            )
        self.wfn = wfn

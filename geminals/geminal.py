#!/usr/bin/env python2

from __future__ import absolute_import, division, print_function

import numpy as np
from itertools import combinations, permutations
from scipy.optimize import root
from slater_det import excite_orbs, excite_pairs, is_pair_occupied, is_occupied


class APIG(object):
    """
    Attributes
    ----------
    npairs : int
        Number of electron pairs
    norbs : int
        Number of spatial orbitals
    coeffs :
    pspace :
        Projection space
        Tuple of integers that, in binary, describes which spin orbitals are
        used to build the Slater determinant
        The 1's in the even positions describe alpha orbitals
        The 1's in the odd positions describe beta orbitals

    Notes
    -----
    Slater determinants are expressed by an integer that, in binary form,
    shows which spin orbitals are used to construct it. The position of each '1'
    from the right is the index of the orbital that is included in the Slater
    determinant. The even positions (i.e. 0, 2, 4, ...) are the alpha orbitals,
    and the odd positions (i.e. 1, 3, 5, ...) are the beta orbitals.
    e.g. 5=0b00110011 is a Slater determinant constructed with the
    0th and 2nd spatial orbitals, or the 0th, 1st, 5th, 6th spin orbitals (where
    the spin orbitals are ordered by the alpha beta pairs)

    The number of electrons is assumed to be even
    """

    # Class-wise behaviour-defining variables
    _exclude_ground = False
    _normalize = True


    def __init__(self, npairs, norbs, ham=None, pspace=None):
        """
        Parameters
        ----------
        npairs : int
            Number of electron pairs
        norbs : int
            Number of spatial orbitals
        ham : 2-tuple of np.ndarrays
            writing docs sucks...
        pspace : {None, iterable of int}
            Projection space
            Iterable of integers that, in binary, describes which spin orbitals are
            used to build the Slater determinant
            The 1's in the even positions describe alpha orbitals
            The 1's in the odd positions describe beta orbitals
            By default, a projection space is generated using generate_pspace
        """

        # Private variables
        self._npairs = None
        self._norbs = None
        self._ham = None
        self._pspace = None
        self._coeffs = None
        self._coeffs_optimized = False
        self._orbitals_optimized = False

        # Assign the attributes their values using the setters
        self.norbs = norbs
        self.npairs = npairs
        self.ham = ham
        self.pspace = pspace if pspace else self.generate_pspace()


    def __call__(self, **kwargs):

        # Update default options
        defaults = {
                     'x0': None,
                     'jac': None,
                     'proj': None,
                     'options': None,
                     'verbose': False,
                   }
        if kwargs:
            defaults.update(kwargs)
        solveropts = {
                       'xatol': 1.0e-12,
                       'method': 'hybr',
                     }
        if defaults['options']:
            solveropts.update(defaults['options'])

        # Process `x0` (coefficients guess) options
        x0 = defaults['x0']
        # "is None" must be explicit here because np.ndarrays overwrite boolean ops
        if x0 is None:
            x0 = self.generate_guess()

        # Process `jac` options
        jac = defaults['jac']
        if jac:
            jac = self.nonlin_jac

        # Process `proj` options
        proj = defaults['proj']
        if not proj:
            proj = list(self.pspace)
            proj.remove(self.ground)
        if len(proj) < x0.size:
            raise ValueError("'proj' is too short, the system is underdetermined.")

        # Run the solver
        result = root( self.nonlin,
                       x0,
                       jac=jac,
                       args=(proj,),
                       options=solveropts,
                     )

        # Update if successful, or else print a warning
        if result['success']:
            self.coeffs = result['x']
        else:
            print("Warning: solution did not converge; coefficients were not updated.")

        # Display some information
        if defaults['verbose']:
            print(10*"=" + " OLSENS RESULTS " + 10*"=")
            print("Number of objective function evaluations: {}".format(result['nfev']))
            if 'njev' in result:
                print("Number of Jacobian evaluations: {}".format(result['njev']))
            svd_u, svd_jac, svd_v = np.linalg.svd(result['fjac'])
            svd_value = max(svd_jac)/min(svd_jac)
            print("max(SVD)/min(SVD) [closer to 1 is better]: {}".format(svd_value))
            print(10*"=" + "================" + 10*"=")

        return result


    @property
    def _row_indices(self):
        return range(0,self.npairs)


    @property
    def _col_indices(self):
        return range(0,self.norbs)


    @property
    def npairs(self):
        """ Number of electron pairs

        Returns
        -------
        npairs : int
            Number of electron pairs
        """

        return self._npairs


    @npairs.setter
    def npairs(self, value):
        """ Sets the number of Electron Pairs

        Parameters
        ----------
        value : int
            Number of electron pairs

        Raises
        ------
        AssertionError
            If number of electron pairs is a float
            If number of electron pairs is less than or equal to zero
            If fractional number of electron pairs is given
        """

        assert isinstance(value, int), 'There can only be integral number of electron pairs'
        assert value > 0, 'Number of electron pairs cannot be less than or equal to zero'
        assert value <= self.norbs,\
        'Number of number of electron pairs must be less than the number of spatial orbitals'
        self._npairs = value


    @property
    def norbs(self):
        """ Number of spatial orbitals

        Returns
        -------
        norbs : int
            Number of spatial orbitals
        """

        return self._norbs


    @norbs.setter
    def norbs(self, value):
        """ Sets the number of spatial orbitals

        Parameters
        ----------
        value : int
            Number of spatial orbitals

        Raises
        ------
        AssertionError
            If fractional number of spatial orbitals is given
        """

        assert isinstance(value, int), \
            "There can only be integral number of spatial orbitals"
        assert value >= self.npairs, \
            "Number of spatial orbitals must be greater than the number of electron pairs"
        self._norbs = value


    @property
    def ham(self):
        return self._ham


    @ham.setter
    def ham(self, value):
        # Check if one and two electron integrals are expressed wrt spatial mo's
        assert (4 > len(value) > 1), \
            "`ham` is too long (2 or 3 elements expected, {} given.".format(len(value))
        assert isinstance(value[0], np.ndarray) and isinstance(value[1], np.ndarray), \
                "One- and two- electron integrals must be numpy ndarrays."
        if len(value) == 3:
            assert isinstance(value[2], float), \
                "If core energy is specified, it must be a float."
        assert value[0].shape == tuple([self.norbs]*2),\
            ('One electron integral is not expressed with respect to the right'
             ' number of spatial molecular orbitals')
        assert value[1].shape == tuple([self.norbs]*4),\
            ('Two electron integral is not expressed with respect to the right'
             ' number of spatial molecular orbitals')
        # Check if Hermitian
        assert np.allclose(value[0], value[0].T), \
            'One electron integral matrix is not symmetric'
        assert np.allclose(value[1], np.einsum('jilk', value[1])),\
            ('Two electron integral matrix does not satisfy <ij|kl> = <ji|lk>'
             " or is not in physicist's notation")
        assert np.allclose(value[1], np.conjugate(np.einsum('klij', value[1]))),\
            ('Two electron integral matrix does not satisfy <ij|kl> = <kl|ij>^*'
             " or is not in physicist's notation")
        self._ham = value


    @property
    def pspace(self):
        """ Projection space

        Returns
        -------
        List of integers that, in binary, describes which spin orbitals are
        used to build the Slater determinant
        The 1's in the even positions describe alpha orbitals
        The 1's in the odd positions describe beta orbitals

        """

        return self._pspace


    @pspace.setter
    def pspace(self, list_sds):
        """ Sets the projection space

        Parameters
        ----------
        list_sds : list of int
            List of integers that, in binary, describes which spin orbitals are
            used to build the Slater determinant
            The 1's in the even positions describe alpha orbitals
            The 1's in the odd positions describe beta orbitals

        Raises
        ------
        AssertionError
            If any of the Slater determinants contains more orbitals than the number of electrons
            If any of the Slater determinants is unrestricted (not all alpha beta pairs are
            both occupied)
            If any of the Slater determinants has spin orbitals whose indices exceed the given
            number of spatial orbitals
        """

        assert hasattr(list_sds, '__iter__')

        for sd in list_sds:
            bin_string = bin(sd)[2:]
            # Add zeros on the left so that bin_string has even numbers
            bin_string = '0'*(len(bin_string)%2) + bin_string
            # Check that number of orbitals used to create spin orbitals is equal to number
            # of electrons
            assert bin_string.count('1') == self.nelec, \
            'Given Slater determinant does not contain the same number of orbitals as the given number of electrons'

            # Check that adjacent orbitals in the Slater determinant are alpha beta pairs
            # i.e. all spatial orbitals are doubly occupied
            # There must be single excitations if number of electron pairs <= 2
            if self.npairs > 2:
                alpha_occ = bin_string[0::2]
                beta_occ = bin_string[1::2]
                assert alpha_occ == beta_occ, "Given Slater determinant is unrestricted"

            # Check that there are no orbitals are used that are outside of the
            # specified number (norbs)
            index_last_spin = len(bin_string)-1-bin_string.index('1')
            index_last_spatial = index_last_spin//2
            assert index_last_spatial < self.norbs,\
            ('Given Slater determinant contains orbitals whose indices exceed the '
             'given number of spatial orbitals')

        self._pspace = tuple(list_sds)


    @property
    def nelec(self):
        """ Number of electrons

        Returns
        -------
        nelec : int
            Number of electrons
        """

        return 2*self.npairs


    @property
    def ground(self):
        return int(2*self.npairs*"1", 2)

    @property
    def coeffs(self):
        return self._coeffs

    @coeffs.setter
    def coeffs(self, value):
        assert value.size == self.npairs*self.norbs,\
                ('Given geminals coefficient matrix does not have the right number of '
                 'coefficients')
        self._coeffs = value.reshape(self.npairs, self.norbs)


    def generate_pspace(self):
        """ Generates a well determined projection space

        Returns
        -------
        tuple_sd : tuple of int
            Tuple of integers that in binary describes the orbitals used to make the Slater
            determinant

        Raises
        ------
        AssertionError
            If the same Slater determinant is generated more than once
            If not enough Slater determinants can be generated

        Note
        ----
        We need to have npairs*norbs+1 dimensional projection space
        First is the ground state HF slater determinant (using the first npair
        spatial orbitals) [1]
        Then, all single pair excitations from any occupieds to any virtuals
        (ordered HOMO to lowest energy for occupieds and LUMO to highest energy
        for virtuals)
        Then, all double excitations of the appropriate number of HOMOs to
        appropriate number of LUMOs. The appropriate number is the smallest number
        that would generate the remaining slater determinants. This number will
        maximally be the number of occupied spatial orbitals.
        Then all triple excitations of the appropriate number of HOMOs to
        appropriate number of LUMOs

        It seems that certain combinations of npairs and norbs is not possible
        because we are assuming that we only use pair excitations. For example,
        a 2 electron system cannot ever have appropriate number of Slater determinants,
        a 4 electron system must have 6 spatial orbitals,
        a 6 electron system must have 6 spatial orbitals.
        a 8 electron system must have 7 spatial orbitals.

        If we treat E as a parameter
        """
        list_sd = []
        # convert string of a binary into an integer
        hf_ground = int('1'*2*self.npairs, 2)
        list_sd.append(hf_ground)
        ind_occ = [i for i in range(self.norbs) if is_pair_occupied(hf_ground, i)]
        ind_occ.reverse() # reverse ordering to put HOMOs first
        ind_vir = [i for i in range(self.norbs) if not is_pair_occupied(hf_ground, i)]
        num_needed = self.npairs*self.norbs+1
        # Add pair excitations
        num_excited = 1
        num_combs = lambda n, r: np.math.factorial(n)/np.math.factorial(r)/np.math.factorial(n-r)
        while len(list_sd) < num_needed and num_excited <= len(ind_occ):
            # Find out what is the smallest number of frontier orbitals (HOMOS and LUMOs)
            # that can be used
            for i in range(2, len(ind_occ)+1):
                if num_combs(i, 2)**2 >= num_needed-len(list_sd):
                    num_frontier = i
                    break
            else:
                num_frontier = max(len(ind_occ), len(ind_vir))+1
            # Add excitations from all possible combinations of num_frontier of HOMOs
            for occs in combinations(ind_occ[:num_frontier], num_excited):
                # to all possible combinations of num_frontier of LUMOs
                for virs in combinations(ind_vir[:num_frontier], num_excited):
                    occs_virs = list(occs) + list(virs)
                    list_sd.append(excite_pairs(hf_ground, *occs_virs))
            num_excited += 1
        # Add single excitations (Needed for systems with less than 2 electron pairs)
        #  Excite betas to alphas
        if self.npairs <= 2:
            for i in ind_occ:
                for j in ind_vir:
                    list_sd.append(excite_orbs(hf_ground, i*2+1, j*2))
        # Check
        assert len(list_sd) == len(set(list_sd)),\
            ('Woops, something went wrong. Same Slater determinant was generated '
             'more than once')
        assert len(list_sd) >= num_needed, \
            'Could not generate enough Slater determinants'
        # Truncate and return
        return tuple(list_sd[:num_needed])


    def generate_guess(self):
        print("Generating guess from AP1roG...")
        gem = AP1roG(self.npairs, self.norbs, ham=self.ham)
        gem()
        print("AP1roG guess for APIG generated.")
        return gem.coeffs.ravel()


    @staticmethod
    def permanent(matrix):
        """ Calculates the permanent of a matrix

        Parameters
        ----------
        matrix : np.ndarray(N,N)
            Two dimensional square numpy array

        Returns
        -------
        permanent : float

        Raises
        ------
        AssertionError
            If matrix is not square
        """
        assert matrix.shape[0] is matrix.shape[1], \
            "Cannot compute the permanent of a non-square matrix."
        permanent = 0
        row_indices = range(matrix.shape[0])
        for col_indices in permutations(row_indices):
            permanent += np.product(matrix[row_indices, col_indices])
        return permanent


    @staticmethod
    def permanent_derivative(matrix, i, j):
        """ Calculates the partial derivative of a permanent with respect to one of its
        coefficients

        Parameters
        ----------
        matrix : np.ndarray(N,N)
            Two dimensional square numpy array
        i : int
            `i` in the indices (i, j) of the coefficient with respect to which the partial
            derivative is computed
        j : int
            See `i`.

        Returns
        -------
        derivative : float

        Raises
        ------
        AssertionError
            If matrix is not square
        """
        assert matrix.shape[0] is matrix.shape[1], \
            "Cannot compute the permanent of a non-square matrix."

        # Permanent is invariant wrt row/column exchange; put coefficient (i,j) at (0,0)
        rows = list(range(matrix.shape[0]))
        cols = list(range(matrix.shape[1]))
        if i is not 0:
            rows[0], rows[i] = rows[i], rows[0]
        if j is not 0:
            cols[0], cols[j] = cols[j], cols[0]

        # Get values of the permutations that include the coefficient (i,j) by
        # multiplying along left- and right- hand diagonals, wrapping around where
        # necessary.  Don't actually include coeff (i,j) since it is differentiated out.
        left = matrix.shape[1] - 1
        right = 1
        prod_l = prod_r = 1
        for row in range(1,matrix.shape[0]):
            prod_l *= matrix[rows,:][:,cols][row, left]
            prod_r *= matrix[rows,:][:,cols][row, right]
            left -= 1
            right += 1
        return prod_l + prod_r


    def overlap(self, slater_det, gem_coeff, derivative=False, indices=None):
        """ Calculate the overlap between a slater determinant and geminal wavefunction

        Parameters
        ----------
        slater_det : int
            Integers that, in binary, describes the orbitals used to make the Slater
            determinant
        gem_coeff : np.ndarray(P,K)
            Coefficient matrix for the geminal wavefunction
        derivative : bool, optional
            Whether to compute the partial derivative of the overlap with respect to a
            geminal coefficient, rather than the overlap itself.
        indices : 2-tuple of ints, optional
            If taking the derivative, with respect to which coefficient?

        Returns
        -------
        overlap : float
            Overlap between the slater determinant and the geminal wavefunction

        """
        # If bad Slater determinant
        if slater_det is None:
            return 0
        # If Slater determinant has different number of electrons
        elif bin(slater_det).count('1') != self.nelec:
            return 0
        # If Slater determinant has any of the (of the alpha beta pair) alpha
        # and beta orbitals do not have the same occupation
        elif any(is_occupied(slater_det, i*2) != is_occupied(slater_det, i*2+1)
                 for i in range(self.norbs)):
            return 0
        # Else
        else:
            ind_occ = [i for i in range(self.norbs) if is_pair_occupied(slater_det, i)]
            # If we're taking a derivative wrt a coefficient appearing in the permanent:
            if derivative:
                if indices[1] in ind_occ:
                    indices = (indices[0],ind_occ.index(indices[1]))
                    return self.permanent_derivative(gem_coeff[:, ind_occ], *indices)/2.0
                return 0
            # If not deriving wrt a coefficient appearing in the permanent,just return
            # the permanent
            return self.permanent(gem_coeff[:, ind_occ])


    def phi_H_psi(self, slater_det, gem_coeff):
        """ Integrates the Slater determinant with a Geminal wavefunction

        Parameters
        ----------
        slater_det : int
        gem_coeff : np.ndarray(P,K)
        one : np.ndarray(K,K)
            One electron integral in the orthogonal spatial basis from which the
            geminals are constructed
        two : np.ndarray(K,K,K,K)
            Two electron integral in the orthogonal spatial basis from which the
            geminals are constructed

        Returns
        -------
        integral : float

        Notes
        -----
        Assume molecular orbitals are restricted spatial orbitals

        """

        bin_string = bin(slater_det)[2:]
        # Add zeros on the left so that bin_string has even numbers
        bin_string = '0'*(len(bin_string)%2) + bin_string
        alpha_occ = bin_string[0::2]
        beta_occ = bin_string[1::2]

        # if all the occupied spin orbitals are alpha beta pairs
        if alpha_occ == beta_occ:
            return self.double_phi_H_psi(slater_det, gem_coeff)
        else:
            return self.brute_phi_H_psi(slater_det, gem_coeff)


    def double_phi_H_psi(self, slater_det, gem_coeff):
        """ Integrates the Slater determinant with a Geminal wavefunction

        Assuming that the molecular orbitals are spatial orbitals,
        the only integral elements that contribute are:

        ..math::

            h_{ii}, h_{\bar{i}\bar{i}}, g_{i\bar{i}i\bar{i}}, g_{ijij},
            g_{\bar{i}\bar{j}\bar{i}\bar{j}}, g_{i\bar{j}i\bar{j}}, g_{\bar{i}j\bar{i}j}
            g_{i\bar{i}a\bar{a}}

        where :math: `g_{ijkl} = V_{ijkl} - V_{ijlk}`,
              i and j's are indices for the occupied orbitals
              a is the index for the virtual orbitals
        Since :math: `V_{i\bar{i}\bar{i}i}, V_{i\bar{j}\bar{j}i}, V_{\bar{i}jj\bar{i}}` are all zero,
        and since the alpha and beta parts are identical

        ..math::

        H = \sum_i (2*h_{ii} + V_{i\bar{i}i\bar{i}}) +
            \sum_{ij} (4*V_{ijij} - 2*V_{ijji} +
            \sum_{ia} V_{i\bar{i}a\bar{a}}

        Parameters
        ----------
        slater_det : int
        gem_coeff : np.ndarray(P,K)
        one : np.ndarray(K,K)
            One electron integral in the orthogonal spatial basis from which the
            geminals are constructed
        two : np.ndarray(K,K,K,K)
            Two electron integral in the orthogonal spatial basis from which the
            geminals are constructed

        Returns
        -------
        integral : float

        Notes
        -----
        Assume molecular orbitals are restricted spatial orbitals
        Assumes that the Slater determinant is a pairwise excitation of the ground
        state HF Slater determinant
        """

        one, two = self.ham

        one_elec_part = 0.0
        coulomb  = 0.0
        exchange = 0.0
        
        olp = self.overlap(slater_det, gem_coeff)
        for i in range(self.norbs):
            if is_pair_occupied(slater_det, i):
                one_elec_part += 2*one[i, i]*olp
                coulomb  += two[i, i, i, i]*olp

                for j in range(i + 1, self.norbs):
                    if is_pair_occupied(slater_det, j):
                        coulomb  += 4*two[i, j, i, j]*olp
                        exchange -= 2*two[i, j, j, i]*olp

                for a in range(self.norbs):
                    if not is_pair_occupied(slater_det, a):
                        excitation = excite_pairs(slater_det, i, a)
                        coulomb += two[i, i, a, a]*self.overlap(excitation, gem_coeff)

        return one_elec_part + coulomb + exchange


    def brute_phi_H_psi(self, slater_det, gem_coeff):
        """ Integrates the Slater determinant with a Geminal wavefunction

        Parameters
        ----------
        slater_det : int
        gem_coeff : np.ndarray(P,K)
        one : np.ndarray(K,K)
            One electron integral in the orthogonal spatial basis from which the
            geminals are constructed
        two : np.ndarray(K,K,K,K)
            Two electron integral in the orthogonal spatial basis from which the
            geminals are constructed
            In physicist's notation

        Returns
        -------
        integral : float

        Notes
        -----
        Assume molecular orbitals are restricted spatial orbitals
        Makes no assumption about the slater_det structure and brute forces
        One and Two electron integrals are expressed wrt spatial orbitals.
        Assumes the one and two electron integrals are Hermitian
        """

        one, two = self.ham

        # spin indices
        ind_occ = [i for i in range(2*self.norbs) if is_occupied(slater_det, i)]
        ind_vir = [i for i in range(2*self.norbs) if not is_occupied(slater_det, i)]
        one_elec_part = 0.0
        coulomb = 0.0
        exchange = 0.0
        ind_first_occ = 0
        for i in ind_occ:
            ind_first_vir = 0
            # add index i to ind_vir because excitation to same orbital is possible
            temp1_ind_vir = sorted(ind_vir+[i])
            for k in temp1_ind_vir:
                single_excitation = excite_orbs(slater_det, i, k)
                if i%2 == k%2:
                    one_elec_part += one[i//2, k//2]*self.overlap(single_excitation, gem_coeff)
                # avoid repetition by making j>i
                for j in ind_occ[ind_first_occ+1:]:
                    # add index i and j to ind_vir because excitation to same orbital is possible
                    # avoid repetition by making l>k
                    temp2_ind_vir = sorted([j] + temp1_ind_vir[ind_first_vir+1:])
                    for l in temp2_ind_vir:
                        double_excitation = excite_orbs(single_excitation, j, l)
                        overlap = self.overlap(double_excitation, gem_coeff)
                        if overlap == 0:
                            continue
                        # in \braket{ij|kl},
                        # i and k must have the same spin
                        # j and l must have the same spin
                        if i%2 == k%2 and j%2 == l%2:
                            coulomb += two[i//2, j//2, k//2, l//2]*overlap
                        # in \braket{ij|lk},
                        # i and l must have the same spin
                        # j and k must have the same spin
                        if i%2 == l%2 and j%2 == k%2:
                            exchange -= two[i//2, j//2, l//2, k//2]*overlap
                ind_first_vir += 1
            ind_first_occ += 1
        return one_elec_part + coulomb + exchange


    def construct_guess(self, x0):
        C = x0.reshape(self.npairs, self.norbs)
        return C


    def nonlin(self, x0, proj):

        one, two = self.ham

        # Handle differences in indexing between geminal methods
        eqn_offset = int(self._normalize)

        C = self.construct_guess(x0)
        energy = self.phi_H_psi(self.ground, C)
        vec = np.zeros(x0.size)
        if self._normalize:
            vec[0] = self.overlap(self.ground, C) - 1.0

        for d in range(x0.size - eqn_offset):
            vec[d + eqn_offset] = energy*self.overlap(proj[d], C) - self.phi_H_psi(proj[d], C)

        return np.array(vec)


    def nonlin_jac(self, x0, proj):
        """ Constructs the Jacobian of the function `nonlin`:

        Assuming that the molecular orbitals are spatial orbitals,
        the only integral elements that contribute are:

        Parameters
        ----------
        x0 : np.ndarray(P*K)
            The (raveled) geminal coefficient matrix.
        one : np.ndarray(K,K)
            One electron integral in the orthogonal spatial basis from which the
            geminals are constructed
        two : np.ndarray(K,K,K,K)
            Two electron integral in the orthogonal spatial basis from which the
            geminals are constructed

        Returns
        -------
        jac : np.ndarray(n_pspace,P*K)
            The Jacobian of the (raveled) geminal coefficients for the Projected
            Schrodinger Equation.
        """

        one, two = self.ham

        # Handle differences in indexing between geminal methods
        eqn_offset = int(self._normalize)

        # Initialize Jacobian tensor and some temporary values
        # (J)_dij = d(F_d)/d(c_ij)
        jac = np.zeros((x0.size, x0.size))
        phi_psi_tmp = np.zeros(x0.size)
        C = self.construct_guess(x0)

        # The objective functions {F_d} are of this form:
        # F_d = (d<phi0|H|psi>/dc_ij)*<phi'|psi>/dc_ij
        #           + <phi0|H|psi>*(d<phi'|psi>/dc_ij) - d<phi'|H|psi>/dc_ij

        # Compute the undifferentiated parts
        energy = self.phi_H_psi(self.ground, C)
        for d in range(x0.size):
            phi_psi_tmp[d] = self.overlap(proj[d], C)

        # Compute the differentiated parts; this works by overwriting the geminal's
        # `overlap` method to be the method that describes its PrSchEq's partial
        # derivative wrt coefficient c_ij; we must back up the original method
        tmp_olp = self.overlap

        # Overwrite `overlap` to take the correct partial derivative
        count = 0
        for i in self._row_indices:
            for j in self._col_indices:
                coords = (i, j)
                def olp_der(sd, gc, overwrite=coords):
                    return tmp_olp(sd, gc, derivative=True, indices=overwrite)
                self.overlap = olp_der
                if self._normalize:
                    jac[0, count] = self.overlap(self.ground, C)

                # Compute the differentiated parts and construct the whole Jacobian
                for d in range(x0.size - eqn_offset):
                    jac[d + eqn_offset, count] = self.phi_H_psi(self.ground, C)*phi_psi_tmp[d] \
                                               + energy*self.overlap(proj[d], C) \
                                               - self.phi_H_psi(proj[d], C)
                count += 1

        # Replace the original `overlap` method and return the Jacobian
        self.overlap = tmp_olp

        # If gg/def overlap
        return jac



class AP1roG(APIG):

    # Class-wide variables for class behaviour
    _exclude_ground = True
    _normalize = False


    @property
    def _row_indices(self):
        return range(0,self.npairs)


    @property
    def _col_indices(self):
        return range(self.npairs,self.norbs)


    @property
    def coeffs(self):
        return self._coeffs


    @coeffs.setter
    def coeffs(self, value):
        assert value.size == self.npairs*(self.norbs - self.npairs), \
                ('Given geminals coefficient matrix does not have the right number of '
                 'coefficients')
        coeffs = np.eye(self.npairs, M=self.norbs)
        coeffs[:,self.npairs:] += value.reshape(self.npairs, self.norbs - self.npairs)
        self._coeffs = coeffs


    def generate_pspace(self):
        """ Generates the projection space

        Returns
        -------
        pspace : list
            List of numbers that in binary describes the occupations
        """
        base = sum([ 2**(2*i) + 2**(2*i + 1) for i in range(self.npairs) ])
        pspace = [base]
        for unoccup in range(self.npairs, self.norbs):
            for i in range(self.npairs):
            # Python's sum is used here because NumPy's sum doesn't respect
            # arbitrary-precision Python longs

            # pspace = all single pair excitations
                pspace.append(excite_pairs(base, i, unoccup))
        # Uniquify
        return tuple(set(pspace))


    def generate_guess(self):
        params = self.npairs*(self.norbs - self.npairs)
        return (2.0/np.around(10*params, -1))*(np.random.rand(params) - 0.5)


    def construct_guess(self, x0):
        C = np.eye(self.npairs, M=self.norbs)
        C[:,self.npairs:] += x0.reshape(self.npairs, self.norbs - self.npairs)
        return C


    def overlap(self, phi, matrix, derivative=False, indices=None):
        if phi == 0:
            return 0
        elif phi not in self.pspace:
            return 0
        else:
            from_index = []
            to_index = []
            excite_count = 0
            for i in range(self.npairs):
                if not is_pair_occupied(phi, i):
                    excite_count += 1
                    from_index.append(i)
            for i in range(self.npairs, self.norbs):
                if is_pair_occupied(phi, i):
                    to_index.append(i)

            if excite_count == 0:
                if derivative:
                    if indices[0] == indices[1]:
                        return 1
                    return 0
                return 1
            elif excite_count == 1:
                if derivative:
                    if indices == (from_index[0], to_index[0]):
                        return 1
                    return 0
                return matrix[from_index[0], to_index[0]]
            elif excite_count == 2:
                if derivative:
                    if indices == (from_index[0], to_index[0]):
                        return matrix[from_index[1], to_index[1]]
                    elif indices == (from_index[1], to_index[1]):
                        return matrix[from_index[0], to_index[0]]
                    elif indices == (from_index[0], to_index[1]):
                        return -matrix[from_index[1], to_index[0]]
                    elif indices == (from_index[1], to_index[0]):
                        return -matrix[from_index[0], to_index[1]]
                    return 0
                overlap = matrix[from_index[0], to_index[0]] * \
                          matrix[from_index[1], to_index[1]]
                overlap -= matrix[from_index[0], to_index[1]] * \
                           matrix[from_index[1], to_index[0]]
                return overlap
            else:
                raise Exception(str(excite_count))


# vim: set textwidth=90 :

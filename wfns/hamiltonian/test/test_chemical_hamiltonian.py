"""Test wfns.hamiltonian.chemical_hamiltonian."""
import numpy as np
from nose.plugins.attrib import attr
from nose.tools import assert_raises
from wfns.hamiltonian.chemical_hamiltonian import ChemicalHamiltonian
from wfns.wavefunction.ci.ci_wavefunction import CIWavefunction
from wfns.tools import find_datafile
from wfns.backend.sd_list import sd_list


class Empty:
    pass


def test_assign_orbtype():
    """Test ChemicalHamiltonian.assign_orbtype."""
    # default option
    test = Empty()
    ChemicalHamiltonian.assign_orbtype(test)
    assert test.orbtype == 'restricted'

    test = Empty()
    ChemicalHamiltonian.assign_orbtype(test, None)
    assert test.orbtype == 'restricted'

    # bad option
    test = Empty()
    assert_raises(TypeError, ChemicalHamiltonian.assign_orbtype, test, 'Restricted')
    assert_raises(TypeError, ChemicalHamiltonian.assign_orbtype, test, 'unrestricteD')
    assert_raises(TypeError, ChemicalHamiltonian.assign_orbtype, test, 'sdf')

    # explicit option
    test = Empty()
    ChemicalHamiltonian.assign_orbtype(test, 'restricted')
    assert test.orbtype == 'restricted'

    test = Empty()
    ChemicalHamiltonian.assign_orbtype(test, 'unrestricted')
    assert test.orbtype == 'unrestricted'

    test = Empty()
    ChemicalHamiltonian.assign_orbtype(test, 'generalized')
    assert test.orbtype == 'generalized'


def test_assign_energy_nuc_nuc():
    """Test ChemicalHamiltonian.assign_energy_nuc_nuc."""
    # default option
    test = Empty()
    ChemicalHamiltonian.assign_energy_nuc_nuc(test)
    assert test.energy_nuc_nuc == 0.0

    test = Empty()
    ChemicalHamiltonian.assign_energy_nuc_nuc(test, None)
    assert test.energy_nuc_nuc == 0.0

    # explicit option
    test = Empty()
    ChemicalHamiltonian.assign_energy_nuc_nuc(test, 0)
    assert test.energy_nuc_nuc == 0.0

    test = Empty()
    ChemicalHamiltonian.assign_energy_nuc_nuc(test, 1.5)
    assert test.energy_nuc_nuc == 1.5

    test = Empty()
    ChemicalHamiltonian.assign_energy_nuc_nuc(test, np.inf)
    assert test.energy_nuc_nuc == np.inf

    # bad option
    test = Empty()
    assert_raises(TypeError, ChemicalHamiltonian.assign_energy_nuc_nuc, test, [-2])
    assert_raises(TypeError, ChemicalHamiltonian.assign_energy_nuc_nuc, test, '2')


def test_assign_integrals():
    """Test ChemicalHamiltonian.assign_integrals."""
    # good input
    one_int = np.random.rand(4, 4)
    two_int = np.random.rand(4, 4, 4, 4)
    test = Empty()
    ChemicalHamiltonian.assign_orbtype(test, 'restricted')
    ChemicalHamiltonian.assign_integrals(test, one_int, two_int)
    assert np.allclose(test.one_int.integrals, (one_int, ))
    assert np.allclose(test.two_int.integrals, (two_int, ))

    test = Empty()
    ChemicalHamiltonian.assign_orbtype(test, 'unrestricted')
    ChemicalHamiltonian.assign_integrals(test, 2*(one_int, ), 3*(two_int, ))
    assert np.allclose(test.one_int.integrals, 2*(one_int, ))
    assert np.allclose(test.two_int.integrals, 3*(two_int, ))

    test = Empty()
    ChemicalHamiltonian.assign_orbtype(test, 'generalized')
    ChemicalHamiltonian.assign_integrals(test, one_int, two_int)
    assert np.allclose(test.one_int.integrals, (one_int, ))
    assert np.allclose(test.two_int.integrals, (two_int, ))

    # bad input
    test = Empty()
    ChemicalHamiltonian.assign_orbtype(test, 'restricted')
    assert_raises(TypeError, ChemicalHamiltonian.assign_integrals, test, np.random.rand(4, 4),
                  np.random.rand(3, 3, 3, 3))

    test = Empty()
    ChemicalHamiltonian.assign_orbtype(test, 'restricted')
    assert_raises(TypeError, ChemicalHamiltonian.assign_integrals, test,
                  np.random.rand(4, 4).astype(float), np.random.rand(4, 4, 4, 4).astype(complex))

    test = Empty()
    ChemicalHamiltonian.assign_orbtype(test, 'restricted')
    assert_raises(TypeError, ChemicalHamiltonian.assign_integrals, test, 2*(np.random.rand(4, 4), ),
                  np.random.rand(4, 4, 4, 4))

    test = Empty()
    ChemicalHamiltonian.assign_orbtype(test, 'restricted')
    assert_raises(TypeError, ChemicalHamiltonian.assign_integrals, test, np.random.rand(4, 4),
                  3*(np.random.rand(4, 4, 4, 4), ))

    test = Empty()
    ChemicalHamiltonian.assign_orbtype(test, 'unrestricted')
    assert_raises(TypeError, ChemicalHamiltonian.assign_integrals, test, np.random.rand(4, 4),
                  np.random.rand(4, 4, 4, 4))

    test = Empty()
    ChemicalHamiltonian.assign_orbtype(test, 'generalized')
    assert_raises(NotImplementedError, ChemicalHamiltonian.assign_integrals, test, np.random.rand(3, 3),
                  np.random.rand(3, 3, 3, 3))


def test_nspin():
    """Test ChemicalHamiltonian.nspin."""
    one_int = np.arange(1, 5, dtype=float).reshape(2, 2)
    two_int = np.arange(5, 21, dtype=float).reshape(2, 2, 2, 2)
    test = ChemicalHamiltonian(one_int, two_int, 'restricted')
    assert test.nspin == 4
    test = ChemicalHamiltonian(2*[one_int], 3*[two_int], 'unrestricted')
    assert test.nspin == 4
    test = ChemicalHamiltonian(one_int, two_int, 'generalized')
    assert test.nspin == 2
    # hack in bad orbital type
    test.orbtype = 'bad orbital type'
    assert_raises(NotImplementedError, lambda: test.nspin)


def test_dtype():
    """Test ChemicalHamiltonian.dtype."""
    one_int = np.arange(1, 5, dtype=float).reshape(2, 2)
    two_int = np.arange(5, 21, dtype=float).reshape(2, 2, 2, 2)
    test = ChemicalHamiltonian(one_int, two_int, 'restricted')
    assert test.dtype == float

    one_int = np.arange(1, 5, dtype=complex).reshape(2, 2)
    two_int = np.arange(5, 21, dtype=complex).reshape(2, 2, 2, 2)
    test = ChemicalHamiltonian(one_int, two_int, 'restricted')
    assert test.dtype == complex


class TestWavefunction(object):
    """Mock wavefunction for testing."""
    def get_overlap(self, sd, deriv=None):
        if sd == 0b0101:
            return 1
        elif sd == 0b1010:
            return 2
        elif sd == 0b1100:
            return 3
        return 0


def test_integrate_wfn_sd():
    """Test ChemicalHamiltonian.integrate_wfn_sd."""
    one_int = np.arange(1, 5, dtype=float).reshape(2, 2)
    two_int = np.arange(5, 21, dtype=float).reshape(2, 2, 2, 2)
    hamiltonian = ChemicalHamiltonian(one_int, two_int, 'restricted')
    test_wfn = TestWavefunction()

    one_energy, coulomb, exchange = hamiltonian.integrate_wfn_sd(test_wfn, 0b0101, deriv=None)
    assert one_energy == 1*1 + 1*1
    assert coulomb == 1*5 + 2*8
    assert exchange == 0

    one_energy, coulomb, exchange = hamiltonian.integrate_wfn_sd(test_wfn, 0b1010, deriv=None)
    assert one_energy == 2*4 + 2*4
    assert coulomb == 1*17 + 2*20
    assert exchange == 0

    one_energy, coulomb, exchange = hamiltonian.integrate_wfn_sd(test_wfn, 0b0110, deriv=None)
    assert one_energy == 1*3 + 2*2
    assert coulomb == 1*13 + 2*12
    assert exchange == 0

    one_energy, coulomb, exchange = hamiltonian.integrate_wfn_sd(test_wfn, 0b1100, deriv=None)
    assert one_energy == 1*3 + 3*4
    assert coulomb == 3*10
    assert exchange == -3*11


def test_integrate_sd_sd_h2_631gdp():
    """Test ChemicalHamiltonian.integrate_sd_sd using H2 HF/6-31G** orbitals.

    Compare CI matrix with the PySCF result
    """
    ''' integrals are geenrated using horton wrapper
    hf_dict = gaussian_fchk('test/h2_hf_631gdp.fchk')
    one_int = hf_dict["one_int"]
    two_int = hf_dict["two_int"]
    '''
    one_int = (np.load(find_datafile('test/h2_hf_631gdp_oneint.npy')), )
    two_int = (np.load(find_datafile('test/h2_hf_631gdp_twoint.npy')), )
    ham = ChemicalHamiltonian(one_int, two_int, 'restricted')

    ''' CI matrix is generated using PYSCF wrapper
    ref_ci_matrix, ref_pspace = generate_fci_cimatrix(one_int[0], two_int[0], 2,
                                                      is_chemist_notation=False)
    '''
    ref_ci_matrix = np.load(find_datafile('test/h2_hf_631gdp_cimatrix.npy'))
    ref_pspace = np.load(find_datafile('test/h2_hf_631gdp_civec.npy'))

    for i, sd1 in enumerate(ref_pspace):
        for j, sd2 in enumerate(ref_pspace):
            sd1, sd2 = int(sd1), int(sd2)
            assert np.allclose(sum(ham.integrate_sd_sd(sd1, sd2)), ref_ci_matrix[i, j])


def test_integrate_wfn_sd_h2_631gdp():
    """Test ChemicalHamiltonian.integrate_wfn_sd using H2 HF/6-31G** orbitals.

    Compare projected energy with the transformed CI matrix from PySCF
    Compare projected energy with the transformed integrate_sd_sd
    """
    ''' integrals are geenrated using horton wrapper
    hf_dict = gaussian_fchk('test/h2_hf_631gdp.fchk')
    one_int = hf_dict["one_int"]
    two_int = hf_dict["two_int"]
    '''
    one_int = np.load(find_datafile('test/h2_hf_631gdp_oneint.npy'))
    two_int = np.load(find_datafile('test/h2_hf_631gdp_twoint.npy'))
    ham = ChemicalHamiltonian(one_int, two_int, 'restricted')

    ''' CI matrix is generated using PYSCF wrapper
    ref_ci_matrix, ref_pspace = generate_fci_cimatrix(one_int[0], two_int[0], 2,
                                                      is_chemist_notation=False)
    '''
    ref_ci_matrix = np.load(find_datafile('test/h2_hf_631gdp_cimatrix.npy'))
    ref_pspace = np.load(find_datafile('test/h2_hf_631gdp_civec.npy')).tolist()

    params = np.random.rand(len(ref_pspace))
    wfn = CIWavefunction(2, 10, sd_vec=ref_pspace, params=params)
    for i, sd in enumerate(ref_pspace):
        assert np.allclose(sum(ham.integrate_wfn_sd(wfn, sd)), ref_ci_matrix[i, :].dot(params))
        assert np.allclose(sum(ham.integrate_wfn_sd(wfn, sd)),
                           sum(sum(ham.integrate_sd_sd(sd, sd1)) * wfn.get_overlap(sd1)
                               for sd1 in ref_pspace))


def test_integrate_wfn_sd_h4_sto6g():
    """Test ChemicalHamiltonian.integrate_wfn_sd using H4 HF/STO6G orbitals.

    Compare projected energy with the transformed integrate_sd_sd
    """
    nelec = 4
    nspin = 8
    sds = sd_list(4, 4, num_limit=None, exc_orders=None)
    wfn = CIWavefunction(nelec, nspin, sd_vec=sds)
    np.random.seed(1000)
    wfn.assign_params(np.random.rand(len(sds)))
    ham = ChemicalHamiltonian(np.abs(np.load(find_datafile('test/h4_square_hf_sto6g_oneint.npy'))),
                              np.abs(np.load(find_datafile('test/h4_square_hf_sto6g_twoint.npy'))),
                              orbtype='restricted')

    for sd in sds:
        assert np.allclose(ham.integrate_wfn_sd(wfn, sd)[0],
                           sum(ham.integrate_sd_sd(sd, sd1)[0] * wfn.get_overlap(sd1)
                               for sd1 in sds))
        assert np.allclose(ham.integrate_wfn_sd(wfn, sd)[1],
                           sum(ham.integrate_sd_sd(sd, sd1)[1] * wfn.get_overlap(sd1)
                               for sd1 in sds))
        assert np.allclose(ham.integrate_wfn_sd(wfn, sd)[2],
                           sum(ham.integrate_sd_sd(sd, sd1)[2] * wfn.get_overlap(sd1)
                               for sd1 in sds))


@attr('slow')
def test_integrate_sd_sd_lih_631g():
    """Test ChemicalHamiltonian.integrate_sd_sd using LiH HF/6-31G orbitals."""
    ''' integrals are geenrated using horton wrapper
    hf_dict = gaussian_fchk('test/lih_hf_631g.fchk')
    one_int = hf_dict["one_int"]
    two_int = hf_dict["two_int"]
    '''
    one_int = (np.load(find_datafile('test/lih_hf_631g_oneint.npy')), )
    two_int = (np.load(find_datafile('test/lih_hf_631g_twoint.npy')), )
    ham = ChemicalHamiltonian(one_int, two_int, 'restricted')

    ''' CI matrix is generated using PYSCF wrapper
    ref_ci_matrix, ref_pspace = generate_fci_cimatrix(one_int[0], two_int[0], 2,
                                                      is_chemist_notation=False)
    '''
    ref_ci_matrix = np.load(find_datafile('test/lih_hf_631g_cimatrix.npy'))
    ref_pspace = np.load(find_datafile('test/lih_hf_631g_civec.npy'))

    for i, sd1 in enumerate(ref_pspace):
        for j, sd2 in enumerate(ref_pspace):
            sd1, sd2 = int(sd1), int(sd2)
            assert np.allclose(sum(ham.integrate_sd_sd(sd1, sd2)), ref_ci_matrix[i, j])


def test_integrate_sd_sd_particlenum():
    """ Tests ChemicalHamiltonian.integrate_sd_sd and break particle number symmetery"""
    one_int = np.arange(1, 17, dtype=float).reshape(4, 4)
    two_int = np.arange(1, 257, dtype=float).reshape(4, 4, 4, 4)
    ham = ChemicalHamiltonian(one_int, two_int, 'restricted')
    civec = [0b01, 0b11]

    # \braket{1 | h_{11} | 1}
    assert np.allclose(sum(ham.integrate_sd_sd(civec[0], civec[0])), 1)
    # \braket{12 | H | 1} = 0
    assert np.allclose(sum(ham.integrate_sd_sd(civec[1], civec[0])), 0)
    assert np.allclose(sum(ham.integrate_sd_sd(civec[0], civec[1])), 0)
    # \braket{12 | h_{11} + h_{22} + g_{1212} - g_{1221} | 12}
    assert np.allclose(sum(ham.integrate_sd_sd(civec[1], civec[1])), 4)


def test_orb_rotate_jacobi():
    """Test ChemicalHamiltonian.orb_rotate_jacobi."""
    one_int = np.arange(1, 17, dtype=float).reshape(4, 4)
    two_int = np.arange(1, 257, dtype=float).reshape(4, 4, 4, 4)
    ham = ChemicalHamiltonian(one_int, two_int, 'restricted')

    theta = 2 * np.pi * (np.random.random() - 0.5)
    p, q = 0, 3
    jacobi_matrix = np.identity(4)
    jacobi_matrix[p, p] = np.cos(theta)
    jacobi_matrix[p, q] = np.sin(theta)
    jacobi_matrix[q, p] = -np.sin(theta)
    jacobi_matrix[q, q] = np.cos(theta)
    one_answer = np.copy(one_int)
    one_answer = np.einsum('ij,ia->aj', one_answer, jacobi_matrix)
    one_answer = np.einsum('aj,jb->ab', one_answer, jacobi_matrix)
    two_answer = np.copy(two_int)
    two_answer = np.einsum('ijkl,ia->ajkl', two_answer, jacobi_matrix)
    two_answer = np.einsum('ajkl,jb->abkl', two_answer, jacobi_matrix)
    two_answer = np.einsum('abkl,kc->abcl', two_answer, jacobi_matrix)
    two_answer = np.einsum('abcl,ld->abcd', two_answer, jacobi_matrix)

    ham.orb_rotate_jacobi((p, q), theta)
    assert np.allclose(ham.one_int.integrals[0], one_answer)
    assert np.allclose(ham.two_int.integrals[0], two_answer)


def test_orb_rotate_matrix():
    """Test ChemicalHamiltonian.orb_rotate_matrix."""
    one_int = np.arange(1, 17, dtype=float).reshape(4, 4)
    two_int = np.arange(1, 257, dtype=float).reshape(4, 4, 4, 4)

    random = np.random.rand(4, 4)
    transform = np.linalg.eigh(random + random.T)[1]

    one_answer = np.copy(one_int)
    one_answer = np.einsum('ij,ia->aj', one_answer, transform)
    one_answer = np.einsum('aj,jb->ab', one_answer, transform)
    two_answer = np.copy(two_int)
    two_answer = np.einsum('ijkl,ia->ajkl', two_answer, transform)
    two_answer = np.einsum('ajkl,jb->abkl', two_answer, transform)
    two_answer = np.einsum('abkl,kc->abcl', two_answer, transform)
    two_answer = np.einsum('abcl,ld->abcd', two_answer, transform)

    ham = ChemicalHamiltonian(one_int, two_int, 'restricted')
    ham.orb_rotate_matrix(transform)
    assert np.allclose(ham.one_int.integrals[0], one_answer)
    assert np.allclose(ham.two_int.integrals[0], two_answer)
    ham = ChemicalHamiltonian(one_int, two_int, 'restricted')
    ham.orb_rotate_matrix([transform])
    assert np.allclose(ham.one_int.integrals[0], one_answer)
    assert np.allclose(ham.two_int.integrals[0], two_answer)

    ham = ChemicalHamiltonian((one_int, one_int), (two_int, two_int, two_int), 'unrestricted')
    ham.orb_rotate_matrix(transform)
    assert np.allclose(ham.one_int.integrals[0], one_answer)
    assert np.allclose(ham.one_int.integrals[1], one_answer)
    assert np.allclose(ham.two_int.integrals[0], two_answer)
    assert np.allclose(ham.two_int.integrals[1], two_answer)
    assert np.allclose(ham.two_int.integrals[2], two_answer)
    ham = ChemicalHamiltonian((one_int, one_int), (two_int, two_int, two_int), 'unrestricted')
    ham.orb_rotate_matrix([transform])
    assert np.allclose(ham.one_int.integrals[0], one_answer)
    assert np.allclose(ham.one_int.integrals[1], one_answer)
    assert np.allclose(ham.two_int.integrals[0], two_answer)
    assert np.allclose(ham.two_int.integrals[1], two_answer)
    assert np.allclose(ham.two_int.integrals[2], two_answer)
    ham = ChemicalHamiltonian((one_int, one_int), (two_int, two_int, two_int), 'unrestricted')
    ham.orb_rotate_matrix([transform, transform])
    assert np.allclose(ham.one_int.integrals[0], one_answer)
    assert np.allclose(ham.one_int.integrals[1], one_answer)
    assert np.allclose(ham.two_int.integrals[0], two_answer)
    assert np.allclose(ham.two_int.integrals[1], two_answer)
    assert np.allclose(ham.two_int.integrals[2], two_answer)
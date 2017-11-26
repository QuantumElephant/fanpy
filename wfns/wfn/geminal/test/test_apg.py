"""Test wfns.wavefunction.geminals.apg."""
from nose.tools import assert_raises
from nose.plugins.attrib import attr
import types
import numpy as np
from wfns.backend.graphs import generate_complete_pmatch
from wfns.tools import find_datafile
from wfns.wfn.geminal.apg import APG
from wfns.ham.chemical import ChemicalHamiltonian
from wfns.objective.schrodinger.system_nonlinear import SystemEquations
from wfns.solver.system import least_squares
from wfns.objective.schrodinger.onesided_energy import OneSidedEnergy
from wfns.solver.equation import minimize, cma


class TestAPG(APG):
    """APG that skips initialization."""
    def __init__(self):
        pass


def test_apg_assign_orbpairs():
    """Test APG.assign_orbpairs."""
    test = TestAPG()
    test.nspin = 10
    assert_raises(ValueError, test.assign_orbpairs, (0, 1))
    assert_raises(ValueError, test.assign_orbpairs, [(0, 1)])
    test.assign_orbpairs(None)
    dict_orbpair_ind = {}
    dict_ind_orbpair = {}
    counter = 0
    for i in range(10):
        for j in range(i+1, 10):
            dict_orbpair_ind[(i, j)] = counter
            dict_ind_orbpair[counter] = (i, j)
            counter += 1


def test_apg_get_col_ind():
    """Test APG.get_col_ind."""
    test = TestAPG()
    test.nspin = 10

    orbpairs = [(i, j) for i in range(10) for j in range(i+1, 10)]

    for i, orbpair in enumerate(orbpairs):
        assert test.get_col_ind(orbpair) == i

    assert_raises(ValueError, test.get_col_ind, (0, 10))
    assert_raises(ValueError, test.get_col_ind, (0, 0))
    assert_raises(ValueError, test.get_col_ind, (9, 10))


def test_apg_get_orbpair():
    """Test APG.get_orbpair."""
    test = TestAPG()
    test.nspin = 10

    orbpairs = [(i, j) for i in range(10) for j in range(i+1, 10)]

    for i, orbpair in enumerate(orbpairs):
        assert test.get_orbpair(i) == orbpair

    assert_raises(ValueError, test.get_orbpair, -1)
    assert_raises(ValueError, test.get_orbpair, len(orbpairs))


def test_assign_pmatch_generator():
    """Test APG.generate_possible_orbpairs."""
    test = TestAPG()
    sd = (0, 1, 2, 3, 4, 5)
    assert isinstance(test.generate_possible_orbpairs(sd), types.GeneratorType)
    for i, j in zip(test.generate_possible_orbpairs(sd), generate_complete_pmatch(sd)):
        assert i == j


# FIXME: answer should be brute force or external (should not depend on the code)
def answer_apg_h2_sto6g():
    """Find the APG/STO-6G wavefunction variationally for H2 system."""
    # Can be read in using HORTON
    # hf_dict = gaussian_fchk('test/h2_hf_sto6g.fchk')
    # one_int = hf_dict["one_int"]
    # two_int = hf_dict["two_int"]
    # nuc_nuc = hf_dict["nuc_nuc_energy"]
    one_int = np.load(find_datafile('test/h2_hf_sto6g_oneint.npy'))
    two_int = np.load(find_datafile('test/h2_hf_sto6g_twoint.npy'))
    nuc_nuc = 0.71317683129
    ham = ChemicalHamiltonian(one_int, two_int, orbtype='restricted', energy_nuc_nuc=nuc_nuc)
    apg = APG(2, 4)
    full_sds = (0b0011, 0b0101, 0b1001, 0b0110, 0b1010, 0b1100)

    objective = OneSidedEnergy(apg, ham, refwfn=full_sds)
    results = minimize(objective)
    print(results)
    print(apg.params)


def test_apg_h2_sto6g():
    """Test APG wavefunction using H2 with HF/STO-6G orbitals.

    Answers obtained from answer_apg_h2_sto6g

    HF (Electronic) Energy : -1.838434256
    APG Energy : -1.8590898441488932
    APG Coeffs : [0.00000000e+00, 1.00061615e+00, 4.43043808e-16, 4.43043808e-16, -1.13806005e-01,
                  0.00000000e+00]

    """
    # Can be read in using HORTON
    # hf_dict = gaussian_fchk('test/h2_hf_sto6g.fchk')
    # one_int = hf_dict["one_int"]
    # two_int = hf_dict["two_int"]
    # nuc_nuc = hf_dict["nuc_nuc_energy"]
    one_int = np.load(find_datafile('test/h2_hf_sto6g_oneint.npy'))
    two_int = np.load(find_datafile('test/h2_hf_sto6g_twoint.npy'))
    nuc_nuc = 0.71317683129
    ham = ChemicalHamiltonian(one_int, two_int, orbtype='restricted', energy_nuc_nuc=nuc_nuc)
    apg = APG(2, 4)
    full_sds = (0b0011, 0b0101, 0b1001, 0b0110, 0b1010, 0b1100)

    # Solve system of equations
    objective = SystemEquations(apg, ham, refwfn=full_sds)
    results = least_squares(objective)
    assert np.allclose(results['energy'], -1.8590898441488932)


# FIXME: answer should be brute force or external (should not depend on the code)
def answer_apg_h2_631gdp():
    """Find the APG/6-31G** wavefunction variationally for H2 system."""
    # Can be read in using HORTON
    # hf_dict = gaussian_fchk('test/h2_hf_631gdp.fchk')
    # one_int = hf_dict["one_int"]
    # two_int = hf_dict["two_int"]
    # nuc_nuc = hf_dict["nuc_nuc_energy"]
    one_int = np.load(find_datafile('test/h2_hf_631gdp_oneint.npy'))
    two_int = np.load(find_datafile('test/h2_hf_631gdp_twoint.npy'))
    nuc_nuc = 0.71317683129
    ham = ChemicalHamiltonian(one_int, two_int, orbtype='restricted', energy_nuc_nuc=nuc_nuc)
    apg = APG(2, 20)
    full_sds = [1 << i | 1 << j for i in range(20) for j in range(i+1, 20)]

    objective = OneSidedEnergy(apg, ham, refwfn=full_sds)
    results = cma(objective, sigma0=0.01, gradf=None, options={'tolfun': 1e-6, 'verb_log': 0})
    print(results)
    results = minimize(objective)
    print(results)
    print(apg.params)


@attr('slow')
def test_apg_h2_631gdp():
    """Test APG wavefunction using H2 with HF/6-31G** orbitals.

    Answers obtained from answer_apg_h2_631gdp

    HF (Electronic) Energy : -1.84444667247
    APG Energy : -1.8783255857444985

    """
    # Can be read in using HORTON
    # hf_dict = gaussian_fchk('test/h2_hf_631gdp.fchk')
    # one_int = hf_dict["one_int"]
    # two_int = hf_dict["two_int"]
    # nuc_nuc = hf_dict["nuc_nuc_energy"]
    one_int = np.load(find_datafile('test/h2_hf_631gdp_oneint.npy'))
    two_int = np.load(find_datafile('test/h2_hf_631gdp_twoint.npy'))
    nuc_nuc = 0.71317683129
    ham = ChemicalHamiltonian(one_int, two_int, orbtype='restricted', energy_nuc_nuc=nuc_nuc)
    apg = APG(2, 20)
    full_sds = [1 << i | 1 << j for i in range(20) for j in range(i+1, 20)]

    # Solve system of equations
    objective = SystemEquations(apg, ham, refwfn=full_sds)
    results = least_squares(objective)
    assert np.allclose(results['energy'], -1.8783255857444985)


# FIXME: answer should be brute force or external (should not depend on the code)
def answer_apg_lih_sto6g():
    """Find the APG/STO-6G wavefunction variationally for LiH system."""
    # Can be read in using HORTON
    # hf_dict = gaussian_fchk('test/lih_hf_sto6g.fchk')
    # one_int = hf_dict["one_int"]
    # two_int = hf_dict["two_int"]
    # nuc_nuc = hf_dict["nuc_nuc_energy"]
    one_int = (np.load(find_datafile('test/lih_hf_sto6g_oneint.npy')), )
    two_int = (np.load(find_datafile('test/lih_hf_sto6g_twoint.npy')), )
    nuc_nuc = 0.995317634356
    ham = ChemicalHamiltonian(one_int, two_int, orbtype='restricted', energy_nuc_nuc=nuc_nuc)
    apg = APG(4, 12)
    full_sds = [1 << i | 1 << j | 1 << k | 1 << l for i in range(12) for j in range(i+1, 12)
                for k in range(j+1, 12) for l in range(k+1, 12)]

    objective = OneSidedEnergy(apg, ham, refwfn=full_sds)
    results = minimize(objective)
    print(results)
    print(apg.params)


@attr('slow')
def test_apg_lih_sto6g():
    """Test APG wavefunction using H2 with LiH/STO-6G orbital.

    Answers obtained from answer_apg_h2_631gdp

    HF (Electronic) Energy : -8.9472891719
    APG Energy :

    """
    # Can be read in using HORTON
    # hf_dict = gaussian_fchk('test/lih_hf_sto6g.fchk')
    # one_int = hf_dict["one_int"]
    # two_int = hf_dict["two_int"]
    # nuc_nuc = hf_dict["nuc_nuc_energy"]
    one_int = np.load(find_datafile('test/lih_hf_sto6g_oneint.npy'))
    two_int = np.load(find_datafile('test/lih_hf_sto6g_twoint.npy'))
    nuc_nuc = 0.995317634356
    ham = ChemicalHamiltonian(one_int, two_int, orbtype='restricted', energy_nuc_nuc=nuc_nuc)
    apg = APG(4, 12)
    full_sds = [1 << i | 1 << j | 1 << k | 1 << l for i in range(12) for j in range(i+1, 12)
                for k in range(j+1, 12) for l in range(k+1, 12)]

    # Solve system of equations
    objective = SystemEquations(apg, ham, refwfn=full_sds)
    results = least_squares(objective)
    assert np.allclose(results['energy'], 0.0)

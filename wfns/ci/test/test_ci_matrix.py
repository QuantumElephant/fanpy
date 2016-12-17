import os
import numpy as np
from nose.plugins.attrib import attr

from wfns.ci import ci_matrix
from wfns.wrapper.horton import gaussian_fchk
from wfns.wrapper.pyscf import generate_fci_cimatrix


def test_is_alpha():
    """
    Tests ci_matrix.is_alpha
    """
    # assert assert_raises(AssertionError, lambda:ci_matrix.is_alpha(0, 0))
    # assert assert_raises(AssertionError, lambda:ci_matrix.is_alpha(0, -1))
    assert ci_matrix.is_alpha(0, 1) is True
    # assert assert_raises(AssertionError, lambda:ci_matrix.is_alpha(-1, 1))
    # assert assert_raises(AssertionError, lambda:ci_matrix.is_alpha(2, 1))
    assert ci_matrix.is_alpha(1, 1) is False

    assert ci_matrix.is_alpha(0, 4) is True
    assert ci_matrix.is_alpha(1, 4) is True
    assert ci_matrix.is_alpha(2, 4) is True
    assert ci_matrix.is_alpha(3, 4) is True
    assert ci_matrix.is_alpha(4, 4) is False
    assert ci_matrix.is_alpha(5, 4) is False
    assert ci_matrix.is_alpha(6, 4) is False
    assert ci_matrix.is_alpha(7, 4) is False


def test_spatial_index():
    """
    Tests ci_matrix.spatial_index
    """
    # assert assert_raises(AssertionError, lambda:ci_matrix.spatial_index(0, 0))
    # assert assert_raises(AssertionError, lambda:ci_matrix.spatial_index(0, -1))
    assert ci_matrix.spatial_index(0, 1) == 0
    # assert assert_raises(AssertionError, lambda:ci_matrix.spatial_index(-1, 1))
    # assert assert_raises(AssertionError, lambda:ci_matrix.spatial_index(2, 1))
    assert ci_matrix.spatial_index(1, 1) == 0

    assert ci_matrix.spatial_index(0, 4) == 0
    assert ci_matrix.spatial_index(1, 4) == 1
    assert ci_matrix.spatial_index(2, 4) == 2
    assert ci_matrix.spatial_index(3, 4) == 3
    assert ci_matrix.spatial_index(4, 4) == 0
    assert ci_matrix.spatial_index(5, 4) == 1
    assert ci_matrix.spatial_index(6, 4) == 2
    assert ci_matrix.spatial_index(7, 4) == 3


def test_get_H_value():
    """
    Tests ci_matrix.get_H_value
    """
    H = (np.arange(16).reshape(4, 4),)
    # restricted
    assert ci_matrix.get_H_value(H, 0, 0, 'restricted') == 0.0
    assert ci_matrix.get_H_value(H, 0, 1, 'restricted') == 1.0
    assert ci_matrix.get_H_value(H, 0, 4, 'restricted') == 0.0
    assert ci_matrix.get_H_value(H, 0, 5, 'restricted') == 0.0
    assert ci_matrix.get_H_value(H, 1, 0, 'restricted') == 4.0
    assert ci_matrix.get_H_value(H, 1, 1, 'restricted') == 5.0
    assert ci_matrix.get_H_value(H, 1, 4, 'restricted') == 0.0
    assert ci_matrix.get_H_value(H, 1, 5, 'restricted') == 0.0
    assert ci_matrix.get_H_value(H, 4, 0, 'restricted') == 0.0
    assert ci_matrix.get_H_value(H, 4, 1, 'restricted') == 0.0
    assert ci_matrix.get_H_value(H, 4, 4, 'restricted') == 0.0
    assert ci_matrix.get_H_value(H, 4, 5, 'restricted') == 1.0
    assert ci_matrix.get_H_value(H, 5, 0, 'restricted') == 0.0
    assert ci_matrix.get_H_value(H, 5, 1, 'restricted') == 0.0
    assert ci_matrix.get_H_value(H, 5, 4, 'restricted') == 4.0
    assert ci_matrix.get_H_value(H, 5, 5, 'restricted') == 5.0
    # unrestricted
    H = (np.arange(16).reshape(4, 4), np.arange(16, 32).reshape(4, 4))
    assert ci_matrix.get_H_value(H, 0, 0, 'unrestricted') == 0.0
    assert ci_matrix.get_H_value(H, 0, 1, 'unrestricted') == 1.0
    assert ci_matrix.get_H_value(H, 0, 4, 'unrestricted') == 0.0
    assert ci_matrix.get_H_value(H, 0, 5, 'unrestricted') == 0.0
    assert ci_matrix.get_H_value(H, 1, 0, 'unrestricted') == 4.0
    assert ci_matrix.get_H_value(H, 1, 1, 'unrestricted') == 5.0
    assert ci_matrix.get_H_value(H, 1, 4, 'unrestricted') == 0.0
    assert ci_matrix.get_H_value(H, 1, 5, 'unrestricted') == 0.0
    assert ci_matrix.get_H_value(H, 4, 0, 'unrestricted') == 0.0
    assert ci_matrix.get_H_value(H, 4, 1, 'unrestricted') == 0.0
    assert ci_matrix.get_H_value(H, 4, 4, 'unrestricted') == 16.0
    assert ci_matrix.get_H_value(H, 4, 5, 'unrestricted') == 17.0
    assert ci_matrix.get_H_value(H, 5, 0, 'unrestricted') == 0.0
    assert ci_matrix.get_H_value(H, 5, 1, 'unrestricted') == 0.0
    assert ci_matrix.get_H_value(H, 5, 4, 'unrestricted') == 20.0
    assert ci_matrix.get_H_value(H, 5, 5, 'unrestricted') == 21.0
    # generalized
    H = (np.arange(64).reshape(8, 8),)
    assert ci_matrix.get_H_value(H, 0, 0, 'generalized') == 0.0
    assert ci_matrix.get_H_value(H, 0, 1, 'generalized') == 1.0
    assert ci_matrix.get_H_value(H, 0, 4, 'generalized') == 4.0
    assert ci_matrix.get_H_value(H, 0, 5, 'generalized') == 5.0
    assert ci_matrix.get_H_value(H, 1, 0, 'generalized') == 8.0
    assert ci_matrix.get_H_value(H, 1, 1, 'generalized') == 9.0
    assert ci_matrix.get_H_value(H, 1, 4, 'generalized') == 12.0
    assert ci_matrix.get_H_value(H, 1, 5, 'generalized') == 13.0
    assert ci_matrix.get_H_value(H, 4, 0, 'generalized') == 32.0
    assert ci_matrix.get_H_value(H, 4, 1, 'generalized') == 33.0
    assert ci_matrix.get_H_value(H, 4, 4, 'generalized') == 36.0
    assert ci_matrix.get_H_value(H, 4, 5, 'generalized') == 37.0
    assert ci_matrix.get_H_value(H, 5, 0, 'generalized') == 40.0
    assert ci_matrix.get_H_value(H, 5, 1, 'generalized') == 41.0
    assert ci_matrix.get_H_value(H, 5, 4, 'generalized') == 44.0
    assert ci_matrix.get_H_value(H, 5, 5, 'generalized') == 45.0


def test_get_G_value():
    """
    Tests ci_matrix.get_G_value
    """
    # restricted
    G = (np.arange(256).reshape(4, 4, 4, 4),)
    assert ci_matrix.get_G_value(G, 0, 0, 0, 1, 'restricted') == 1.0
    assert ci_matrix.get_G_value(G, 0, 0, 4, 1, 'restricted') == 0.0
    assert ci_matrix.get_G_value(G, 0, 4, 0, 1, 'restricted') == 0.0
    assert ci_matrix.get_G_value(G, 4, 0, 0, 1, 'restricted') == 0.0
    assert ci_matrix.get_G_value(G, 0, 4, 4, 1, 'restricted') == 0.0
    assert ci_matrix.get_G_value(G, 4, 0, 4, 1, 'restricted') == 1.0
    assert ci_matrix.get_G_value(G, 4, 4, 0, 1, 'restricted') == 0.0
    assert ci_matrix.get_G_value(G, 4, 4, 4, 1, 'restricted') == 0.0
    assert ci_matrix.get_G_value(G, 0, 0, 0, 5, 'restricted') == 0.0
    assert ci_matrix.get_G_value(G, 0, 0, 4, 5, 'restricted') == 0.0
    assert ci_matrix.get_G_value(G, 0, 4, 0, 5, 'restricted') == 1.0
    assert ci_matrix.get_G_value(G, 4, 0, 0, 5, 'restricted') == 0.0
    assert ci_matrix.get_G_value(G, 0, 4, 4, 5, 'restricted') == 0.0
    assert ci_matrix.get_G_value(G, 4, 0, 4, 5, 'restricted') == 0.0
    assert ci_matrix.get_G_value(G, 4, 4, 0, 5, 'restricted') == 0.0
    assert ci_matrix.get_G_value(G, 4, 4, 4, 5, 'restricted') == 1.0
    # unrestricted
    G = (np.arange(256).reshape(4, 4, 4, 4),
         np.arange(256, 512).reshape(4, 4, 4, 4),
         np.arange(512, 768).reshape(4, 4, 4, 4))
    assert ci_matrix.get_G_value(G, 0, 0, 0, 1, 'unrestricted') == 1.0
    assert ci_matrix.get_G_value(G, 0, 0, 4, 1, 'unrestricted') == 0.0
    assert ci_matrix.get_G_value(G, 0, 4, 0, 1, 'unrestricted') == 0.0
    assert ci_matrix.get_G_value(G, 4, 0, 0, 1, 'unrestricted') == 0.0
    assert ci_matrix.get_G_value(G, 0, 4, 4, 1, 'unrestricted') == 0.0
    assert ci_matrix.get_G_value(G, 4, 0, 4, 1, 'unrestricted') == 260.0
    assert ci_matrix.get_G_value(G, 4, 4, 0, 1, 'unrestricted') == 0.0
    assert ci_matrix.get_G_value(G, 4, 4, 4, 1, 'unrestricted') == 0.0
    assert ci_matrix.get_G_value(G, 0, 0, 0, 5, 'unrestricted') == 0.0
    assert ci_matrix.get_G_value(G, 0, 0, 4, 5, 'unrestricted') == 0.0
    assert ci_matrix.get_G_value(G, 0, 4, 0, 5, 'unrestricted') == 257.0
    assert ci_matrix.get_G_value(G, 4, 0, 0, 5, 'unrestricted') == 0.0
    assert ci_matrix.get_G_value(G, 0, 4, 4, 5, 'unrestricted') == 0.0
    assert ci_matrix.get_G_value(G, 4, 0, 4, 5, 'unrestricted') == 0.0
    assert ci_matrix.get_G_value(G, 4, 4, 0, 5, 'unrestricted') == 0.0
    assert ci_matrix.get_G_value(G, 4, 4, 4, 5, 'unrestricted') == 513.0
    # generalized
    G = (np.arange(4096).reshape(8, 8, 8, 8),)
    assert ci_matrix.get_G_value(G, 0, 0, 0, 1, 'generalized') == 1.0
    assert ci_matrix.get_G_value(G, 0, 0, 4, 1, 'generalized') == 33.0
    assert ci_matrix.get_G_value(G, 0, 4, 0, 1, 'generalized') == 257.0
    assert ci_matrix.get_G_value(G, 4, 0, 0, 1, 'generalized') == 2049.0
    assert ci_matrix.get_G_value(G, 0, 4, 4, 1, 'generalized') == 289.0
    assert ci_matrix.get_G_value(G, 4, 0, 4, 1, 'generalized') == 2081.0
    assert ci_matrix.get_G_value(G, 4, 4, 0, 1, 'generalized') == 2305.0
    assert ci_matrix.get_G_value(G, 4, 4, 4, 1, 'generalized') == 2337.0
    assert ci_matrix.get_G_value(G, 0, 0, 0, 5, 'generalized') == 5.0
    assert ci_matrix.get_G_value(G, 0, 0, 4, 5, 'generalized') == 37.0
    assert ci_matrix.get_G_value(G, 0, 4, 0, 5, 'generalized') == 261.0
    assert ci_matrix.get_G_value(G, 4, 0, 0, 5, 'generalized') == 2053.0
    assert ci_matrix.get_G_value(G, 0, 4, 4, 5, 'generalized') == 293.0
    assert ci_matrix.get_G_value(G, 4, 0, 4, 5, 'generalized') == 2085.0
    assert ci_matrix.get_G_value(G, 4, 4, 0, 5, 'generalized') == 2309.0
    assert ci_matrix.get_G_value(G, 4, 4, 4, 5, 'generalized') == 2341.0


class DummyWavefunction(object):
    """ Dummy wavefunction because ci_matrix takes in Wavefunction class"""
    dtype = np.float64
    orb_type = 'restricted'

    def __init__(self, pspace, H, G):
        self.civec = pspace
        self.nci = len(pspace)
        self.H = H
        self.G = G

    def compute_ci_matrix(self):
        return ci_matrix.ci_matrix(self, self.orb_type)


def test_ci_matrix_h2():
    """
    Tests ci_matrix.ci_matrix using H2 FCI ci_matrix

    Note
    ----
    Needs PYSCF!!
    """
    # HORTON/Olsen Results
    data_path = os.path.join(os.path.dirname(__file__), '../../../data/test/h2_hf_631gdp.fchk')
    hf_dict = gaussian_fchk(data_path)

    H = hf_dict["H"]
    G = hf_dict["G"]

    ref_ci_matrix, ref_pspace = generate_fci_cimatrix(H[0], G[0], 2, is_chemist_notation=False)


    dummy = DummyWavefunction(ref_pspace, H, G)
    test_ci_matrix = dummy.compute_ci_matrix()

    assert np.allclose(test_ci_matrix, ref_ci_matrix)


@attr('slow')
def test_ci_matrix_lih():
    """
    Tests ci_matrix.ci_matrix using LiH FCI ci_matrix

    Note
    ----
    Needs PYSCF!!
    """
    # HORTON/Olsen Results
    data_path = os.path.join(os.path.dirname(__file__), '../../../data/test/lih_hf_631g.fchk')
    hf_dict = gaussian_fchk(data_path)

    E_hf = hf_dict["energy"]
    H = hf_dict["H"]
    G = hf_dict["G"]

    ref_ci_matrix, ref_pspace = generate_fci_cimatrix(H[0], G[0], 4, is_chemist_notation=False)


    dummy = DummyWavefunction(ref_pspace, H, G)
    test_ci_matrix = dummy.compute_ci_matrix()

    assert np.allclose(test_ci_matrix, ref_ci_matrix)


def test_doci_matrix():
    """
    Tests ci_matrix.doci_matrix
    """
    pass
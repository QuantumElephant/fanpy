==================
 Example Template
==================

*Ignore italicized sections*

The following scripts are generated by using :code:`wfns_make_script.py` and by tweaking the
generated script. For more information on using :code:`wfns_make_script.py`, go to
:ref:`Using a script that makes a script <tutorial_calc_make_script>` for the tutorial and
:ref:`wfns_make_script.py <script_make_script>` for the API. For more information on customizing the
script, go to :ref:`How to run a calculation by making a script <tutorial_calc_code>`.

*Each example should describe the API of one object (e.g. wavefunction)*

For more information, see *API location*.

Recommended default calculation configuration
---------------------------------------------
*If the calculation is supported by the script, include the following:*

.. code:: bash

   wfns_make_script.py --nelec 4 --nspin 8 --one_int_file oneint.npy \
                       --two_int_file twoint.npy --wfn_type fci \
                       --solver diag --filename example.py

*Describe the details of the calculation.*

Wavefunction
   wavefunction name
Hamiltonian
   Hamiltonian type
Optimized Parameters
   parameters that will be optimized (active)
Projection Space
   orders of excitation
Objective
   type of Schrodinger equation
Optimizer
   type of optimizer used

Other calculation configuration
-------------------------------
*Part of the code that demonstrates specific API for the object.*
*For example, if the wavfunction is modified, include a different wavefunction initialization.*

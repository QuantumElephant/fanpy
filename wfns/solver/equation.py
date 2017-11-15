"""Solvers for single equations."""
from __future__ import absolute_import, division, print_function
import numpy as np
from wfns.objective.base_objective import BaseObjective
from wfns.objective.schrodinger.onesided_energy import OneSidedEnergy
from wfns.objective.schrodinger.twosided_energy import TwoSidedEnergy
from wfns.objective.schrodinger.least_squares import LeastSquaresEquations
from wfns.solver.wrappers import wrap_scipy


def cma(objective, save_file='', **kwargs):
    """Solve an equation using Covariance Matrix Adaptation Evolution Strategy.

    See module `cma` for details.

    Parameters
    ----------
    objective : BaseObjective
        Instance that contains the function that will be optimized.
    save_file : str
        File to which the results of the optimization is saved.
        By default, the results are not saved.
    kwargs : dict
        Keyword arguments to `cma.fmin`. See its documentation for details.
        By default, 'sigma0' is set to 0.01, 'gradf' to the gradient of the objective, and 'options'
        to `{'ftarget': 1e-7}`.

    Returns
    -------
    Dictionary with the following keys and values:
    success : bool
        True if optimization succeeded.
    params : np.ndarray
        Parameters at the end of the optimization.
    energy : float
        Energy after optimization.
        Only available for objectives that are OneSidedEnergy, TwoSidedEnergy, and
        LeastSquaresEquations instances.
    message : str
        Termination reason.
    internal : list
        Returned value of the `cma.fmin`.

    Raises
    ------
    TypeError
        If objective is not BaseObjective instance.
    ValueError
        If objective has more than one equation.

    """
    import cma

    if not isinstance(objective, BaseObjective):
        raise TypeError('Objective must be a BaseObjective instance.')
    elif objective.num_eqns != 1:
        raise ValueError('Objective must contain only one equation.')

    if kwargs == {}:
        kwargs = {'sigma0': 0.01}

    results = cma.fmin(objective.objective, objective.params, **kwargs)

    output = {}
    output['success'] = results[-3] != {}
    output['params'] = results[0]
    output['function'] = results[1]

    if isinstance(objective, LeastSquaresEquations):
        output['energy'] = objective.energy.params
    elif isinstance(objective, (OneSidedEnergy, TwoSidedEnergy)):
        output['energy'] = results[1]

    if output['success']:
        output['message'] = ('Following termination conditions are satisfied:' +
                             ''.join(' {0}: {1},'.format(key, val)
                                     for key, val in results[-3].items()))
        output['message'] = output['message'][:-1] + '.'
    else:
        output['message'] = 'Optimization did not succeed.'

    output['internal'] = results

    if save_file != '':
        np.save(save_file, objective.all_params)

    return output


def minimize(objective, save_file='', **kwargs):
    """Solve an equation using `scipy.optimize.minimize`.

    See module `scipy.optimize.minimize` for details.

    Parameters
    ----------
    objective : BaseObjective
        Instance that contains the function that will be optimized.
    save_file : str
        File to which the results of the optimization is saved.
        By default, the results are not saved.
    kwargs : dict
        Keyword arguments to `scipy.optimize.minimize`. See its documentation for details.
        By default, if the objective has a gradient,  'method' is 'BFGS', 'jac' is the gradient
        of the objective, and 'options' is `{'gtol': 1e-8}`.
        By default, if the objective does not have a gradient, 'method' is 'Powell' and 'options' is
        `{'xtol': 1e-9, 'ftol': 1e-9}}`.

    Returns
    -------
    Dictionary with the following keys and values:
    success : bool
        True if optimization succeeded.
    params : np.ndarray
        Parameters at the end of the optimization.
    energy : float
        Energy after optimization.
        Only available for objectives that are OneSidedEnergy, TwoSidedEnergy, and
        LeastSquaresEquations instances.
    message : str
        Message returned by the optimizer.
    internal : list
        Returned value of the `scipy.optimize.minimize`.

    Raises
    ------
    TypeError
        If objective is not BaseObjective instance.
    ValueError
        If objective has more than one equation.

    """
    import scipy.optimize

    if not isinstance(objective, BaseObjective):
        raise TypeError('Objective must be a BaseObjective instance.')
    elif objective.num_eqns != 1:
        raise ValueError('Objective must contain only one equation.')

    if kwargs == {}:
        if hasattr(objective, 'gradient'):
            kwargs = {'method': 'BFGS', 'jac': objective.gradient, 'options': {'gtol': 1e-8}}
        else:
            kwargs = {'method': 'Powell', 'options': {'xtol': 1e-9, 'ftol': 1e-9}}

    output = wrap_scipy(scipy.optimize.minimize)(objective, save_file=save_file, **kwargs)
    output['function'] = output['internal'].fun
    if isinstance(objective, LeastSquaresEquations):
        output['energy'] = objective.energy.params
    elif isinstance(objective, (OneSidedEnergy, TwoSidedEnergy)):
        output['energy'] = output['function']

    return output

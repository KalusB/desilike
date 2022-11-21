import os

import numpy as np


def AbacusSummitLRG(cosmo='external', solve=None):

    import desilike
    from desilike.theories.galaxy_clustering import LPTVelocileptorsTracerPowerSpectrumMultipoles, FullPowerSpectrumTemplate
    from desilike.observables.galaxy_clustering import ObservedTracerPowerSpectrum
    from desilike.likelihoods import GaussianLikelihood

    theory = LPTVelocileptorsTracerPowerSpectrumMultipoles(template=FullPowerSpectrumTemplate(z=0.8, cosmo=cosmo))
    if solve is None:
        from desilike.utils import jax
        solve = jax is not None
    if solve:
        for param in theory.params.select(name=['alpha*', 'sn*']): param.derived = '.marg'
        theory.log_info('Use analytic marginalization for {}.'.format(theory.params.names(solved=True)))
    observable = ObservedTracerPowerSpectrum(klim={0: [0.02, 0.2], 2: [0.02, 0.2]}, kstep=0.005,
                                             data='/global/cfs/cdirs/desi/cosmosim/KP45/MC/Clustering/AbacusSummit/CubicBox/LRG/Pk/Pre/jmena/nmesh_512/pypower_format/Pk_AbacusSummit_base_*.npy',
                                             mocks='/global/cfs/cdirs/desi/cosmosim/KP45/MC/Clustering/EZmock/CubicBox/LRG/Pk/jmena/nmesh_512/pypower_format/Pk_EZmock_B2000G512Z0.8N8015724_b0.385d4r169c0.3_seed*.npy',
                                             wmatrix='/global/cfs/cdirs/desi/users/adematti/desi_mock_challenge/FirstGenMocks/AbacusSummit/CubicBox/ELG/z1.100/window_nmesh512_los-x.npy',
                                             theory=theory)
    return GaussianLikelihood(observables=[observable])


if __name__ == '__main__':
    
    from desilike import setup_logging
    from desilike.bindings.cobaya.factory import CobayaLikelihoodGenerator
    from desilike.bindings.cosmosis.factory import CosmoSISLikelihoodGenerator
    from desilike.bindings.montepython.factory import MontePythonLikelihoodGenerator


    for cls in [AbacusSummitLRG]:
        setup_logging('info')
        CobayaLikelihoodGenerator()(cls)
        CosmoSISLikelihoodGenerator()(cls)
        MontePythonLikelihoodGenerator()(cls)
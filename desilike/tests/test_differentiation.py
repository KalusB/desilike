import numpy as np

from desilike import setup_logging


def test_misc():
    from desilike.differentiation import deriv_nd, deriv_grid

    X = np.linspace(0., 1., 11)[..., None]
    Y = np.linspace(0., 1., 11)[..., None]
    center = X[0]
    print(deriv_nd(X, Y, orders=[(0, 1, 2)], center=center))

    deriv = deriv_grid([(np.array([0]), np.array([0]), 0)] * 3)
    deriv2 = set([tuple(d) for d in deriv])
    print(deriv, len(deriv), len(deriv2))

    deriv = deriv_grid([(np.linspace(-1., 1., 3), [1, 0, 1], 2)] * 3)
    deriv2 = set([tuple(d) for d in deriv])
    print(deriv, len(deriv), len(deriv2))

    deriv = deriv_grid([(np.linspace(-1., 1., 3), [1, 0, 1], 2), (np.linspace(-1., 1., 5), [1, 1, 0, 1, 1], 1)])
    deriv2 = set([tuple(d) for d in deriv])
    print(deriv, len(deriv), len(deriv2))

    deriv = deriv_grid([(np.linspace(-1., 1., 3), [1, 0, 1], 2)] * 20)
    deriv2 = set([tuple(d) for d in deriv])
    print(deriv, len(deriv), len(deriv2))


def test_jax():
    import timeit
    import numpy as np
    from desilike.jax import jax
    from desilike.jax import numpy as jnp

    def f(a, b):
        return jnp.sum(a * b)

    jac = jax.jacrev(f)
    jac(1., 3.)

    a = np.arange(10)
    number = 100000
    d = {}
    d['np-sum'] = {'stmt': "np.sum(a)", 'number': number}
    d['jnp-sum'] = {'stmt': "jnp.sum(a)", 'number': number}

    for key, value in d.items():
        dt = timeit.timeit(**value, globals={**globals(), **locals()}) #/ value['number'] * 1e3
        print('{} takes {: .3f} milliseconds'.format(key, dt))


def test_differentiation():

    from desilike.theories.galaxy_clustering import KaiserTracerPowerSpectrumMultipoles, ShapeFitPowerSpectrumTemplate

    from desilike import Differentiation
    theory = KaiserTracerPowerSpectrumMultipoles(template=ShapeFitPowerSpectrumTemplate(z=1.4))
    theory.params['power'] = {'derived': True}
    theory(sn0=100.)
    diff = Differentiation(theory, method=None, order=2)
    diff()
    diff(sn0=50.)


def test_solve():

    from desilike.likelihoods import ObservablesGaussianLikelihood
    from desilike.observables.galaxy_clustering import TracerPowerSpectrumMultipolesObservable, BoxFootprint, ObservablesCovarianceMatrix
    from desilike.theories.galaxy_clustering import KaiserTracerPowerSpectrumMultipoles, ShapeFitPowerSpectrumTemplate, BandVelocityPowerSpectrumTemplate

    theory = KaiserTracerPowerSpectrumMultipoles(template=BandVelocityPowerSpectrumTemplate(z=0.5, kp=np.arange(0.05, 0.2 + 1e-6, 0.005)))
    observable = TracerPowerSpectrumMultipolesObservable(klim={0: [0.05, 0.2, 0.01], 2: [0.05, 0.2, 0.01]},
                                                         data={},
                                                         theory=theory)
    footprint = BoxFootprint(volume=1e10, nbar=1e-5)
    cov = ObservablesCovarianceMatrix(observable, footprints=footprint, resolution=3)()
    likelihood = ObservablesGaussianLikelihood(observables=[observable], covariance=cov)
    from desilike.emulators import Emulator, TaylorEmulatorEngine
    emulator = Emulator(theory, engine=TaylorEmulatorEngine(order=1))
    emulator.set_samples(method='finite')
    emulator.fit()
    observable.init.update(theory=emulator.to_calculator())

    for param in likelihood.all_params.select(basename=['alpha*', 'sn*', 'dptt*']):
        param.update(prior=None, derived='.best')
    likelihood()
    from desilike.utils import Monitor
    with Monitor() as mem:
        mem.start()
        for i in range(10): likelihood(b1=1. + i * 0.1)
        mem.stop()
        print(mem.get('time', average=False))

    theory = KaiserTracerPowerSpectrumMultipoles(template=ShapeFitPowerSpectrumTemplate(z=0.5))
    for param in theory.params.select(basename=['alpha*', 'sn*']): param.update(derived='.best')
    observable = TracerPowerSpectrumMultipolesObservable(klim={0: [0.05, 0.2, 0.01], 2: [0.05, 0.2, 0.01]},
                                                         data={},
                                                         theory=theory)
    footprint = BoxFootprint(volume=1e10, nbar=1e-5)
    cov = ObservablesCovarianceMatrix(observable, footprints=footprint, resolution=3)()
    likelihood = ObservablesGaussianLikelihood(observables=[observable], covariance=cov)

    from desilike.utils import Monitor
    with Monitor() as mem:
        mem.start()
        for i in range(10): likelihood(b1=1. + i * 0.1)
        mem.stop()
        print(mem.get('time', average=False))


def test_solve():

    from desilike.theories.galaxy_clustering import KaiserTracerPowerSpectrumMultipoles, LPTVelocileptorsTracerPowerSpectrumMultipoles, PyBirdTracerPowerSpectrumMultipoles, ShapeFitPowerSpectrumTemplate
    from desilike.observables.galaxy_clustering import TracerPowerSpectrumMultipolesObservable, ObservablesCovarianceMatrix, BoxFootprint
    from desilike.likelihoods import ObservablesGaussianLikelihood

    template = ShapeFitPowerSpectrumTemplate(z=0.5)
    #theory = KaiserTracerPowerSpectrumMultipoles(template=template)
    #theory = LPTVelocileptorsTracerPowerSpectrumMultipoles(template=template)
    theory = PyBirdTracerPowerSpectrumMultipoles(template=template)
    #for param in theory.params.select(basename=['df', 'dm', 'qpar', 'qper']): param.update(fixed=True)
    for param in theory.params.select(basename=['alpha*', 'sn*', 'ce*']): param.update(derived='.best')
    observable = TracerPowerSpectrumMultipolesObservable(klim={0: [0.05, 0.2, 0.01], 2: [0.05, 0.2, 0.01]},
                                                         data={},
                                                         theory=theory)
    covariance = ObservablesCovarianceMatrix(observables=observable, footprints=BoxFootprint(volume=1e10, nbar=1e-2))
    observable.init.update(covariance=covariance())
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    #for param in likelihood.all_params.select(basename=['df', 'dm', 'qpar', 'qper']): param.update(fixed=True)

    likelihood()


def test_fisher_galaxy():

    from desilike.observables.galaxy_clustering import TracerPowerSpectrumMultipolesObservable
    from desilike.likelihoods import ObservablesGaussianLikelihood, SumLikelihood
    from desilike.theories.galaxy_clustering import KaiserTracerPowerSpectrumMultipoles, LPTVelocileptorsTracerPowerSpectrumMultipoles, DirectPowerSpectrumTemplate

    theory = KaiserTracerPowerSpectrumMultipoles(template=DirectPowerSpectrumTemplate(z=0.5))
    for param in theory.params.select(basename=['alpha*', 'sn*']): param.update(derived='.best')
    observable = TracerPowerSpectrumMultipolesObservable(klim={0: [0.05, 0.2, 0.01], 2: [0.05, 0.18, 0.01]},
                                                         data='_pk/data.npy', covariance='_pk/mock_*.npy', wmatrix='_pk/window.npy',
                                                         theory=theory)
    likelihood = ObservablesGaussianLikelihood(observables=[observable], scale_covariance=False)
    likelihood.all_params['logA'].update(derived='jnp.log(10 *  {A_s})', prior=None)
    likelihood.all_params['A_s'] = {'prior': {'limits': [1.9, 2.2]}, 'ref': {'dist': 'norm', 'loc': 2.083, 'scale': 0.01}}
    for param in likelihood.all_params.select(name=['m_ncdm', 'w0_fld', 'wa_fld', 'Omega_k']):
        param.update(fixed=False)

    #print(likelihood(w0_fld=-1), likelihood(w0_fld=-1.1))
    #print(likelihood(wa_fld=0), likelihood(wa_fld=0.1))
    from desilike import Fisher
    fisher = Fisher(likelihood)
    #like = fisher()
    #print(like.to_stats())
    from desilike import mpi
    fisher.mpicomm = mpi.COMM_SELF
    like = fisher()
    print(like.to_stats())


def test_fisher_cmb():
    from desilike import Fisher, FisherGaussianLikelihood
    from desilike.likelihoods.cmb import BasePlanck2018GaussianLikelihood, TTTEEEHighlPlanck2018PlikLikelihood, TTHighlPlanck2018PlikLiteLikelihood,\
                                         TTTEEEHighlPlanck2018PlikLiteLikelihood, TTLowlPlanck2018ClikLikelihood,\
                                         EELowlPlanck2018ClikLikelihood, LensingPlanck2018ClikLikelihood
    from desilike.likelihoods import SumLikelihood
    from desilike.theories.primordial_cosmology import Cosmoprimo
    # Now let's turn to Planck (lite) clik likelihoods
    cosmo = Cosmoprimo(fiducial='DESI')
    likelihoods = [Likelihood(cosmo=cosmo) for Likelihood in [TTTEEEHighlPlanck2018PlikLiteLikelihood, TTLowlPlanck2018ClikLikelihood,\
                                                              EELowlPlanck2018ClikLikelihood, LensingPlanck2018ClikLikelihood]]
    likelihood_clik = SumLikelihood(likelihoods=likelihoods)
    for param in likelihood_clik.all_params:
        param.update(fixed=True)
    likelihood_clik.all_params['m_ncdm'].update(fixed=False)
    fisher_clik = Fisher(likelihood_clik)
    # Planck covariance matrix used above should roughly correspond to Fisher at the Planck posterior bestfit
    # at which logA ~= 3.044 (instead of logA = ln(1e10 2.0830e-9) = 3.036 assumed in the DESI fiducial cosmology)
    fisher_clik = fisher_clik()
    print(fisher_clik.to_stats(tablefmt='pretty'))
    for likelihood in likelihood_clik.likelihoods:
        print(likelihood, likelihood.loglikelihood)
    fisher_likelihood_clik = fisher_clik.to_likelihood()
    print(fisher_likelihood_clik.all_params)
    print(likelihood_clik(), fisher_likelihood_clik())
    fn = '_tests/test.npy'
    fisher_likelihood_clik.save(fn)
    fisher_likelihood_clik2 = FisherGaussianLikelihood.load(fn)
    assert np.allclose(fisher_likelihood_clik2(), fisher_likelihood_clik())


if __name__ == '__main__':

    setup_logging()
    #test_misc()
    #test_differentiation()
    #test_solve()
    test_fisher_galaxy()
    test_fisher_cmb()

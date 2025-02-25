import glob
import numpy as np

from desilike import setup_logging
from desilike.likelihoods import ObservablesGaussianLikelihood


def test_power_spectrum():

    from cosmoprimo.fiducial import DESI
    from desilike.theories.galaxy_clustering import DampedBAOWigglesTracerPowerSpectrumMultipoles, KaiserTracerPowerSpectrumMultipoles, ShapeFitPowerSpectrumTemplate
    from desilike.observables.galaxy_clustering import TracerPowerSpectrumMultipolesObservable, TopHatFiberCollisionsPowerSpectrumMultipoles, BoxFootprint, ObservablesCovarianceMatrix

    template = ShapeFitPowerSpectrumTemplate(z=0.5, fiducial=DESI())
    theory = KaiserTracerPowerSpectrumMultipoles(template=template)

    size = 10
    ells = (0, 2)
    observable = TracerPowerSpectrumMultipolesObservable(data=np.ravel([np.linspace(0., 1., size)] * len(ells)),
                                                         k=np.linspace(0.01, 0.1, size),
                                                         ells=ells,
                                                         covariance=np.eye(size * len(ells)),
                                                         theory=theory)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    likelihood()

    observable = TracerPowerSpectrumMultipolesObservable(klim={0: [0.05, 0.2, 0.01], 2: [0.05, 0.2, 0.01]},
                                                         data='../../tests/_pk/data.npy',
                                                         covariance=glob.glob('../../tests/_pk/mock_*.npy'),
                                                         wmatrix='../../tests/_pk/window.npy',
                                                         theory=theory)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    likelihood()
    assert np.allclose(likelihood.flatdiff, observable.wmatrix.flatpower - observable.flatdata)
    theory()

    fiber_collisions = TopHatFiberCollisionsPowerSpectrumMultipoles(fs=0.5, Dfc=1.)
    observable = TracerPowerSpectrumMultipolesObservable(klim={0: [0.05, 0.2, 0.01], 2: [0.05, 0.2, 0.01]},
                                                         data='../../tests/_pk/data.npy',
                                                         covariance='../../tests/_pk/mock_*.npy',
                                                         wmatrix='../../tests/_pk/window.npy',
                                                         shotnoise=1e4,
                                                         theory=theory,
                                                         fiber_collisions=fiber_collisions,
                                                         kinlim=(0., 0.24),
                                                         transform='cubic')
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    likelihood.params['pk.loglikelihood'] = {}
    likelihood.params['pk.logprior'] = {}
    likelihood()
    #observable.plot(show=True)
    observable()
    #observable.wmatrix.plot(show=True)
    theory.template.init.update(z=1.)
    observable()
    #print(observable.runtime_info.pipeline.varied_params)
    assert theory.template.z == 1.
    likelihood()
    assert np.allclose((likelihood + likelihood)(), 2. * likelihood() - likelihood.logprior)
    assert np.allclose(likelihood.flatdiff, 3. * observable.flatdata * (np.cbrt(observable.wmatrix.flatpower / observable.flatdata) - 1.))

    theory = DampedBAOWigglesTracerPowerSpectrumMultipoles()
    params = {'al0_1': 100., 'al0_-1': 100., 'al2_1': 100., 'b1': 1.5}
    observable = TracerPowerSpectrumMultipolesObservable(klim={0: [0.05, 0.2, 0.01], 2: [0.05, 0.2, 0.01]},
                                                         data=params,
                                                         wmatrix=dict(resolution=2),
                                                         theory=theory)
    footprint = BoxFootprint(volume=1e10, nbar=1e-3)
    cov = ObservablesCovarianceMatrix(observable, footprints=footprint, resolution=3)(**params)
    likelihood = ObservablesGaussianLikelihood(observables=observable, covariance=cov)
    print(likelihood(**params))
    observable.plot(show=True)
    observable.wmatrix.plot(show=True)
    observable.plot_wiggles(show=True)

    observable = TracerPowerSpectrumMultipolesObservable(klim={0: [0.05, 0.2, 0.01], 2: [0.05, 0.2, 0.01]},
                                                         data=params,
                                                         wmatrix=dict(resolution=2),
                                                         fiber_collisions=fiber_collisions,
                                                         theory=theory)
    footprint = BoxFootprint(volume=1e10, nbar=1e-3)
    cov = ObservablesCovarianceMatrix(observable, footprints=footprint, resolution=3)(**params)
    likelihood = ObservablesGaussianLikelihood(observables=observable, covariance=cov)
    print(likelihood(**params))

    observable = TracerPowerSpectrumMultipolesObservable(klim={0: [0.05, 0.2, 0.01], 2: [0.05, 0.2, 0.01]},
                                                         data=params,
                                                         wmatrix='../../tests/_pk/window.npy',
                                                         theory=theory)
    footprint = BoxFootprint(volume=1e10, nbar=1e-3)
    cov = ObservablesCovarianceMatrix(observable, footprints=footprint, resolution=3)(**params)
    likelihood = ObservablesGaussianLikelihood(observables=observable, covariance=cov)
    print(likelihood(**params))
    #observable.plot_wiggles(show=True)


def test_correlation_function():

    from desilike.theories.galaxy_clustering import KaiserTracerCorrelationFunctionMultipoles, LPTVelocileptorsTracerCorrelationFunctionMultipoles, FOLPSTracerCorrelationFunctionMultipoles, ShapeFitPowerSpectrumTemplate
    from desilike.observables.galaxy_clustering import TracerCorrelationFunctionMultipolesObservable, TopHatFiberCollisionsCorrelationFunctionMultipoles

    template = ShapeFitPowerSpectrumTemplate(z=0.5)
    theory = KaiserTracerCorrelationFunctionMultipoles(template=template)
    #theory = LPTVelocileptorsTracerCorrelationFunctionMultipoles(template=template, ells=(0, 2))
    size = 10
    ells = (0, 2)
    observable = TracerCorrelationFunctionMultipolesObservable(data=np.ravel([np.linspace(0., 1., size)] * len(ells)),
                                                               s=np.linspace(20., 150., size),
                                                               ells=ells,
                                                               covariance=np.eye(size * len(ells)),
                                                               theory=theory)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    likelihood()

    observable = TracerCorrelationFunctionMultipolesObservable(slim={0: [20., 150., 5.], 2: [20., 150., 5.]},
                                                               data='../../tests/_xi/data.npy',
                                                               covariance=glob.glob('../../tests/_xi/mock_*.npy'),
                                                               theory=theory)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    likelihood()
    theory()
    fiber_collisions = TopHatFiberCollisionsCorrelationFunctionMultipoles(fs=0.5, Dfc=1.)
    observable = TracerCorrelationFunctionMultipolesObservable(slim={0: [20., 150., 5.], 2: [20., 150., 5.]},
                                                               data='../../tests/_xi_fft/data.npy',
                                                               covariance='../../tests/_xi_fft/mock_*.npy',
                                                               theory=theory,
                                                               fiber_collisions=fiber_collisions)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    observable()
    observable.plot(show=True)

    fiber_collisions = TopHatFiberCollisionsCorrelationFunctionMultipoles(fs=0.5, Dfc=1.)
    observable = TracerCorrelationFunctionMultipolesObservable(slim={0: [20., 150., 5.], 2: [20., 150., 5.]},
                                                               data={}, #'../../tests/_xi/data.npy',
                                                               covariance='../../tests/_xi/mock_*.npy',
                                                               theory=theory,
                                                               fiber_collisions=fiber_collisions)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    likelihood()
    theory.power.template.init.update(z=1.)
    observable()
    observable.plot(show=True)
    print(observable.runtime_info.pipeline.varied_params)
    assert theory.power.template.z == 1.

    observable = TracerCorrelationFunctionMultipolesObservable(slim={0: [20., 150., 5.], 2: [20., 150., 5.]},
                                                               data={}, #'../../tests/_xi/data.npy',
                                                               covariance='../../tests/_xi/mock_*.npy',
                                                               theory=theory,
                                                               wmatrix={'resolution': 2})
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    observable.wmatrix.plot(show=True)

    observable = TracerCorrelationFunctionMultipolesObservable(slim={0: [20., 150., 5.], 2: [20., 150., 5.]},
                                                               data={}, #'../../tests/_xi/data.npy',
                                                               covariance='../../tests/_xi/mock_*.npy',
                                                               theory=theory,
                                                               wmatrix={'resolution': 2},
                                                               fiber_collisions=fiber_collisions)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    observable.wmatrix.plot(show=True)


def test_bao():

    from cosmoprimo.fiducial import DESI
    from desilike.theories.galaxy_clustering import DampedBAOWigglesTracerPowerSpectrumMultipoles, BAOPowerSpectrumTemplate
    from desilike.observables.galaxy_clustering import TracerPowerSpectrumMultipolesObservable

    template = BAOPowerSpectrumTemplate(z=0.38, fiducial=DESI())
    theory = DampedBAOWigglesTracerPowerSpectrumMultipoles(template=template)
    theory.init.params = theory.init.params.select(basename='al0_*')
    theory.init.params.set(theory.init.params['al0_0'].clone(name='al0_6'))
    observable = TracerPowerSpectrumMultipolesObservable(data='../../tests/_pk/data.npy',
                                                         covariance='../../tests/_pk/mock_*.npy',
                                                         klim={0: [0.01, 0.3]},
                                                         wmatrix='../../tests/_pk/window.npy',
                                                         theory=theory)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])

    setup_logging()
    print(likelihood.all_params)


def test_footprint():
    from desilike.observables.galaxy_clustering import BoxFootprint, CutskyFootprint
    from cosmoprimo.fiducial import DESI
    fn = '_tests/footprint.npy'
    footprint = BoxFootprint(volume=1e10, nbar=1e-3)
    footprint.save(fn)
    footprint = BoxFootprint.load(fn)
    footprint = CutskyFootprint(nbar=2500., area=14000., zrange=(0.8, 1.6), cosmo=DESI())
    footprint.save(fn)
    footprint = CutskyFootprint.load(fn)
    print(footprint.zavg, footprint.size / 1e6, footprint.shotnoise, footprint.volume / 1e9)


def test_covariance_matrix():

    from desilike.theories.galaxy_clustering import (ShapeFitPowerSpectrumTemplate,
                                                     KaiserTracerPowerSpectrumMultipoles, KaiserTracerCorrelationFunctionMultipoles,
                                                     LPTVelocileptorsTracerPowerSpectrumMultipoles, LPTVelocileptorsTracerCorrelationFunctionMultipoles)
    from desilike.observables.galaxy_clustering import TracerCorrelationFunctionMultipolesObservable, BoxFootprint, ObservablesCovarianceMatrix

    template = ShapeFitPowerSpectrumTemplate(z=1.1)
    #theory = LPTVelocileptorsTracerCorrelationFunctionMultipoles(template=template)
    theory =  KaiserTracerCorrelationFunctionMultipoles(template=template)
    footprint = BoxFootprint(volume=1e10, nbar=1e-4)
    observable = TracerCorrelationFunctionMultipolesObservable(slim={0: [30., 150., 4.], 2: [30., 150., 4.], 4: [30., 150., 4.]},
                                                               data={},  #'../../tests/_xi/data.npy',
                                                               theory=theory)

    cov = ObservablesCovarianceMatrix(observable, footprints=footprint, resolution=3)
    likelihood = ObservablesGaussianLikelihood(observables=[observable], covariance=cov())
    print(likelihood())
    #observable.plot(show=True)
    observable.plot_covariance_matrix(show=True, corrcoef=True)

    #theory_pk = LPTVelocileptorsTracerPowerSpectrumMultipoles(template=template)
    theory_pk = KaiserTracerPowerSpectrumMultipoles(template=template)
    cov = ObservablesCovarianceMatrix(observable, footprints=footprint, theories=theory_pk, resolution=3)
    likelihood = ObservablesGaussianLikelihood(observables=[observable], covariance=cov())
    print(likelihood())
    #observable.plot(show=True)
    observable.plot_covariance_matrix(show=True, corrcoef=True)

    from desilike.observables.galaxy_clustering import TracerPowerSpectrumMultipolesObservable, BoxFootprint, ObservablesCovarianceMatrix

    template = ShapeFitPowerSpectrumTemplate(z=0.5)
    theory = KaiserTracerPowerSpectrumMultipoles(template=template)
    footprint = BoxFootprint(volume=1e10, nbar=1e-5)
    observable = TracerPowerSpectrumMultipolesObservable(klim={0: [0.05, 0.2, 0.01], 2: [0.05, 0.2, 0.01], 4: [0.05, 0.2, 0.01]},
                                                         data={},  #'../../tests/_xi/data.npy',
                                                         theory=theory)
    cov = ObservablesCovarianceMatrix(observable, footprints=footprint, resolution=3)
    likelihood = ObservablesGaussianLikelihood(observables=[observable], covariance=cov())
    print(likelihood())
    #observable.plot(show=True)
    observable.plot_covariance_matrix(show=True, corrcoef=True)

    from desilike.theories.galaxy_clustering import ShapeFitPowerSpectrumTemplate
    from desilike.observables.galaxy_clustering import TracerPowerSpectrumMultipolesObservable, TracerCorrelationFunctionMultipolesObservable, BoxFootprint, ObservablesCovarianceMatrix

    template = ShapeFitPowerSpectrumTemplate(z=0.5)
    footprint = BoxFootprint(volume=1e10, nbar=1e-5)
    theory = KaiserTracerPowerSpectrumMultipoles(template=template)
    observable1 = TracerPowerSpectrumMultipolesObservable(klim={0: [0.05, 0.2, 0.01], 2: [0.05, 0.2, 0.01]},
                                                          data={},  #'../../tests/_xi/data.npy',
                                                          theory=theory)
    theory = KaiserTracerCorrelationFunctionMultipoles(template=template)
    observable2 = TracerCorrelationFunctionMultipolesObservable(slim={0: [20., 150., 5.], 2: [20., 150., 5.]},
                                                                data={},  #'../../tests/_xi/data.npy',
                                                                theory=theory)
    observables = [observable1, observable2]
    cov = ObservablesCovarianceMatrix(observables, footprints=footprint, resolution=3)()
    likelihood = ObservablesGaussianLikelihood(observables=observables, covariance=cov)
    print(likelihood())
    #observable.plot(show=True)
    likelihood.plot_covariance_matrix(show=True, corrcoef=True)


def test_covariance_matrix_mocks():

    from desilike.theories.galaxy_clustering import KaiserTracerPowerSpectrumMultipoles, KaiserTracerCorrelationFunctionMultipoles, ShapeFitPowerSpectrumTemplate
    from desilike.observables.galaxy_clustering import TracerPowerSpectrumMultipolesObservable, TracerCorrelationFunctionMultipolesObservable, BoxFootprint, ObservablesCovarianceMatrix

    template = ShapeFitPowerSpectrumTemplate(z=0.5)
    theory = KaiserTracerPowerSpectrumMultipoles(template=template)

    pk_mocks, xi_mocks = '../../tests/_pk/mock_*.npy', '../../tests/_xi/mock_*.npy'
    data = {'b1': 2.}

    #pk_mocks, xi_mocks = '../../tests/_pk_shotnoise/mock_*.npy', '../../tests/_xi_shotnoise/mock_*.npy'
    #data = {'b1': 0., 'df': 0.}

    klim = {0: [0.05, 0.2, 0.01], 2: [0.05, 0.2, 0.01], 4: [0.05, 0.2, 0.01]}
    #klim = {0: [0.05, 0.2, 0.02], 2: [0.05, 0.2, 0.02], 4: [0.05, 0.2, 0.02]}
    observable_pk_mocks = TracerPowerSpectrumMultipolesObservable(klim=klim, data=pk_mocks, covariance=pk_mocks, theory=theory)

    observable_pk_mocks(**data)
    shotnoise = observable_pk_mocks.shotnoise[0]
    footprint = BoxFootprint(volume=500**3, nbar=1. / shotnoise)

    observable_pk = TracerPowerSpectrumMultipolesObservable(klim=klim, data=data, theory=theory)

    covariance = ObservablesCovarianceMatrix(observable_pk, footprints=footprint, resolution=3)(**data)
    observable_pk.init.update(covariance=covariance)
    observable_pk(**data)

    #observable_pk_mocks.plot(show=True)
    from matplotlib import pyplot as plt
    ax = plt.gca()
    for ill, ell in enumerate(observable_pk.ells):
        ax.plot(observable_pk.k[ill], observable_pk_mocks.std[ill] / observable_pk.std[ill], color='C{:d}'.format(ill), label=r'$\ell = {:d}$'.format(ell))
    ax.legend()
    plt.show()

    theory = KaiserTracerCorrelationFunctionMultipoles(template=template)
    slim = {0: [20., 80., 4.], 2: [20., 80., 4.], 4: [20., 80., 4.]}
    #slim = {0: [20., 80., 2.], 2: [20., 80., 2.], 4: [20., 80., 2.]}
    observable_xi_mocks = TracerCorrelationFunctionMultipolesObservable(slim=slim, data=xi_mocks, covariance=xi_mocks, theory=theory)

    observable_xi_mocks(**data)
    observable_xi = TracerCorrelationFunctionMultipolesObservable(slim=slim, data=data, theory=theory)
    covariance = ObservablesCovarianceMatrix(observable_xi, footprints=footprint, resolution=3)(**data)
    observable_xi.init.update(covariance=covariance)
    observable_xi(**data)

    #observable_xi_mocks.plot(show=True)
    from matplotlib import pyplot as plt
    ax = plt.gca()
    for ill, ell in enumerate(observable_xi.ells):
        ax.plot(observable_xi.s[ill], observable_xi_mocks.std[ill] / observable_xi.std[ill], color='C{:d}'.format(ill), label=r'$\ell = {:d}$'.format(ell))
    ax.legend()
    plt.show()

    ax = plt.gca()
    index = np.arange(observable_xi_mocks.covariance.shape[0])
    for offset in range(1, 5):
        indices = (index[:-offset], index[offset:])
        ax.plot(observable_xi_mocks.covariance[indices] / observable_xi.covariance[indices])
    ax.set_ylim(0., 3.)
    plt.show()

    covariance = ObservablesCovarianceMatrix([observable_pk, observable_xi], footprints=footprint, resolution=3)(**data)
    likelihood_mocks = ObservablesGaussianLikelihood([observable_pk_mocks, observable_xi_mocks])
    likelihood = ObservablesGaussianLikelihood([observable_pk, observable_xi], covariance=covariance)

    ax = plt.gca()
    index = np.arange(likelihood_mocks.covariance.shape[0])
    for offset in [1, observable_pk.covariance.shape[0], observable_pk.covariance.shape[0] + 1]:
        indices = (index[:-offset], index[offset:])
        ax.plot(likelihood_mocks.covariance[indices] / likelihood.covariance[indices])
    ax.set_ylim(0., 3.)
    plt.show()

    likelihood_mocks.plot_covariance_matrix(show=True)
    likelihood.plot_covariance_matrix(show=True)


def test_compression():

    from desilike import LikelihoodFisher

    from desilike.observables.galaxy_clustering import BAOCompressionObservable, StandardCompressionObservable, ShapeFitCompressionObservable, WiggleSplitCompressionObservable, BandVelocityCompressionObservable, TurnOverCompressionObservable
    from desilike.emulators import Emulator, TaylorEmulatorEngine

    def test(likelihood, emulate=True, test_zero=False):
        print(likelihood.varied_params)
        likelihood_bak = likelihood()
        if test_zero:
            assert np.allclose(likelihood.loglikelihood, 0.)
        print(likelihood_bak)
        if emulate:
            emulator = Emulator(likelihood.observables, engine=TaylorEmulatorEngine(order=1))
            emulator.set_samples()
            emulator.fit()
            likelihood.init.update(observables=emulator.to_calculator())
            assert np.allclose(likelihood(), likelihood_bak)

    observable = BAOCompressionObservable(data=[1., 1.], covariance=np.diag([0.01, 0.01]), quantities=['qpar', 'qper'], z=2.)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    test(likelihood)

    observable = BAOCompressionObservable(data=[1., 1.], quantities=['DM_over_rd', 'DH_over_rd'], z=2.)
    observable2 = BAOCompressionObservable(data=[1., 1.], quantities=['DM_over_rd', 'DH_over_rd'], z=2.)
    likelihood = ObservablesGaussianLikelihood(observables=[observable, observable2], covariance=np.diag([0.01, 0.01, 0.01, 0.01]))
    test(likelihood)

    observable = BAOCompressionObservable(data=[1.], covariance=np.diag([0.01]), quantities=['DV_over_rd'], z=2.)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    test(likelihood)

    fisher = LikelihoodFisher(center=[0.], params=['qiso'], offset=0., hessian=[[1.]], with_prior=True)
    observable = BAOCompressionObservable(data=fisher, covariance=fisher, z=2.)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    test(likelihood)

    observable = BAOCompressionObservable(data=np.array([1.]), covariance=np.diag([0.01]), quantities=['qiso'], z=2.)
    likelihood = ObservablesGaussianLikelihood(observables=observable)
    test(likelihood)

    observable = StandardCompressionObservable(data=[1., 1., 1.], covariance=np.diag([0.01, 0.01, 0.01]), quantities=['qpar', 'qper', 'df'], z=2.)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    test(likelihood)

    observable = ShapeFitCompressionObservable(data=[1., 1., 0., 0.8], covariance=np.diag([0.01, 0.01, 0.0001, 0.01]), quantities=['qpar', 'qper', 'm', 'f_sqrt_Ap'], z=2.)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    test(likelihood)

    observable = ShapeFitCompressionObservable(data=[1., 1., 0., 1.], covariance=np.diag([0.01, 0.01, 0.0001, 0.01]), quantities=['qiso', 'qap', 'dm', 'df'], z=2.)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    test(likelihood)

    observable = WiggleSplitCompressionObservable(data=[1., 1., 1., 0.], covariance=np.diag([0.01, 0.01, 0.01, 0.01]), quantities=['qap', 'qbao', 'df', 'dm'], z=2.)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    test(likelihood)

    observable = BandVelocityCompressionObservable(data=[1., 1., 1.], covariance=np.diag([0.01, 0.01, 0.01]), kp=[0.01, 0.1], quantities=['dptt0', 'dptt1', 'qap'], z=2.)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    test(likelihood)

    observable = TurnOverCompressionObservable(data=[1.], covariance=np.diag([0.01]), quantities=['qto'], z=2.)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    test(likelihood, test_zero=True)

    from desilike import ParameterCovariance
    covariance = ParameterCovariance(value=np.diag([0.01, 0.01, 0.01]), params=['qpar', 'qper', 'df'])
    observable = StandardCompressionObservable(data={}, covariance=covariance, quantities=['qpar', 'qper', 'df'], z=2.)
    likelihood = ObservablesGaussianLikelihood(observables=[observable])
    test(likelihood)


def test_integral_cosn():

    from desilike.observables.galaxy_clustering.window import integral_cosn

    for n in np.arange(6):
        limits = (-0.3, 0.8)
        x = np.linspace(*limits, num=1000)
        ref = np.trapz(np.cos(x)**n, x=x)
        test = integral_cosn(n=n, range=limits)
        assert np.abs(test / ref - 1.) < 1e-6


def test_fiber_collisions():

    from matplotlib import pyplot as plt
    from desilike.observables.galaxy_clustering import (FiberCollisionsPowerSpectrumMultipoles, FiberCollisionsCorrelationFunctionMultipoles,
                                                        TopHatFiberCollisionsPowerSpectrumMultipoles, TopHatFiberCollisionsCorrelationFunctionMultipoles)
    from desilike.observables.galaxy_clustering import WindowedCorrelationFunctionMultipoles, WindowedPowerSpectrumMultipoles
    """
    fs, Dfc = 0.5, 3.
    ells = (0, 2, 4)

    fiber_collisions = TopHatFiberCollisionsPowerSpectrumMultipoles(fs=fs, Dfc=Dfc, ells=ells)
    fiber_collisions()
    ax = fiber_collisions.plot()

    n = 10
    sep = np.linspace(0., Dfc, n)
    kernel = np.linspace(fs, 0., n)
    fiber_collisions = FiberCollisionsPowerSpectrumMultipoles(sep=sep, kernel=kernel, ells=ells)
    fiber_collisions()

    for ill, ell in enumerate(fiber_collisions.ells):
        color = 'C{:d}'.format(ill)
        ax.plot(fiber_collisions.k, fiber_collisions.k * fiber_collisions.power[ill], color=color, linestyle=':', label=r'$\ell = {:d}$'.format(ell))
    ax.legend()
    plt.show()

    s = np.linspace(1., 200., 200)
    fiber_collisions = TopHatFiberCollisionsCorrelationFunctionMultipoles(s=s, fs=fs, Dfc=Dfc, ells=ells)
    fiber_collisions()
    ax = fiber_collisions.plot()
    # ax.get_legend().remove()

    n = 10
    sep = np.linspace(0., Dfc, n)
    kernel = np.linspace(fs, 0., n)
    fiber_collisions = FiberCollisionsCorrelationFunctionMultipoles(s=s, sep=sep, kernel=kernel, ells=ells)
    fiber_collisions()
    for ill, ell in enumerate(fiber_collisions.ells):
        color = 'C{:d}'.format(ill)
        ax.plot(fiber_collisions.s, fiber_collisions.s**2 * fiber_collisions.corr[ill], color=color, linestyle=':')
    ax.legend()
    plt.show()

    fs, Dfc = 0.5, 3.
    ells = (0, 2, 4)
    fiber_collisions = TopHatFiberCollisionsPowerSpectrumMultipoles(fs=fs, Dfc=Dfc, ells=ells)
    window = WindowedPowerSpectrumMultipoles(k=np.linspace(0.01, 0.2, 50), fiber_collisions=fiber_collisions)
    window()
    window.plot(show=True)
    """

    fs, Dfc = 0.5, 3.
    ells = (0, 2, 4)
    fiber_collisions = TopHatFiberCollisionsCorrelationFunctionMultipoles(fs=fs, Dfc=Dfc, ells=ells, with_uncorrelated=False, mu_range_cut=True)
    window = WindowedCorrelationFunctionMultipoles(s=np.linspace(20, 150, 50), fiber_collisions=fiber_collisions)
    window()
    window.plot(show=True)


from desilike.base import BaseCalculator


class CompressionWindow(BaseCalculator):

    def initialize(self, likelihood, observable, quantities):
        self.likelihood = likelihood
        self.observable = observable
        self.quantities = [str(name) for name in quantities]
        self.runtime_info.requires = [self.observable]

    def calculate(self):
        self.likelihood.flatdata = self.observable.flattheory.copy()
        for i in range(3):
            self.likelihood()  # find parameter best fit (iteratively in case order > 1)
        #self.likelihood.observables[0].plot(show=True)
        self.values = {}
        for quantity in self.quantities:
            self.values[quantity] = self.likelihood.runtime_info.pipeline.input_values[quantity]

    def get(self):
        return self.values

    def __getstate__(self):
        state = {'compression_{}'.format(quantity): value for quantity, value in self.values.items()}
        for name in ['quantities']: state[name] = getattr(self, name)
        return state

    def __setstate__(self, state):
        for name in ['quantities']: setattr(self, name, state[name])
        self.values = {quantity: state['compression_{}'.format(quantity)] for quantity in self.quantities}


def test_compression_window():

    from desilike.theories.galaxy_clustering import StandardPowerSpectrumTemplate, DirectPowerSpectrumTemplate, BandVelocityPowerSpectrumTemplate, KaiserTracerPowerSpectrumMultipoles
    from desilike.observables.galaxy_clustering import TracerPowerSpectrumMultipolesObservable, BoxFootprint, ObservablesCovarianceMatrix

    z, b1 = 1., 2.
    order = 2
    kwargs_template = {'only_now': 'peakaverage', 'z': z, 'fiducial': 'DESI'}
    theory_compression = KaiserTracerPowerSpectrumMultipoles(template=StandardPowerSpectrumTemplate(**kwargs_template, apmode='qap'))
    theory_compression.params['b1'].update(fixed=False, value=b1)
    #theory_compression.params['sn0'].update(fixed=True, value=0.)
    observable_compression = TracerPowerSpectrumMultipolesObservable(klim={0: [0.01, 0.15, 0.01], 2: [0.01, 0.15, 0.01], 4: [0.01, 0.15, 0.01]},
                                                                     data={},
                                                                     theory=theory_compression)

    footprint = BoxFootprint(volume=1e10, nbar=1e-3)
    cov = ObservablesCovarianceMatrix(observable_compression, footprints=footprint)()
    likelihood_compression = ObservablesGaussianLikelihood(observables=observable_compression, covariance=cov)
    #likelihood_compression.all_params['df'].update(fixed=True)
    #likelihood_compression.all_params['qap'].update(fixed=True)
    #for param in likelihood_compression.all_params.select(basename='q*'):
    #    param.update(fixed=True)
    from desilike.emulators import Emulator, TaylorEmulatorEngine
    emulator = Emulator(theory_compression, engine=TaylorEmulatorEngine(order=order))
    emulator.set_samples()
    emulator.fit()

    observable_compression.init.update(theory=emulator.to_calculator())
    for param in likelihood_compression.varied_params:
        param.update(prior=None, derived='.best')

    # Theory is band power + AP
    template_band = BandVelocityPowerSpectrumTemplate(**kwargs_template)
    theory_band = KaiserTracerPowerSpectrumMultipoles(template=template_band)
    theory_band.params['b1'].update(fixed=False, value=b1)
    for param in theory_band.params: param.update(fixed=True)

    observable_band = observable_compression.deepcopy()
    kp = np.unique(np.concatenate(observable_compression.k))
    template_band.init.update(kp=kp)
    observable_band.init.update(theory=theory_band)
    compression_window = CompressionWindow(likelihood=likelihood_compression, observable=observable_band, quantities=theory_compression.template.varied_params)
    #compression_window.all_params['qap'].update(fixed=True)

    from desilike.emulators import Emulator, TaylorEmulatorEngine
    emulator = Emulator(compression_window, engine=TaylorEmulatorEngine(order=order))
    emulator.set_samples()
    #print(emulator.samples['compression_df']['compression_df'], emulator.samples['compression_df']['compression_df'].derivs)
    #print(emulator.samples['compression_qap']['compression_qap'], emulator.samples['compression_qap']['compression_qap'].derivs)
    emulator.fit()
    emulated_compression_window = emulator.to_calculator()
    #emulated_compression_window()

    observable_compression.init.update(theory=theory_compression)
    observable_direct = observable_compression.deepcopy()
    template_direct = DirectPowerSpectrumTemplate(**kwargs_template)
    theory_direct = KaiserTracerPowerSpectrumMultipoles(template=template_direct)
    theory_direct.params['b1'].update(fixed=False, value=b1)
    #theory_direct.params['sn0'].update(fixed=True, value=0.)
    observable_direct.init.update(theory=theory_direct)
    #observable_direct.wmatrix.theory.init.update(template=template_direct)
    #print(observable_direct.all_params, print(observable_direct.wmatrix.theory.template))

    from desilike.profilers import MinuitProfiler

    #likelihood_compression.all_params['qap'].update(fixed=True)
    profiler = MinuitProfiler(likelihood_compression, seed=42)
    bestfits, expected_no_window, expected_no_window_grid, expected_with_window = [], [], [], []

    def get_expected_no_window(grid_coordinates=False):
        cosmo, fiducial = template_direct.cosmo, template_direct.fiducial
        fo = fiducial.get_fourier()
        r = 8.
        fsigma8_fid = fo.sigma_rz(r, template_direct.z, of='theta_cb')
        qper, qpar = cosmo.comoving_angular_distance(template_direct.z) / fiducial.comoving_angular_distance(template_direct.z), fiducial.efunc(template_direct.z) / cosmo.efunc(template_direct.z)
        qiso = qpar**(1. / 3.) * qper**(2. / 3.)
        qap = qpar / qper
        fo = cosmo.get_fourier()
        if grid_coordinates: r *= qiso
        df = fo.sigma_rz(r, template_direct.z, of='theta_cb') / fsigma8_fid
        return {'qiso': qiso, 'qap': qap, 'df': df}

    def get_expected_with_window():
        cosmo, fiducial = template_direct.cosmo, template_direct.fiducial
        qper, qpar = cosmo.comoving_angular_distance(template_direct.z) / fiducial.comoving_angular_distance(template_direct.z), fiducial.efunc(template_direct.z) / cosmo.efunc(template_direct.z)
        qiso = qpar**(1. / 3.) * qper**(2. / 3.)
        qap = qpar / qper
        # Move pk_tt to grid coordinates
        pk_tt = 1. / qiso**3 * cosmo.get_fourier().pk_interpolator(of='theta_cb')(kp / qiso, z=template_direct.z)
        #pk_tt = cosmo.get_fourier().pk_interpolator(of='theta_cb')(kp, z=template_direct.z)
        # Compare to fiducial
        pk_tt /= fiducial.get_fourier().pk_interpolator(of='theta_cb')(kp, z=template_direct.z)
        '''
        pk_tt = 1. / qiso**3 * cosmo.get_fourier().pk_interpolator(of='delta_cb')(kp / qiso, z=template_direct.z)
        pk_tt /= fiducial.get_fourier().pk_interpolator(of='delta_cb')(kp, z=template_direct.z)
        fo = fiducial.get_fourier()
        f_fid = fo.sigma8_z(template_direct.z, of='theta_cb') / fo.sigma8_z(template_direct.z, of='delta_cb')
        fo = cosmo.get_fourier()
        r = 8. * qiso
        f = fo.sigma_rz(r, template_direct.z, of='theta_cb') / fo.sigma_rz(r, template_direct.z, of='delta_cb')
        pk_tt *= f**2 / f_fid**2
        '''
        params = {'qap': qap, **{'ptt{:d}'.format(ik): ptt for ik, ptt in enumerate(pk_tt)}}
        return emulated_compression_window(**params)

    params = {}
    #params['w0_fld'] = [-1.2, -1., -0.8]
    #params['wa_fld'] = [-0.3, 0., 0.3]
    #params['Omega_m'] = [0.27, 0.3, 0.33]
    params['Omega_m'] = [0.2, 0.3, 0.4]
    params['h'] = [0.65, 0.7, 0.75]
    import itertools
    grid_params = [dict(zip(params.keys(), values)) for values in itertools.product(*params.values())]
    for param in params:
        template_direct.params[param].update(fixed=False)

    theories = []
    for params in grid_params:
        likelihood_compression.flatdata = observable_direct(**params).flattheory
        theories.append(observable_direct.theory)
        profiles = profiler.maximize(niterations=5)
        profiler.profiles = None
        index = profiles.bestfit.logposterior.argmax()
        bestfits.append({param.name: (profiles.bestfit[param][index], profiles.error[param][index]) for param in profiles.bestfit.params(varied=True)})
        expected_no_window.append(get_expected_no_window(grid_coordinates=False))
        expected_no_window_grid.append(get_expected_no_window(grid_coordinates=True))
        expected_with_window.append(get_expected_with_window())
        print('besfit', bestfits[-1])
        print('no window', expected_no_window[-1])
        print('no window grid', expected_no_window_grid[-1])
        print('with window', expected_with_window[-1])

    params_compression = emulated_compression_window.quantities

    from matplotlib import pyplot as plt
    fig, lax = plt.subplots(1, len(params_compression), sharex=False, sharey=False, figsize=(len(params_compression) * 5, 5), squeeze=False)
    lax = lax.flatten()
    fig.subplots_adjust(hspace=0)
    for iparam, param in enumerate(params_compression):
        ax = lax[iparam]
        '''
        ax.scatter([bestfit[param][0] for bestfit in bestfits], [expected[param] for expected in expected_no_window], color='C0', label='standard interpretation')
        ax.scatter([bestfit[param][0] for bestfit in bestfits], [expected[param] for expected in expected_no_window_grid], color='C1', label='standard interpretation in grid coordinates')
        #ax.scatter([bestfit[param][0] for bestfit in bestfits], [expected[param] for expected in expected_with_window], color='C1', label='window')
        ax.errorbar([bestfit[param][0] for bestfit in bestfits], [expected[param] for expected in expected_with_window], yerr=[bestfit[param][1] for bestfit in bestfits], color='C2', label='window', marker='o', linestyle='')
        ax.plot(ax.get_xlim(), ax.get_xlim(), linestyle='--', color='k')
        ax.set_xlabel('best fit')
        ax.set_ylabel('expected')
        '''
        ax.scatter([expected[param] for expected in expected_no_window], [bestfit[param][0] for bestfit in bestfits], color='C0', label='standard interpretation')
        ax.scatter([expected[param] for expected in expected_no_window_grid], [bestfit[param][0] for bestfit in bestfits], color='C1', label='standard interpretation in grid coordinates')
        ax.errorbar([expected[param] for expected in expected_with_window], [bestfit[param][0] for bestfit in bestfits], yerr=[bestfit[param][1] for bestfit in bestfits], color='C2', label='window', marker='o', linestyle='')
        ax.plot(ax.get_xlim(), ax.get_xlim(), linestyle='--', color='k')
        ax.set_xlabel('expected')
        ax.set_ylabel('best fit')
        ax.set_title(param)
    lax[0].legend()
    plt.show()

    ax = plt.gca()
    for ill, ell in enumerate(observable_direct.ells):
        for theory in theories:
            ax.plot(observable_direct.k[ill], observable_direct.k[ill] * theory[ill], color='C{:d}'.format(ill), alpha=0.3)
        ax.plot([], [], linestyle='-', color='C{:d}'.format(ill), label=r'$\ell = {:d}$'.format(ell))
    ax.legend()
    ax.set_xlabel(r'$k$ [$h/\mathrm{Mpc}$]')
    ax.set_ylabel(r'$k P_{\ell}(k)$ [$(\mathrm{Mpc}/h)^{2}$]')
    plt.show()


def test_shapefit(run=True, plot=True):
    from cosmoprimo.fiducial import DESI

    from desilike.samples import Chain
    from desilike.observables.galaxy_clustering import ShapeFitCompressionObservable
    from desilike.emulators import Emulator, TaylorEmulatorEngine

    z = 0.8

    if run:
        chain_shapefit = np.loadtxt('_tests/shapefit_chains_test.txt', unpack=True)
        chain_shapefit = Chain(chain_shapefit, params=['fsigma8', 'qpar', 'qper', 'dm'])

        cosmo = DESI(A_s=np.exp(3.0364) / 1e10)
        chain_shapefit['df'] = chain_shapefit['fsigma8'] / cosmo.get_fourier().sigma_rz(8., z, of='theta_m')
        #print(cosmo.growth_rate(z) * cosmo.get_fourier().sigma_rz(8., z, of='delta_cb') / cosmo.get_fourier().sigma_rz(8., z, of='theta_cb'))
        #print(cosmo.n_s, cosmo['ln10^10A_s'], cosmo.h, cosmo.Omega0_b * cosmo.h**2, cosmo.Omega0_cdm * cosmo.h**2, cosmo.N_ur, cosmo.m_ncdm)

        from desilike.theories import Cosmoprimo
        cosmo = Cosmoprimo(fiducial='DESI')
        for param in cosmo.params:
            param.update(fixed=param.basename not in ['h', 'omega_cdm', 'omega_b', 'logA'])
        cosmo.params['omega_b'].update(fixed=False, prior={'dist': 'norm', 'loc': 0.02237, 'scale': 0.00037})
        observable = ShapeFitCompressionObservable(cosmo=cosmo, data=chain_shapefit, covariance=chain_shapefit, quantities=['qpar', 'qper', 'dm', 'df'], z=z)
        emulator = Emulator(observable, engine=TaylorEmulatorEngine(method='finite', order=2))
        emulator.set_samples()
        emulator.fit()
        likelihood = ObservablesGaussianLikelihood(observables=[emulator.to_calculator()])

        from desilike.samplers import EmceeSampler
        sampler = EmceeSampler(likelihood, chains=4, seed=42, save_fn='_tests/SF_desilike_m_*.npy')
        sampler.run(min_iterations=2000, check={'max_eigen_gr': 0.03})

    if plot:
        chain = Chain.concatenate([Chain.load('_tests/SF_desilike_m_{:d}.npy'.format(i)).remove_burnin(0.5)[::10] for i in range(4)])
        chain2 = Chain.concatenate([Chain.load('_tests/SF_desilike_Appk_m_{:d}.npy'.format(i)).remove_burnin(0.5)[::10] for i in range(4)])
        #chain3 = Chain.concatenate([Chain.load('_tests/SF_desilike_Appkh_{:d}.npy'.format(i)).remove_burnin(0.5)[::10] for i in range(4)])
        #chain4 = Chain.concatenate([Chain.load('_tests/SF_desilike_Appkh_cAs_{:d}.npy'.format(i)).remove_burnin(0.5)[::10] for i in range(4)])
        chain_ref = Chain(np.loadtxt('_tests/SF_Markresult_convert-2.txt', unpack=True), params=['h', 'omega_cdm', 'omega_b', 'logA'])
        chain_ref_new = Chain(np.loadtxt('_tests/SF_convert_Mark_new.txt', unpack=True), params=['H0', 'omega_b', 'omega_cdm', 'logA'])
        chain_ref_new['h'] = chain_ref_new['H0'] / 100.
        from desilike.samples import plotting
        plotting.plot_triangle([chain, chain_ref, chain_ref_new], params=['h', 'omega_cdm', 'omega_b', 'logA'], labels=['desilike', 'Mark old code', 'Mark new code'], fn='_tests/comparison.png')


if __name__ == '__main__':

    setup_logging()

    # test_bao()
    test_power_spectrum()
    test_correlation_function()
    # test_footprint()
    # test_covariance_matrix()
    # test_covariance_matrix_mocks()
    # test_compression()
    # test_integral_cosn()
    # test_fiber_collisions()
    # test_compression_window()
    # test_shapefit(run=False)

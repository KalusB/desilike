"""Warning: not tested!"""

import re

import numpy as np
from scipy import special, integrate

from desilike.base import BaseCalculator
from desilike.theories.primordial_cosmology import get_cosmo, external_cosmo, Cosmoprimo
from desilike.jax import numpy as jnp
from .power_template import BAOPowerSpectrumTemplate
from .base import (BaseTheoryPowerSpectrumMultipoles, BaseTheoryPowerSpectrumMultipolesFromWedges,
                   BaseTheoryCorrelationFunctionMultipoles, BaseTheoryCorrelationFunctionFromPowerSpectrumMultipoles)


class BaseBAOWigglesPowerSpectrumMultipoles(BaseTheoryPowerSpectrumMultipoles):

    """Base class for theory BAO power spectrum multipoles, without broadband terms."""

    def initialize(self, *args, template=None, mode='', smoothing_radius=15., ells=(0, 2), **kwargs):
        super(BaseBAOWigglesPowerSpectrumMultipoles, self).initialize(*args, ells=ells, **kwargs)
        self.mode = str(mode)
        available_modes = ['', 'recsym', 'reciso']
        if self.mode not in available_modes:
            raise ValueError('Reconstruction mode {} must be one of {}'.format(self.mode, available_modes))
        self.smoothing_radius = float(smoothing_radius)
        if template is None:
            template = BAOPowerSpectrumTemplate()
        self.template = template


class DampedBAOWigglesPowerSpectrumMultipoles(BaseBAOWigglesPowerSpectrumMultipoles, BaseTheoryPowerSpectrumMultipolesFromWedges):
    """
    Theory BAO power spectrum multipoles, without broadband terms,
    used in the BOSS DR12 BAO analysis by Beutler et al. 2017.
    Supports pre-, reciso, recsym, real (f = 0) and redshift-space reconstruction.

    Reference
    ---------
    https://arxiv.org/abs/1607.03149
    """
    def initialize(self, *args, mu=40, method='leggauss', **kwargs):
        super(DampedBAOWigglesPowerSpectrumMultipoles, self).initialize(*args, **kwargs)
        self.set_k_mu(k=self.k, mu=mu, method=method, ells=self.ells)

    def calculate(self, b1=1., sigmas=0., sigmapar=9., sigmaper=6.):
        f = self.template.f
        jac, kap, muap = self.template.ap_k_mu(self.k, self.mu)
        pknow = self.template.pknow_dd_interpolator(kap)
        pk = self.template.pk_dd_interpolator(kap)
        sigmanl2 = kap**2 * (sigmapar**2 * muap**2 + sigmaper**2 * (1. - muap**2))
        damped_wiggles = (pk / pknow - 1.) * np.exp(-sigmanl2 / 2.)
        fog = 1. / (1. + (sigmas * kap * muap)**2 / 2.)**2.
        sk = 0.
        if self.mode == 'reciso': sk = np.exp(-1. / 2. * (kap * self.smoothing_radius)**2)
        pkmu = jac * fog * (b1 + f * muap**2 * (1 - sk))**2 * pknow * (1 + damped_wiggles)
        self.power = self.to_poles(pkmu)


class SimpleBAOWigglesPowerSpectrumMultipoles(DampedBAOWigglesPowerSpectrumMultipoles):
    r"""
    As :class:`DampedBAOWigglesPowerSpectrumMultipoles`, but moving only BAO wiggles (and not damping or RSD terms)
    with scaling parameters.
    """
    def calculate(self, b1=1., sigmas=0., sigmapar=9., sigmaper=6.):
        f = self.template.f
        jac, kap, muap = self.template.ap_k_mu(self.k, self.mu)
        pknow = self.template.pknow_dd_interpolator(self.k)[:, None]
        sigmanl2 = self.k[:, None]**2 * (sigmapar**2 * self.mu**2 + sigmaper**2 * (1. - self.mu**2))
        damped_wiggles = (self.template.pk_dd_interpolator(kap) / self.template.pknow_dd_interpolator(kap) - 1.) * np.exp(-sigmanl2 / 2.)
        fog = 1. / (1. + (sigmas * self.k[:, None] * self.mu)**2 / 2.)**2.
        sk = 0.
        if self.mode == 'reciso': sk = np.exp(-1. / 2. * (self.k * self.smoothing_radius)**2)[:, None]
        pkmu = fog * (b1 + f * self.mu**2 * (1 - sk))**2 * pknow * (1. + damped_wiggles)
        self.power = self.to_poles(pkmu)


class ResummedPowerSpectrumWiggles(BaseCalculator):
    r"""
    Resummed BAO wiggles.
    Supports pre-, reciso, recsym, real (f = 0) and redshift-space reconstruction.

    Reference
    ---------
    https://arxiv.org/abs/1907.00043
    """
    def initialize(self, template=None, mode='', smoothing_radius=15.):
        self.mode = str(mode)
        available_modes = ['', 'recsym', 'reciso']
        if self.mode not in available_modes:
            raise ValueError('reconstruction mode {} must be one of {}'.format(self.mode, available_modes))
        self.smoothing_radius = float(smoothing_radius)
        if template is None:
            template = BAOPowerSpectrumTemplate()
        self.template = template
        self.template.runtime_info.initialize()
        if external_cosmo(self.template.cosmo):
            self.cosmo_requires = {'thermodynamics': {'rs_drag': None}}

    def calculate(self):
        k = self.template.pknow_dd_interpolator.k
        pklin = self.template.pknow_dd_interpolator.pk
        q = self.template.cosmo.rs_drag
        j0 = special.jn(0, q * k)
        sk = 0.
        if self.mode: sk = np.exp(-1. / 2. * (k * self.smoothing_radius)**2)
        self.sigma_dd = 1. / (3. * np.pi**2) * integrate.simps((1. - j0) * (1. - sk)**2 * pklin, k)
        #print(k.shape, self.sigma_dd.shape)
        if self.mode:
            self.sigma_ss = 1. / (3. * np.pi**2) * integrate.simps((1. - j0) * sk**2 * pklin, k)
            if self.mode == 'recsym':
                self.sigma_ds = 1. / (3. * np.pi**2) * integrate.simps((1. / 2. * ((1. - sk)**2 + sk**2) + j0 * sk * (1. - sk)) * pklin, k)
            else:
                self.sigma_ds_dd = 1. / (6. * np.pi**2) * integrate.simps((1. - sk)**2 * pklin, k)
                self.sigma_ds_ds = - 1. / (6. * np.pi**2) * integrate.simps(j0 * sk * (1. - sk) * pklin, k)
                self.sigma_ds_ss = 1. / (6. * np.pi**2) * integrate.simps(sk**2 * pklin, k)

    def wiggles(self, k, mu, b1=1., f=0.):
        wiggles = self.template.pk_dd_interpolator(k) - self.template.pknow_dd_interpolator(k)
        b1 = b1 - 1.  # lagrangian b1
        sk = 0.
        if self.mode: sk = np.exp(-1. / 2. * (k * self.smoothing_radius)**2)
        ksq = (1 + f * (f + 2) * mu**2) * k**2
        damping_dd = np.exp(-1. / 2. * ksq * self.sigma_dd)
        resummed_wiggles = damping_dd * ((1 + f * mu**2) * (1 - sk) + b1)**2
        if self.mode == 'recsym':
            damping_ds = np.exp(-1. / 2. * ksq * self.sigma_ds)
            resummed_wiggles -= 2. * damping_ds * ((1 + f * mu**2) * (1 - sk) + b1) * (1 + f * mu**2) * sk
            damping_ss = np.exp(-1. / 2. * ksq * self.sigma_ss)
            resummed_wiggles += damping_ss * (1 + f * mu**2)**2 * sk**2
        if self.mode == 'reciso':
            damping_ds = np.exp(-1. / 2. * (ksq * self.sigma_ds_dd + k**2 * (self.sigma_ds_ss - 2. * (1 + f * mu**2) * self.sigma_ds_dd)))
            resummed_wiggles -= 2. * damping_ds * ((1 + f * mu**2) * (1 - sk) + b1) * sk
            damping_ss = np.exp(-1. / 2. * k**2 * self.sigma_ss)  # f = 0.
            resummed_wiggles += damping_ss * sk**2
        return resummed_wiggles * wiggles


class ResummedBAOWigglesPowerSpectrumMultipoles(BaseBAOWigglesPowerSpectrumMultipoles, BaseTheoryPowerSpectrumMultipolesFromWedges):
    r"""
    Theory BAO power spectrum multipoles, without broadband terms, with resummation of BAO wiggles.
    Supports pre-, reciso, recsym, real (f = 0) and redshift-space reconstruction.

    Reference
    ---------
    https://arxiv.org/abs/1907.00043
    """
    def initialize(self, *args, mu=20, method='leggauss', **kwargs):
        super(ResummedBAOWigglesPowerSpectrumMultipoles, self).initialize(*args, **kwargs)
        self.set_k_mu(k=self.k, mu=mu, method=method, ells=self.ells)
        self.wiggles = ResummedPowerSpectrumWiggles(mode=self.mode, template=self.template,
                                                    smoothing_radius=self.smoothing_radius)

    def calculate(self, b1=1., sigmas=0., **kwargs):
        f = self.template.f
        jac, kap, muap = self.template.ap_k_mu(self.k, self.mu)
        pknow = self.template.pknow_dd_interpolator(kap)
        damped_wiggles = 0. if self.template.only_now else self.wiggles.wiggles(kap, muap, b1=b1, **kwargs) / pknow
        fog = 1. / (1. + (sigmas * kap * muap)**2 / 2.)**2.
        sk = 0.
        if self.mode == 'reciso': sk = np.exp(-1. / 2. * (kap * self.smoothing_radius)**2)
        pkmu = jac * fog * pknow * (damped_wiggles + (b1 + f * muap**2 * (1 - sk))**2)
        self.power = self.to_poles(pkmu)


class BaseBAOWigglesTracerPowerSpectrumMultipoles(BaseTheoryPowerSpectrumMultipoles):
    r"""
    Base class for theory BAO power spectrum multipoles, with broadband terms.

    Parameters
    ----------
    k : array, default=None
        Theory wavenumbers where to evaluate multipoles.

    ells : tuple, default=(0, 2)
        Multipoles to compute.

    mu : int, default=20
        Number of :math:`\mu`-bins to use (in :math:`[0, 1]`).

    mode : str, default=''
        Reconstruction mode:

        - '': no reconstruction
        - 'recsym': recsym reconstruction (both data and randoms are shifted with RSD displacements)
        - 'reciso': reciso reconstruction (data only is shifted with RSD displacements)

    wiggle : bool, default=True
        If ``False``, switch off BAO wiggles: model is computed with smooth power spectrum.

    smoothing_radius : float, default=15
        Smoothing radius used in reconstruction.

    template : BasePowerSpectrumTemplate, default=None
        Power spectrum template. If ``None``, defaults to :class:`BAOPowerSpectrumTemplate`.
    """

    config_fn = 'bao.yaml'

    def initialize(self, k=None, ells=(0, 2), **kwargs):
        super(BaseBAOWigglesTracerPowerSpectrumMultipoles, self).initialize(k=k, ells=ells)
        self.pt = globals()[self.__class__.__name__.replace('Tracer', '')]()
        self.pt.init.update(k=self.k, ells=self.ells, **kwargs)
        self.kp = 0.1  # pivot to normalize broadband terms
        self.set_params()

    def set_params(self):

        def get_params_matrix(base):
            coeffs = {ell: {} for ell in self.ells}
            for param in self.params.select(basename=base + '*_*'):
                name = param.basename
                ell = None
                if name == base + '0':
                    ell, pow = 0, 0
                else:
                    match = re.match(base + '(.*)_(.*)', name)
                    if match:
                        ell, pow = int(match.group(1)), int(match.group(2))
                if ell is not None:
                    if ell in self.ells:
                        coeffs[ell][name] = (self.k / self.kp)**pow
                    else:
                        del self.params[param]
            params = [name for ell in self.ells for name in coeffs[ell]]
            matrix = []
            for ell in self.ells:
                row = [np.zeros_like(self.k) for i in range(len(params))]
                for name, k_i in coeffs[ell].items():
                    row[params.index(name)][:] = k_i
                matrix.append(np.column_stack(row))
            matrix = jnp.array(matrix)
            return params, matrix

        self.broadband_params, self.broadband_matrix = get_params_matrix('al')
        pt_params = self.params.copy()
        for param in pt_params.basenames():
            if param in self.broadband_params: del pt_params[param]
        self.pt.params = pt_params
        self.params = self.params.select(basename=self.broadband_params)

    def calculate(self, **params):
        values = jnp.array([params.get(name, 0.) for name in self.broadband_params])
        self.power = self.pt.power + self.broadband_matrix.dot(values)

    @property
    def template(self):
        return self.pt.template

    def get(self):
        return self.power


class DampedBAOWigglesTracerPowerSpectrumMultipoles(BaseBAOWigglesTracerPowerSpectrumMultipoles):
    r"""
    Theory BAO power spectrum multipoles, with broadband terms, used in the BOSS DR12 BAO analysis by Beutler et al. 2017.
    Supports pre-, reciso, recsym, real (f = 0) and redshift-space reconstruction.

    Parameters
    ----------
    k : array, default=None
        Theory wavenumbers where to evaluate multipoles.

    ells : tuple, default=(0, 2)
        Multipoles to compute.

    mu : int, default=20
        Number of :math:`\mu`-bins to use (in :math:`[0, 1]`).

    mode : str, default=''
        Reconstruction mode:

        - '': no reconstruction
        - 'recsym': recsym reconstruction (both data and randoms are shifted with RSD displacements)
        - 'reciso': reciso reconstruction (data only is shifted with RSD displacements)

    wiggle : bool, default=True
        If ``False``, switch off BAO wiggles: model is computed with smooth power spectrum.

    smoothing_radius : float, default=15
        Smoothing radius used in reconstruction.

    template : BasePowerSpectrumTemplate, default=None
        Power spectrum template. If ``None``, defaults to :class:`BAOPowerSpectrumTemplate`.


    Reference
    ---------
    https://arxiv.org/abs/1607.03149
    """


class SimpleBAOWigglesTracerPowerSpectrumMultipoles(BaseBAOWigglesTracerPowerSpectrumMultipoles):
    r"""
    As :class:`DampedBAOWigglesTracerPowerSpectrumMultipoles`, but moving only BAO wiggles (and not damping or RSD terms)
    with scaling parameters; essentially used for Fisher forecasts.

    Parameters
    ----------
    k : array, default=None
        Theory wavenumbers where to evaluate multipoles.

    ells : tuple, default=(0, 2)
        Multipoles to compute.

    mu : int, default=20
        Number of :math:`\mu`-bins to use (in :math:`[0, 1]`).

    mode : str, default=''
        Reconstruction mode:

        - '': no reconstruction
        - 'recsym': recsym reconstruction (both data and randoms are shifted with RSD displacements)
        - 'reciso': reciso reconstruction (data only is shifted with RSD displacements)

    wiggle : bool, default=True
        If ``False``, switch off BAO wiggles: model is computed with smooth power spectrum.

    smoothing_radius : float, default=15
        Smoothing radius used in reconstruction.

    template : BasePowerSpectrumTemplate, default=None
        Power spectrum template. If ``None``, defaults to :class:`BAOPowerSpectrumTemplate`.

    """


class ResummedBAOWigglesTracerPowerSpectrumMultipoles(BaseBAOWigglesTracerPowerSpectrumMultipoles):
    r"""
    Theory BAO power spectrum multipoles, with broadband terms, with resummation of BAO wiggles.
    Supports pre-, reciso, recsym, real (f = 0) and redshift-space reconstruction.

    Parameters
    ----------
    k : array, default=None
        Theory wavenumbers where to evaluate multipoles.

    ells : tuple, default=(0, 2)
        Multipoles to compute.

    mu : int, default=20
        Number of :math:`\mu`-bins to use (in :math:`[0, 1]`).

    mode : str, default=''
        Reconstruction mode:

        - '': no reconstruction
        - 'recsym': recsym reconstruction (both data and randoms are shifted with RSD displacements)
        - 'reciso': reciso reconstruction (data only is shifted with RSD displacements)

    wiggle : bool, default=True
        If ``False``, switch off BAO wiggles: model is computed with smooth power spectrum.

    smoothing_radius : float, default=15
        Smoothing radius used in reconstruction.

    template : BasePowerSpectrumTemplate, default=None
        Power spectrum template. If ``None``, defaults to :class:`BAOPowerSpectrumTemplate`.


    Reference
    ---------
    https://arxiv.org/abs/1907.00043
    """


class BaseBAOWigglesCorrelationFunctionMultipoles(BaseTheoryCorrelationFunctionFromPowerSpectrumMultipoles):
    """
    Base class that implements theory BAO correlation function multipoles, without broadband terms,
    as Hankel transforms of the theory power spectrum multipoles.
    """
    def initialize(self, s=None, ells=(0, 2), **kwargs):
        power = globals()[self.__class__.__name__.replace('CorrelationFunction', 'PowerSpectrum')](**kwargs)
        super(BaseBAOWigglesCorrelationFunctionMultipoles, self).initialize(s=s, ells=ells, power=power)


class DampedBAOWigglesCorrelationFunctionMultipoles(BaseBAOWigglesCorrelationFunctionMultipoles):

    pass


class SimpleBAOWigglesCorrelationFunctionMultipoles(BaseBAOWigglesCorrelationFunctionMultipoles):

    pass


class ResummedBAOWigglesCorrelationFunctionMultipoles(BaseBAOWigglesCorrelationFunctionMultipoles):

    pass


class BaseBAOWigglesTracerCorrelationFunctionMultipoles(BaseTheoryCorrelationFunctionMultipoles):

    """Base class that implements theory BAO correlation function multipoles, with broadband terms."""
    config_fn = 'bao.yaml'

    def initialize(self, s=None, ells=(0, 2), **kwargs):
        super(BaseBAOWigglesTracerCorrelationFunctionMultipoles, self).initialize(s=s, ells=ells)
        self.pt = globals()[self.__class__.__name__.replace('Tracer', '')]()
        self.pt.init.update(s=self.s, ells=self.ells, **kwargs)
        self.sp = 60.  # pivot to normalize broadband terms
        self.set_params()

    def set_params(self):
        self.k, self.kp = self.s, self.sp
        BaseBAOWigglesTracerPowerSpectrumMultipoles.set_params(self)
        del self.k, self.kp

    def calculate(self, **params):
        values = jnp.array([params.get(name, 0.) for name in self.broadband_params])
        self.corr = self.pt.corr + self.broadband_matrix.dot(values)

    @property
    def wiggle(self):
        return self.pt.wiggle

    @wiggle.setter
    def wiggle(self, wiggle):
        self.pt.wiggle = wiggle

    def get(self):
        return self.corr


class DampedBAOWigglesTracerCorrelationFunctionMultipoles(BaseBAOWigglesTracerCorrelationFunctionMultipoles):
    r"""
    Theory BAO correlation function multipoles, with broadband terms.
    Supports pre-, reciso, recsym, real (f = 0) and redshift-space reconstruction.

    Parameters
    ----------
    s : array, default=None
        Theory separations where to evaluate multipoles.

    ells : tuple, default=(0, 2)
        Multipoles to compute.

    mu : int, default=20
        Number of :math:`\mu`-bins to use (in :math:`[0, 1]`).

    mode : str, default=''
        Reconstruction mode:

        - '': no reconstruction
        - 'recsym': recsym reconstruction (both data and randoms are shifted with RSD displacements)
        - 'reciso': reciso reconstruction (data only is shifted with RSD displacements)

    wiggle : bool, default=True
        If ``False``, switch off BAO wiggles: model is computed with smooth power spectrum.

    smoothing_radius : float, default=15
        Smoothing radius used in reconstruction.

    template : BasePowerSpectrumTemplate, default=None
        Power spectrum template. If ``None``, defaults to :class:`BAOPowerSpectrumTemplate`.


    Reference
    ---------
    https://arxiv.org/abs/1607.03149
    """


class SimpleBAOWigglesTracerCorrelationFunctionMultipoles(BaseBAOWigglesTracerCorrelationFunctionMultipoles):
    r"""
    As :class:`DampedBAOWigglesTracerCorrelationFunctionMultipoles`, but moving only BAO wiggles (and not damping or RSD terms)
    with scaling parameters; essentially used for Fisher forecasts.

    Parameters
    ----------
    s : array, default=None
        Theory separations where to evaluate multipoles.

    ells : tuple, default=(0, 2)
        Multipoles to compute.

    mu : int, default=20
        Number of :math:`\mu`-bins to use (in :math:`[0, 1]`).

    mode : str, default=''
        Reconstruction mode:

        - '': no reconstruction
        - 'recsym': recsym reconstruction (both data and randoms are shifted with RSD displacements)
        - 'reciso': reciso reconstruction (data only is shifted with RSD displacements)

    wiggle : bool, default=True
        If ``False``, switch off BAO wiggles: model is computed with smooth power spectrum.

    smoothing_radius : float, default=15
        Smoothing radius used in reconstruction.

    template : BasePowerSpectrumTemplate, default=None
        Power spectrum template. If ``None``, defaults to :class:`BAOPowerSpectrumTemplate`.


    Reference
    ---------
    https://arxiv.org/abs/1607.03149
    """


class ResummedBAOWigglesTracerCorrelationFunctionMultipoles(BaseBAOWigglesTracerCorrelationFunctionMultipoles):
    r"""
    Theory BAO correlation function multipoles, with broadband terms, with resummation of BAO wiggles.
    Supports pre-, reciso, recsym, real (f = 0) and redshift-space reconstruction.

    Parameters
    ----------
    s : array, default=None
        Theory separations where to evaluate multipoles.

    ells : tuple, default=(0, 2)
        Multipoles to compute.

    mu : int, default=20
        Number of :math:`\mu`-bins to use (in :math:`[0, 1]`).

    mode : str, default=''
        Reconstruction mode:

        - '': no reconstruction
        - 'recsym': recsym reconstruction (both data and randoms are shifted with RSD displacements)
        - 'reciso': reciso reconstruction (data only is shifted with RSD displacements)

    wiggle : bool, default=True
        If ``False``, switch off BAO wiggles: model is computed with smooth power spectrum.

    smoothing_radius : float, default=15
        Smoothing radius used in reconstruction.

    template : BasePowerSpectrumTemplate, default=None
        Power spectrum template. If ``None``, defaults to :class:`BAOPowerSpectrumTemplate`.


    Reference
    ---------
    https://arxiv.org/abs/1907.00043
    """

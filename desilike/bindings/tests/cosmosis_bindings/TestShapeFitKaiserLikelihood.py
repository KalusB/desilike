# NOTE: This code has been automatically generated by desilike.bindings.cosmosis.factory.CosmoSISLikelihoodGenerator
from desilike.bindings.cosmosis.factory import CosmoSISLikelihoodFactory

from desilike.bindings.tests.test_generator import TestShapeFitKaiserLikelihood
TestShapeFitKaiserLikelihood = CosmoSISLikelihoodFactory(TestShapeFitKaiserLikelihood, 'TestShapeFitKaiserLikelihood', kw_like={}, module=__name__)

setup, execute, cleanup = TestShapeFitKaiserLikelihood.build_module()


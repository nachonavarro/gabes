"""
Tests for `gabes` module.
"""

import pytest
import gabes.settings as settings

from concurrent.futures import ThreadPoolExecutor as Executor
from collections import namedtuple
from gabes.garbler import garbler
from gabes.evaluator import evaluator


@pytest.fixture
def args(request):
    truth, optims = request.param
    flags = 'address, circuit, identifiers, bits'
    Args = namedtuple('Args', flags)
    g_args = {
        'address': 'localhost:5000',
        'circuit': 'circuits/simple-2.circuit',
        'identifiers': ['A', 'B', 'C'],
        'bits': '111'
    }
    e_args = {
        'address': 'localhost:5000',
        'circuit': 'circuits/simple-2.circuit',
        'identifiers': ['D', 'E', 'F'],
        'bits': '001' if truth else '000'
    }
    settings.CLASSICAL = 'classical' in optims
    settings.POINT_AND_PERMUTE = 'point_and_permute' in optims
    settings.GRR3 = 'grr3' in optims
    settings.FREE_XOR = 'free_xor' in optims
    settings.FLEXOR = 'flexor' in optims
    settings.HALF_GATES = 'half_gates' in optims
    garbler_args = Args(**g_args)
    evaluator_args = Args(**e_args)
    return garbler_args, evaluator_args, truth


def run_garbler_and_evaluator_with(args):
    garbler_args, evaluator_args, truth = args
    with Executor() as executor:
        future1 = executor.submit(garbler, garbler_args)
        future2 = executor.submit(evaluator, evaluator_args)
        out1, out2 = future1.result(), future2.result()
        assert out1 is truth
        assert out2 is truth


@pytest.mark.parametrize('args', [(False, 'classical')], indirect=True)
def test_false_classical(args):
    run_garbler_and_evaluator_with(args)


@pytest.mark.parametrize('args', [(True, 'classical')], indirect=True)
def test_true_classical(args):
    run_garbler_and_evaluator_with(args)


@pytest.mark.parametrize('args', [(False, 'point_and_permute')], indirect=True)
def test_false_point_and_permute(args):
    run_garbler_and_evaluator_with(args)


@pytest.mark.parametrize('args', [(True, 'point_and_permute')], indirect=True)
def test_true_point_and_permute(args):
    run_garbler_and_evaluator_with(args)


@pytest.mark.parametrize('args', [(False, 'grr3')], indirect=True)
def test_false_grr3(args):
    run_garbler_and_evaluator_with(args)


@pytest.mark.parametrize('args', [(True, 'grr3')], indirect=True)
def test_true_grr3(args):
    run_garbler_and_evaluator_with(args)


@pytest.mark.parametrize('args', [(False, 'free_xor')], indirect=True)
def test_false_free_xor(args):
    run_garbler_and_evaluator_with(args)


@pytest.mark.parametrize('args', [(True, 'free_xor')], indirect=True)
def test_true_free_xor(args):
    run_garbler_and_evaluator_with(args)


@pytest.mark.parametrize('args', [(False, 'flexor')], indirect=True)
def test_false_flexor(args):
    run_garbler_and_evaluator_with(args)


@pytest.mark.parametrize('args', [(True, 'flexor')], indirect=True)
def test_true_flexor(args):
    run_garbler_and_evaluator_with(args)

@pytest.mark.parametrize('args', [(False, 'half_gates')], indirect=True)
def test_false_half(args):
    run_garbler_and_evaluator_with(args)


@pytest.mark.parametrize('args', [(True, 'half_gates')], indirect=True)
def test_true_half(args):
    run_garbler_and_evaluator_with(args)
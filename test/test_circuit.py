"""
Tests for `gabes` module.
"""
import pytest
import os

from gabes.circuit import Circuit
from anytree import LevelOrderIter


@pytest.fixture
def circuit():
    '''Returns a :class:`Circuit` object instance for simple-2.circuit file'''
    parent = os.getcwd()
    path = os.path.join(parent, 'circuits/simple-2.circuit')
    return Circuit(path)


def test_input_wires(circuit):
    input_wires = circuit.get_input_wires()
    for input_wire in input_wires:
        assert input_wire.identifier in ['A', 'B', 'C', 'D', 'E', 'F']


def test_separate(circuit):
    example = '(A AND B) AND (C AND D)'
    left, gate, right = circuit._separate(example)
    assert left == 'A AND B'
    assert gate == 'AND'
    assert right == 'C AND D'


def test_build_tree(circuit):
    gates_expected_order = ['AND', 'AND', 'XOR', 'AND', 'XOR']
    gates_actual_order = [node.name.gate_type for
                          node in LevelOrderIter(circuit.tree)]
    assert gates_actual_order == gates_expected_order

"""
This module implements the :class:`Circuit` object which is in charge of
maintaining the tree hierarchy for the circuit. This includes handling all
the gates in the circuit as well as keeping track of global parameters (for
instance R in FreeXOR). It also parses the .circuit file into the tree via the
function :meth:`gabes.circuit.build_tree`.

At the moment, the structure of the .circuit file must be like the one
shown in examples; that is, each child gate of a gate (except the root)
must be surrounded by parenthesis.

"""

import copy
import os
import gabes.settings as settings
import anytree

from gabes.gate import Gate
from gabes.utils import get_last_bit


class Circuit(object):
    """
        The :class:`Circuit` object holds all the gates and wires
        composing the circuit. Internally, it is represented as a binary
        tree. It also sets `R` for FreeXOR or Half Gates if necessary.

        :param str file: path of the file describing the circuit
    """

    def __init__(self, file):
        if settings.FREE_XOR or settings.HALF_GATES:
            while True:
                settings.R = os.urandom(settings.NUM_BYTES)
                if get_last_bit(settings.R):
                    break
        self.tree = self.build_tree(file)
        self.input_wires = None

    def build_tree(self, file):
        """
            Builds the tree recursively by parsing and breaking up
            the circuit file into smaller expressions until the expression
            left is the wire's identifier. On each gate it visits
            the function also garbles it in preparation for the
            evaluator.

            :param str file: path of the file describing the circuit
            :return: the root node as used in the package `anytree`
            :rtype: :class:`anytree.Node`
        """
        with open(file, 'r') as f:
            expression = f.read().strip()
            root = self._build_tree(None, expression)
        return root

    def _build_tree(self, parent, expression):
        """
            Helper function to build the tree.

            :param Node parent: parent of the current node
            :return: the root node as used in the package `anytree`
            :rtype: :class:`anytree.Node`

        """
        left, gate_type, right = self._separate(expression)
        node = self._build_gate(parent, left, gate_type, right)
        gate = node.name

        if len(left.split()) == 1:
            gate.left_wire.identifier = left
        else:
            self._build_tree(node, left)
        if len(right.split()) == 1:
            gate.right_wire.identifier = right
        else:
            self._build_tree(node, right)

        gate.garble()

        if not parent:
            return node

    def _build_gate(self, parent, left, gate_type, right):
        """
            Ensures the parent's left wire is the left children's output wire
            and the parent's right wire is the right children's output wire.

            :param Node parent: parent of the current node
            :param str left: left expression to parse
            :param str gate_type: type of gate (AND, XOR...)
            :param str right: righr expression to parse
            :return: the node as used in the package `anytree`
            that holds the :class:`Gate`.
            :rtype: :class:`anytree.Node`
        """
        is_left_leaf = len(left.split()) == 1
        is_right_leaf = len(right.split()) == 1
        gate = Gate(gate_type, create_left=is_left_leaf,
                    create_right=is_right_leaf)
        if parent:
            node = anytree.Node(gate, parent=parent)
        else:
            node = anytree.Node(gate)
        if parent:
            if parent.children[0] == node:
                parent.name.left_wire = gate.output_wire
            elif parent.children[1] == node:
                parent.name.right_wire = gate.output_wire
        return node

    def _separate(self, expression):
        """
            Separates an expression according to parenthesis.

            :param str expression: the expression to parse and separate
            :return: the expression split into three parts: a left expression,
            a right expression, and a gate type.
            :rtype: tuple(str)
        """
        if '(' not in expression:
            return expression.split()
        balance = 0
        for i, char in enumerate(expression):
            if char == '(':
                balance += 1
            elif char == ')':
                balance -= 1
            if balance == 0:
                break
        left, rest = expression[1:i], expression[i + 1: -1]
        gate, right = rest.split('(', 1)
        return left, gate.strip(), right

    def reconstruct(self, labels):
        """
            Function used by the evaluator to reconstruct the circuit given
            only the input labels by the garbler. The reconstruction needs
            to be done in a bottom-up approach since the output labels of
            input gates will serve as input labels for parent gates.
            The function traverses the tree by level starting at the leaves.
            If the nodes are leaves, then the labels will be provided through
            the network by the garbler. For all other nodes, the evaluator will
            have the necessary labels as part of the node's children by a
            process of ungarbling (see :meth:`gabes.gate.Gate.ungarble`).

            :param labels: the list of input labels supplied by the garbler
            :type labels: list(:class:`Label`)
            :return: the final output label at the end of the circuit
            :rtype: :class:`Label`

        """
        levels = [[node for node in children]
                  for children in anytree.LevelOrderGroupIter(self.tree)][::-1]
        for level in levels:
            for node in level:
                gate = node.name
                if node.is_leaf:
                    garblers_label = labels.pop(0)
                    evaluators_label = labels.pop(0)
                else:
                    left_gate = node.children[0].name
                    right_gate = node.children[1].name
                    garblers_label = left_gate.chosen_label
                    evaluators_label = right_gate.chosen_label
                output_label = gate.ungarble(garblers_label, evaluators_label)
                gate.chosen_label = output_label
        return self.tree.name.chosen_label

    def clean(self):
        """
            Cleans the circuit from any private labels in preparation
            for the evaluator. Before cleaning, it creates a copy of itself
            so that the garbler still has a reference of the mapping between
            labels and truth values.
        """
        circ = copy.deepcopy(self)
        for node in anytree.PreOrderIter(circ.tree):
            gate = node.name
            gate.left_wire = gate.right_wire = gate.output_wire = None
        return circ

    def draw_circuit(self):
        """
            Draws the tree structure of the circuit.

            .. code-block:: python

               >>> from gabes.circuit import Circuit
               >>> c = Circuit('gabes/circuits/simple-2.circuit')
               >>> c.draw_circuit()
               AND
               ├── AND
               │   ├── AND
               │   └── XOR
               └── XOR
        """
        for pre, fill, node in anytree.RenderTree(self.tree):
            print("{}{}".format(pre, node.name))

    def get_input_wires(self):
        if not self.input_wires:
            leaves = [node.name for node
                      in anytree.PostOrderIter(self.tree) if node.is_leaf]
            input_wires = [wire for leaf in leaves
                           for wire in [leaf.left_wire, leaf.right_wire]]
            self.input_wires = input_wires
        return self.input_wires

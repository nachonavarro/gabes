"""

gabes.circuit
~~~~~~~~~~~~~~~~~~~

This module implements the :class:`Circuit` object which is in charge of maintaining
the tree hierarchy for the circuit. This includes handling all the gates in the
circuit as well as keeping track of global parameters (for instance R in FreeXOR).
It also parses the .circuit file into the tree via the :method:build_tree.

"""

import copy
import os
import gabes.settings as settings

from anytree import Node, RenderTree, PostOrderIter, LevelOrderGroupIter, PreOrderIter
from itertools import takewhile, dropwhile
from gabes.gate import Gate
from gabes.wire import Wire
from gabes.utils import get_last_bit

class Circuit(object):
	"""The :class:`Circuit` object holds all the gates and wires
	composing the circuit. Internally, it is represented as a binary
	tree.
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
		with open(file, 'r') as f:
			expression = f.read().strip()
			root = self._build_tree(None, expression)
		return root

	def _build_tree(self, parent, expression):
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
		""" Ensure the parent's left wire is the left children's output wire
		and the parent's right wire is the right children's output wire."""
		is_left_leaf = len(left.split()) == 1
		is_right_leaf = len(right.split()) == 1
		gate = Gate(gate_type, create_left_wire=is_left_leaf, create_right_wire=is_right_leaf)
		node = Node(gate, parent=parent) if parent else Node(gate)
		if parent:
			if parent.children[0] == node:
				parent.name.left_wire = gate.output_wire
			elif parent.children[1] == node:
				parent.name.right_wire = gate.output_wire
		return node

	def _separate(self, expression):
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
		left, rest  = expression[1:i], expression[i + 1: -1]
		gate, right = rest.split('(', 1)
		return left, gate.strip(), right

	def reconstruct(self, labels):
		levels = [[node for node in children] for children in LevelOrderGroupIter(self.tree)][::-1]
		for level in levels:
			for node in level:
				gate = node.name
				if node.is_leaf:
					garblers_label, evaluators_label = labels.pop(0), labels.pop(0)
				else:
					left_gate  = node.children[0].name
					right_gate = node.children[1].name
					garblers_label, evaluators_label = left_gate.chosen_label, right_gate.chosen_label
				output_label = gate.ungarble(garblers_label, evaluators_label)
				gate.chosen_label = output_label
		return self.tree.name.chosen_label

	def clean(self):
		""" Cleans the circuit from any private labels in preparation for Bob. """
		circ = copy.deepcopy(self)
		for node in PreOrderIter(circ.tree):
			gate = node.name
			gate.left_wire = gate.right_wire = gate.output_wire = None
		return circ

	def draw_circuit(self):
		for pre, fill, node in RenderTree(self.tree):
			print("{}{}".format(pre, node.name))

	def get_input_wires(self):
		if not self.input_wires:
			leaves = [node.name for node in PostOrderIter(self.tree) if node.is_leaf]
			input_wires = [wire for leaf in leaves for wire in [leaf.left_wire, leaf.right_wire]]
			self.input_wires = input_wires
		return self.input_wires



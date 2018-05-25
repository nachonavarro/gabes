import re
from anytree import Node, RenderTree, PostOrderIter
from itertools import takewhile, dropwhile
from gate import Gate

class Circuit(object):
	"""The :class:`Circuit` object holds all the gates and wires
	composing the circuit. Internally, it is represented as a binary
	tree.
	"""

	def __init__(self, file):
		self.tree = self.build_tree(file)

	def build_tree(self, file):
		with open(file, 'r') as f:
			expression = f.read().strip()
			root = self._build_tree(None, expression)
		return root

	def _build_tree(self, parent, expression):
		left, gate_type, right = self._separate(expression)
		gate = Gate(gate_type)
		node = Node(gate, parent=parent) if parent else Node(gate)

		if len(left.split()) == 1:
			Node(left, parent=node)
		else:
			self._build_tree(node, left)
		if len(right.split()) == 1:
			Node(right, parent=node)
		else:
			self._build_tree(node, right)

		if not parent:
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
		gate, right = rest.split('(')
		return left, gate.strip(), right

	def draw_circuit(self):
		for pre, fill, node in RenderTree(self.tree):
			print("%s%s" % (pre, node.name))

	def get_input_labels(self):
		return [node.name for node in PostOrderIter(self.tree) if node.is_leaf]



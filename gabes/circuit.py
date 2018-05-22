import re
from anytree import Node, RenderTree
from itertools import takewhile, dropwhile

def to_circuit(file):
	t = build_tree(file)

def build_tree(file):
	with open(file, 'r') as f:
		expression = f.read().strip()
		root = _build_tree(None, expression)
	return root

def _build_tree(parent, expression):
	left, gate, right = _separate(expression)
	node = Node(gate, parent=parent) if parent else Node(gate)

	if len(left.split()) == 1:
		Node(left, parent=node)
	else:
		_build_tree(node, left)
	if len(right.split()) == 1:
		Node(right, parent=node)
	else:
		_build_tree(node, right)

	if not parent:
		return node

def _separate(expression):
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

def draw_circuit(tree):
	for pre, fill, node in RenderTree(tree):
		print("%s%s" % (pre, node.name))



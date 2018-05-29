import argparse
import settings
from garbler import garbler
from evaluator import evaluator

def main(args):
	if args.garbler:
		garbler(args)
	elif args.evaluator:
		evaluator(args)

def sanitize_inputs(parser):
	args = parser.parse_args()
	if not args.garbler and not args.evaluator:
		parser.error('Either -g or -e needs to be set.')
	if args.garbler and args.evaluator:
		parser.error('Can not be both garbler and evaluator!')
	if args.garbler and not args.circuit:
		parser.error('The garbler needs to supply the circuit file.')
	main(args)
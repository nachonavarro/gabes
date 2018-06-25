========================================
Gabes: Garbled Circuits in Python
========================================

.. image:: https://travis-ci.org/nachonavarro/gabes.svg?branch=master
    :target: https://travis-ci.org/nachonavarro/gabes

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT

Introduction
-----------------------------

Garbled Circuits allow two distrusting parties
to compute a joint function while keeping their inputs private. More precisely,
it allows Alice with input `x` and Bob with input `y` to compute a function
`f(x, y)` without Alice ever knowing `y` and without Bob knowing `x`. The way
it does so is by first translating `f` to a boolean circuit from which it will
cleverly obfuscate or **garble** the circuit to allow the computation of `f`
while keeping the inputs private.

The classical example is that of two millionaires who wish to find out who is
richer without revealing their wealth. In that case, `f` becomes the ">" (greater
than) function, and `x` and `y` are their wealth. 

**Gabes** implements garbled circuits in Python. The application runs as a command
line interface but the functions required to run garbled circuits can be used without
the command line (see gabes).

Installation
------------------

At the command line either via pip::

    $ pip install gabes

Or, if you have virtualenvwrapper installed::

    $ mkvirtualenv gabes
    $ pip install gabes

Usage
--------

Each party will run their own instance of the program on their computer as a CLI app. 
The garbler will provide the IP and port number to establish the connection with the
evaluator.

.. note:: Make sure to open the port when connecting between two different networks.

**Garbler's Side**::

   gabes -g -grr3 -c Desktop/my-circuit.circuit -a localhost:5000

**Evaluator's Side**::

   gabes -e -grr3 -a localhost:5000

Flags
----------

.. code-block::

	usage: gabes [-h] [-g] [-e] [-b bits] [-i identifier [identifier ...]]
	                   [-c file] -a ip:port [-cl] [-pp] [-grr3] [-free] [-grr2]
	                   [-fle] [-half]

	Program to garble and evaluate a circuit.

	optional arguments:
	  -h, --help            show this help message and exit
	  -g, --garbler         Set this flag to become the garbler
	  -e, --evaluator       Set this flag to become the evaluator
	  -b bits, --bits bits  Include your private input bitstring to the circuit
	                        (e.g. 001011)
	  -i identifier [identifier ...], --identifiers identifier [identifier ...]
	                        Indicate which input wires you supply to the circuit
	                        (e.g. -i A C D)
	  -c file, --circuit file
	                        Path of the file representing the circuit. Only the
	                        garbler needs to supply the file
	  -a ip:port, --address ip:port
	                        IP address followed by the port number
	  -cl, --classical      Set this flag for classical garbled circuits
	  -pp, --point-and-permute
	                        Set this flag to include point-and-permute
	  -grr3, --grr3         Set this flag for GRR3 garbled circuits
	  -free, --free-xor     Set this flag for free-xor garbled circuits
	  -fle, --flexor        Set this flag for flexor garbled circuits
	  -half, --half-gates   Set this flag for half gates garbled circuits

Documentation
------------------

All the documentation can be found in https://gabes.readthedocs.io/en/latest/




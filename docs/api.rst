.. _api:

API
=======

.. module:: gabes

This part of the documentation explains each function or class in detail to better
understand the internal details behind garbled circuits.


Circuit
--------------
.. automodule:: gabes.circuit
.. autoclass:: gabes.circuit.Circuit
   :inherited-members:

Gate
--------------

.. automodule:: gabes.gate
.. autoclass:: gabes.gate.Gate
   :inherited-members:

(*The*) Wire
--------------

.. note:: 
	*"The king stay the king"*
	
	- D'Angelo Barksdale

.. automodule:: gabes.wire
.. autoclass:: gabes.wire.Wire
   :inherited-members:

Label
--------------

.. automodule:: gabes.label
.. autoclass:: gabes.label.Label
   :inherited-members:

Garbler
--------------

.. automodule:: gabes.garbler
.. autofunction:: gabes.garbler.garbler
.. autofunction:: gabes.garbler.hand_over_wire_identifiers
.. autofunction:: gabes.garbler.hand_over_cleaned_circuit
.. autofunction:: gabes.garbler.hand_over_labels
.. autofunction:: gabes.garbler.learn_output

Evaluator
--------------

.. automodule:: gabes.evaluator
.. autofunction:: gabes.evaluator.evaluator
.. autofunction:: gabes.evaluator.request_cleaned_circuit
.. autofunction:: gabes.evaluator.request_wire_identifiers
.. autofunction:: gabes.evaluator.request_labels
.. autofunction:: gabes.evaluator.learn_output

Cryptography
--------------

.. automodule:: gabes.crypto
.. autoclass:: gabes.crypto.AESKey
   :inherited-members:
.. autofunction:: gabes.crypto.generate_zero_ciphertext

Network
-------------

.. automodule:: gabes.network
.. autofunction:: gabes.network.connect_garbler
.. autofunction:: gabes.network.connect_evaluator
.. autofunction:: gabes.network.send_data
.. autofunction:: gabes.network.receive_data
.. autofunction:: gabes.network.send_ack
.. autofunction:: gabes.network.wait_for_ack


Oblivious Transfer
---------------------

.. automodule:: gabes.ot
.. autofunction:: gabes.ot.garbler_ot
.. autofunction:: gabes.ot.evaluator_ot

Utils
---------------------

.. automodule:: gabes.utils
.. autofunction:: gabes.utils.ask_for_inputs
.. autofunction:: gabes.utils.get_last_bit
.. autofunction:: gabes.utils.xor
.. autofunction:: gabes.utils.adjust_wire_offset

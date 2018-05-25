from circuit import Circuit

def ask_for_inputs(circuit_file):
	choice = input("Press 1 to input your private inputs for the circuit \none by one or press 2 to input them all at once: ")
	circuit = Circuit(circuit_file)
	if choice == '1':
		inputs = []
		for label in circuit.get_input_labels():
			inputs.append(input("Choice for input {}: ".format(label)))
	elif choice == '2':
		inputs = list(input("Type in inputs as a bitstring (e.g. 0101101): "))
	return inputs
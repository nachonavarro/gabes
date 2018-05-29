def ask_for_inputs(identifiers):

	print("To start the protocol please indicate with y/n which wires you supply:")
	chosen_wires = []
	for identifier in identifiers:
		decision = input("Do you supply {}? ".format(identifier))
		while True:
			if decision == 'y':
				chosen_wires.append(identifier)
				break
			elif decision == 'n':
				break
			else:
				decision = input("Sorry, didn't recognize that. Indicate with y or n whether you supply {}: ".format(identifier))

	inputs = {}
	for identifier in chosen_wires:
		label_choice = input("Choice for {}: ".format(identifier))
		while True:
			if label_choice in '01':
				break
			else:
				label_choice = input("Sorry, you must supply either a 0 (indicating false) or a 1 (indicating true) for wire {}: ".format(identifier))

		inputs[identifier] = label_choice

	return inputs
def garbler_ot(m0, m1):
	private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
	d = private_key.private_numbers().d

	public_key = private_key.public_key()
	n, e = public_key.public_numbers().n, public_key.public_numbers().e
	
	x0, x1 = [randint(2, n) for _ in range(2)]
	send_data_to_evaluator(x0, x1, n, e)
	v = receive_data_from_evaluator()
	k0, k1 = [(v - x) ** d % n for x in (x0, x1)]
	send_data_to_evaluator(m0 + k0, m1 + k1)

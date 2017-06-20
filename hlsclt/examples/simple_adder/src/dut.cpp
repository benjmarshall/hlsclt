int simple_adder(int a, int b) {
	#pragma HLS PIPELINE
	int c;
	c = a + b;
	return c;
}

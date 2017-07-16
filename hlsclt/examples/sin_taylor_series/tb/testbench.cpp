#include <fstream>
#include <math.h>
#include "../src/dut.h"

int main(void) {

	// Setup some required variables
	const double pi = 3.1415;
	const double rad2deg = 180/pi;
	const double deg2rad = pi/180;
	double x = 0.0;
	double result, expected_result;
	int error_count = 0;

	// Test Loop
	while (x < 90*deg2rad) {
		// Call dut
		result = sin_taylor_series(x);
		// Generate expected_result
		expected_result = sin(x);
		// Check result and output some visual check
		if (fabs(result - expected_result) > expected_result*0.001) {
			error_count++;
		}
		printf("Sin(%d) - Expected result: %f, Got Result: %f\n", int(round(x*rad2deg)), expected_result, result);
		x = x + (5*deg2rad);
	}

	return error_count;

}

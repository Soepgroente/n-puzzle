#include "tests.hpp"

int main()
{
	int	results = 0;

	results += runParsingTests();
	results += runSolutionTests();

	std::cout << "Total errors: " << results << "\n";
	return results;
}
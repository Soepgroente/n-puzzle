#include "tests.hpp"

int	runParsingTests()
{
	PuzzleData	data;

	data.configFromFile("../puzzles/puzzle1.txt");
	Board		board(std::vector<ui32>
	{
		1, 2, 3,
		8, 6, 4,
		7, 0, 5
	});


}
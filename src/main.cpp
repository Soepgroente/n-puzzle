#include "n-puzzle.hpp"
#include "Board.hpp"

#include <fstream>
#include <iostream>
#include <sstream>

int main(int argc, char** argv)
{
	if (argc == 2)
	{
		try
		{
			Board	startingPosition(argv[1]);
			
			// solve(startingPosition);
		}
		catch (const std::exception& e)
		{
			std::cerr << "Error: " << e.what() << std::endl;
			return 1;
		}
		return 0;
	}
	if (argc > 2)
	{
		std::cerr << "Use the GUI or use: " << argv[0] << " [puzzle_file]" << std::endl;
		return 1;
	}
	std::string line;
	std::vector<int>	puzzleConfig;
	
	while (std::getline(std::cin, line))
	{
		std::stringstream	ss(line);

		int	value;
		while (ss.eof() == false)
		{
			ss >> value;
			puzzleConfig.push_back(value);
		}
	}
	
	// Echo back a valid JSON response to stdout
	std::cout << "{\"moves\": [1, 2, 3, 4]}" << std::endl;
	
	return 0;
}
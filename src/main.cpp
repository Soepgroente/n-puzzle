#include "n-puzzle.hpp"
#include "Board.hpp"

#include <fstream>

int main(int argc, char** argv)
{
    std::ofstream testFile("test.txt");
    
    // Write command line args (if any)
    testFile << "=== Command Line Arguments ===" << std::endl;
    for (int i = 0; i < argc; ++i)
    {
        testFile << "argv[" << i << "]: " << argv[i] << std::endl;
    }
    
    // Read from stdin (this is where Python sends the JSON)
    testFile << "\n=== Standard Input (stdin) ===" << std::endl;
    std::string line;
    while (std::getline(std::cin, line))
    {
        testFile << line << std::endl;
    }
    
    testFile.close();
    
    // Echo back a valid JSON response to stdout
    std::cout << "{\"moves\": [1, 2, 3, 4]}" << std::endl;
    
    return 0;
}
	// if (argc != 2)
	// {
	// 	std::cerr << "Usage: " << argv[0] << " <input_file>" << std::endl;
	// 	return 1;
	// }
	// try
	// {
	// 	Board	board(argv[1]);

	// 	board.solve();
	// }
	// catch(const std::exception& e)
	// {
	// 	std::cerr << "Error: " << e.what() << std::endl;
	// 	return 1;
	// }
	// return 0;
#include "n-puzzle.hpp"
#include "Board.hpp"
#include <array>

enum Direction
{
	NONE = 0,
	UP = 1,
	DOWN = 2,
	LEFT = 3,
	RIGHT = 4
};

bool	Board::isSolved() const noexcept
{
	for (int i = 0; i < size - 1; i++)
	{
		if (tiles[i] != i + 1)
		{
			return false;
		}
	}
	return tiles.back() == 0;
}

void	Board::calculateMoveOrder(std::array<int, 4>& order) const noexcept
{
	if (hole + UP * n >= 0)
	{
		order[0] = UP;
	}
	if (hole + DOWN * n < size)
	{
		order[1] = DOWN;
	}
	if (hole % n != 0)
	{
		order[2] = LEFT;
	}
	if ((hole + 1) % n != 0)
	{
		order[3] = RIGHT;
	}
}

bool	Board::recursiveSolve(Board& board)
{
	std::array<int, 4> order{NONE, NONE, NONE, NONE};
	
	calculateMoveOrder(order);
}

void	Board::solve()
{
	Board copy = *this;

	path.reserve(1024);
	bool result = recursiveSolve(copy);

	if (result == false)
	{
		std::cout << "No solution found." << std::endl;
		return;
	}
	std::cout << copy << std::endl;
}
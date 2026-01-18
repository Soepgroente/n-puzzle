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

bool	Board::isSolved(const std::vector<int>& tiles) noexcept
{
	return tiles == Board::solution;
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
	(void)board; // To suppress unused variable warning for now
	return true;
}

void	solve(const Board& initialBoard)
{
	std::vector<Board>	boards;

	boards.reserve(initialBoard.getSize() * 10);
	boards.push_back(initialBoard);
}
#include "PuzzleData.hpp"

#include <iostream>
#include <iomanip>

enum Direction
{
	NONE = 0,
	UP = 1,
	DOWN = 2,
	LEFT = 3,
	RIGHT = 4
};

int	PuzzleData::findSensibleMoves(Board& board) noexcept
{
	int	legalmoves = 0;

	if (previousMove != DOWN && board.emptyTile - n >= 0)
	{
		board.up();
		if (closedBoards.count(board) == 0)
		{
			legalmoves |= (1 << UP);
		}
		board.down();
	}
	if (previousMove != UP && board.emptyTile + n < size)
	{
		board.down();
		if (closedBoards.count(board) == 0)
		{
			legalmoves |= (1 << DOWN);
		}
		board.up();
	}
	if (previousMove != RIGHT && board.emptyTile % n != 0)
	{
		board.left();
		if (closedBoards.count(board) == 0)
		{
			legalmoves |= (1 << LEFT);
		}
		board.right();
	}
	if (previousMove != LEFT && board.emptyTile % n != n - 1)
	{
		board.right();
		if (closedBoards.count(board) == 0)
		{
			legalmoves |= (1 << RIGHT);
		}
		board.left();
	}
	return legalmoves;
}

void	PuzzleData::loopPathBackwards()
{
	Board	currentBoard = solution;

	while (cameFrom.find(currentBoard) != cameFrom.end())
	{
		Board	parentBoard = cameFrom[currentBoard];
		ui32	move = 0;

		if (currentBoard.emptyTile == parentBoard.emptyTile - static_cast<int>(n))
		{
			move = UP;
		}
		else if (currentBoard.emptyTile == parentBoard.emptyTile + static_cast<int>(n))
		{
			move = DOWN;
		}
		else if (currentBoard.emptyTile == parentBoard.emptyTile - 1)
		{
			move = LEFT;
		}
		else if (currentBoard.emptyTile == parentBoard.emptyTile + 1)
		{
			move = RIGHT;
		}
		path.push_back(move);
		currentBoard = parentBoard;
	}
	std::reverse(path.begin(), path.end());
	endTime = std::chrono::high_resolution_clock::now();
}

void	PuzzleData::solve() noexcept
{
	int moves;

	startTime = std::chrono::high_resolution_clock::now();
	while (openBoards.empty() == false)
	{
		Board currentBoard = openBoards.top();

		openBoards.pop();
		if (currentBoard == solution)
		{
			loopPathBackwards();
			break;
		}
		moves = findSensibleMoves(currentBoard);
		if (moves == 0)
		{
			closedBoards.insert(currentBoard);
			continue;
		}
		for (int direction = UP; direction <= RIGHT; direction++)
		{
			if ((moves & (1 << direction)) == 0)
			{
				continue;
			}
			Board newBoard = currentBoard;

			switch (direction)
			{
				case UP: newBoard.up();  break;
				case DOWN: newBoard.down(); break;
				case LEFT: newBoard.left(); break;
				case RIGHT: newBoard.right(); break;
				default: break;
			}
			newBoard.distanceTraveled++;
			newBoard.heuristicValue = calculateHeuristicValue(newBoard);
			newBoard.totalScore = newBoard.distanceTraveled + newBoard.heuristicValue;
			cameFrom[newBoard] = currentBoard;
			openBoards.push(newBoard);
			largestOpenBoardSize = std::max(largestOpenBoardSize, openBoards.size());
		}
		closedBoards.insert(currentBoard);
	}
}

void	PuzzleData::printSolution(std::ostream& os)	const noexcept
{
	size_t	size = path.size();
	size_t	boardStates = closedBoards.size() + openBoards.size();

	if (size == 0)
	{
		os << "Something went wrong or puzzle was already solved!" << std::endl;
		return ;
	}
	os << "{\"moves\": [";
	for (size_t i = 0; i < size - 1; i++)
	{
		os << path[i] << ", ";
	}
	if (size > 0)
	{
		os << path[size - 1];
	}
	os << "],\n";
	os << "\"time_ms\": " << std::chrono::duration_cast<std::chrono::milliseconds>(endTime - startTime).count() << ",\n";
	os << "\"total_searched\": " << boardStates << ",\n";
	os << "\"peak_memory_states\": " << boardStates << ",\n";
	os << "\"peak_memory_bytes\": " << boardStates * sizeof(Board) << "\n}" << std::endl;
}
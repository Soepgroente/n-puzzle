#pragma once

#include <array>
#include <vector>
#include <iostream>

typedef uint32_t ui32;
typedef uint64_t ui64;

struct Board
{
	public:

	Board() = default;
	~Board() = default;
	Board(const Board &other);
	Board(const std::vector<ui32>& initialTiles);
	Board& operator=(const Board &other);

	ui32	operator[](ui32 index) const { return tiles[index]; }
	bool	operator==(const Board& other) const { return tiles == other.tiles; }
	bool	operator!=(const Board& other) const { return tiles != other.tiles; }
	bool	operator<(const Board& other) const { return totalScore < other.totalScore; }
	bool	operator>(const Board& other) const { return totalScore > other.totalScore; }
	bool	operator<=(const Board& other) const { return totalScore <= other.totalScore; }
	bool	operator>=(const Board& other) const { return totalScore >= other.totalScore; }

	void	up()	noexcept;
	void	down()	noexcept;
	void	left()	noexcept;
	void	right()	noexcept;

	std::vector<ui32>	tiles;

	ui32	emptyTile;
	ui32	distanceTraveled;
	ui32	heuristicValue;
	ui32	totalScore;
};

std::ostream& operator<<(std::ostream& os, const Board& board);

namespace std
{
template<>
struct hash<Board>
{
	std::size_t operator()(const Board& board) const
	{
		size_t h = 0;
		size_t multiplier = 1;
		size_t boardSize = board.tiles.size();

		for (size_t i = 0; i < boardSize; i++)
		{
			h += board[i] * multiplier;
			multiplier *= 17;
		}
		return h;
	}
};
}	// namespace std
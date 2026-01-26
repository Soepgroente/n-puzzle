#include "Board.hpp"
#include "PuzzleData.hpp"

#include <iostream>
#include <fstream>
#include <sstream>
#include <stdexcept>

Board::Board(const std::vector<ui32>& initialTiles) : tiles(initialTiles), distanceTraveled(0), heuristicValue(UINT32_MAX), totalScore(UINT32_MAX)
{
	for (size_t i = 0; i < tiles.size(); i++)
	{
		if (tiles[i] == 0)
		{
			emptyTile = i;
			break;
		}
	}
}

Board::Board(const Board& other)
{
	*this = other;
}

Board& Board::operator=(const Board &other)
{
	if (this != &other)
	{
		this->tiles = other.tiles;
		this->emptyTile = other.emptyTile;
		this->distanceTraveled = other.distanceTraveled;
		this->heuristicValue = other.heuristicValue;
		this->totalScore = other.totalScore;
	}
	return *this;
}

void	Board::up() noexcept
{
	tiles[emptyTile] ^= tiles[emptyTile - PuzzleData::n];
	tiles[emptyTile - PuzzleData::n] ^= tiles[emptyTile];
	tiles[emptyTile] ^= tiles[emptyTile - PuzzleData::n];
	emptyTile -= PuzzleData::n;
}

void	Board::down() noexcept
{
	tiles[emptyTile] ^= tiles[emptyTile + PuzzleData::n];
	tiles[emptyTile + PuzzleData::n] ^= tiles[emptyTile];
	tiles[emptyTile] ^= tiles[emptyTile + PuzzleData::n];
	emptyTile += PuzzleData::n;
}

void	Board::left() noexcept
{
	tiles[emptyTile] ^= tiles[emptyTile - 1];
	tiles[emptyTile - 1] ^= tiles[emptyTile];
	tiles[emptyTile] ^= tiles[emptyTile - 1];
	emptyTile -= 1;
}

void	Board::right() noexcept
{
	tiles[emptyTile] ^= tiles[emptyTile + 1];
	tiles[emptyTile + 1] ^= tiles[emptyTile];
	tiles[emptyTile] ^= tiles[emptyTile + 1];
	emptyTile += 1;
}

std::ostream& operator<<(std::ostream& os, const Board& board)
{
	ui32	n = PuzzleData::n;
	const std::vector<ui32>& tiles = board.tiles;

	for (ui32 i = 0; i < n; i++)
	{
		for (ui32 j = 0; j < n; j++)
		{
			os << tiles[i * n + j] << ' ';
		}
		os << '\n';
	}
	return os;
}
#include "Board.hpp"

#include <iostream>
#include <fstream>
#include <sstream>
#include <stdexcept>

Board::Board(const Board& other)
{
	*this = other;
}

Board& Board::operator=(const Board &other)
{
	if (this != &other)
	{
		this->tiles = other.tiles;
		this->n = other.n;
	}
	return *this;
}

Board::Board(const char* filename)
{
	std::ifstream file(filename);

	if (file.is_open() == false)
	{
		throw std::invalid_argument("Could not open file: " + std::string(filename));
	}
	std::string line;
	this->n = 0;

	while (file.eof() == false)
	{
		std::getline(file, line);
		if (line.empty() || line[0] == '#')
		{
			continue;
		}
		std::istringstream stream(line);
		int tile, rowCount = 0;

		while (stream >> tile)
		{
			tiles.push_back(tile);
			rowCount++;
		}
		if (this->n == 0)
		{
			this->n = rowCount;
		}
		else if (this->n != rowCount)
		{
			throw std::invalid_argument("Inconsistent row lengths in file: " + std::string(filename));
		}
	}
	if (tiles.size() != static_cast<size_t>(this->n * this->n))
	{
		throw std::invalid_argument("Invalid number of tiles in file: " + std::string(filename));
	}
	std::vector<bool> seen(tiles.size(), false);

	for (size_t i = 0; i < tiles.size(); i++)
	{
		int tile = tiles[i];
		if (tile < 0 || tile >= static_cast<int>(tiles.size()))
		{
			throw std::invalid_argument("Tile value out of range in file: " + std::string(filename));
		}
		if (seen[tile] == true)
		{
			throw std::invalid_argument("Duplicate tile value in file: " + std::string(filename));
		}
		seen[tile] = true;
		if (tile == 0)
		{
			hole = i;
		}
	}
	this->size = static_cast<int>(tiles.size());
}

std::ostream& operator<<(std::ostream& os, const Board& board)
{
	int n = board.getSize();
	const std::vector<int>& tiles = board.getTiles();

	for (int i = 0; i < n; ++i)
	{
		for (int j = 0; j < n; ++j)
		{
			os << tiles[i * n + j] << ' ';
		}
		os << '\n';
	}
	return os;
}
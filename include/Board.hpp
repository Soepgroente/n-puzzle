#pragma once

#include <vector>
#include <iostream>

class Board
{
	public:

	Board() = delete;
	~Board() = default;
	Board(const char* filename);
	Board(const Board &other);
	Board& operator=(const Board &other);

	int	operator[](int index) const { return tiles[index]; }

	const std::vector<int>& getTiles() const { return tiles; }
	int getSize() const { return n; }

	void	solve();
	bool	recursiveSolve(Board& board);
	
	private:
	
	std::vector<int>	tiles;
	std::vector<int>	path;
	
	int	n;
	int	size;
	int	hole;

	bool	isSolved() const noexcept;
	void	calculateMoveOrder(int* order) const noexcept;
};

std::ostream& operator<<(std::ostream& os, const Board& board);
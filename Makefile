EXEC		:= n-puzzle
CC			:= c++
INCLUDES	:= -I./include
BASEFLAGS	:= -Wall -Wextra -Werror -std=c++20
DEBUGFLAGS	:= -g -fsanitize=address
OPTIMFLAGS	:= -O3 -flto -march=native -funroll-loops -DNDEBUG -fno-math-errno

SRCS	:=	main.cpp \
			Board.cpp \
			BoardSolve.cpp \

SRC_DIR		:= src
OBJ_DIR		:= $(SRC_DIR)/obj

OBJS		:=	$(addprefix $(OBJ_DIR)/,$(notdir $(SRCS:%.cpp=%.o)))

CPPFLAGS	= $(BASEFLAGS) $(OPTIMFLAGS)

all: $(EXEC)

debug: CPPFLAGS = $(BASEFLAGS) $(DEBUGFLAGS)
debug: re

$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

$(EXEC): $(OBJ_DIR) $(OBJS)
	$(CC) $(CPPFLAGS) $(INCLUDES) $(OBJS) -o $(EXEC)

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp
	$(CC) $(CPPFLAGS) $(INCLUDES) -c $< -o $@

clean:
	rm -rf $(OBJ_DIR)

fclean: clean
	rm -f $(EXEC)

re: fclean all

.PHONY: all clean fclean re debug

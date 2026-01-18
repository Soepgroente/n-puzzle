NAME			:=	n-puzzle
GUI				=	n_puzzle_gui_mac.py
CC				:=	c++
BASE_CPPFLAGS	:=	-Wall -Wextra -Werror -std=c++20 -fPIC
RELEASE_FLAGS	:=	-DNDEBUG -flto -O3 -march=native -fno-math-errno
DEBUG_FLAGS		:=	-g -fsanitize=address

INCLUDES	:=	-I./include \
				-I/opt/homebrew/include \

SRCS		:=	main.cpp \
				Board.cpp \
				solve.cpp \

SRCDIR		:=	src
OBJDIR		:=	$(SRCDIR)/obj
OBJS		:=	$(addprefix $(OBJDIR)/,$(notdir $(SRCS:%.cpp=%.o)))
SYSTEM		:=	$(shell uname -s)

ifeq ($(SYSTEM), Linux)
	GUI = n_puzzle_gui_linux.py
endif

CPPFLAGS = $(BASE_CPPFLAGS) $(RELEASE_FLAGS)

all: $(NAME)

debug: CPPFLAGS = $(BASE_CPPFLAGS) $(DEBUG_FLAGS)
debug: $(NAME)

run: all
	python3 $(GUI)

rundebug: debug
	python3 $(GUI)

rerundebug: fclean rundebug

rerun: fclean run

$(OBJDIR):
	mkdir -p $(OBJDIR)

$(NAME): $(OBJDIR) $(OBJS)
	$(CC) $(CPPFLAGS) $(INCLUDES) -o $(NAME) $(OBJS)

$(OBJDIR)/%.o: $(SRCDIR)/%.cpp
	$(CC) $(CPPFLAGS) $(INCLUDES) -c $< -o $@

clean:
	rm -rf $(OBJDIR)

fclean: clean
	rm -f $(NAME)

re: fclean all

.PHONY: all debug clean fclean re run rundebug rerun
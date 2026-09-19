CC := gcc
LDFLAGS := -lminiaudio -ldl -lpthread -lm  -shared -fPIC 
SRC := playback.c
OBJ := libplayback.so

all: $(SRC)
	$(CC) -o libplayback.so $(SRC) $(LDFLAGS)

clean: 
	rm $(OBJ) 

.PHONY: all clean

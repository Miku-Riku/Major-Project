LIBS = cpu.so

CXX = g++
CXXFLAGS = -Wall -Wextra -g -O2 -fPIC
LDFLAGS = -shared

.PHONY: all clean

all: $(LIBS)

%.so: %.cpp
	@echo "[EXT]" Compiling $< ...
	@$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $<

clean:
	@echo "[EXT] Cleaning up build..."
	@rm -f $(LIBS)

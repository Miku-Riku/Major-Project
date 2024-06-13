LIBS = l2

.PHONY: all clean

all: $(LIBS)

%: %.p4
	@echo "[P4]" Compiling $< ...
	@mkdir -p ../build
	@p4c-bm2-ss --p4v 16 --p4runtime-files ../build/$@.p4.p4info.txt -o ../build/$@.json $@.p4 --emit-externs

clean:
	@echo "[P4] Cleaning up build..."
	@rm -rf ../build

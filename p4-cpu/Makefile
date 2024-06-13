.PHONY: extern run docker

extern:
	cd extern && make clean && make

p4:
	cd p4src && make clean && make

clean:
	cd p4src && make clean
	cd extern && make clean
	rm -rf logs
	rm -rf pcaps

run:
	make extern
	make p4
	python3 run.py
	mn -c
	python3 records/graph.py

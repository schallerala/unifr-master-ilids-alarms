

build:
	-mkdir $@

build/decord: build
	git clone --recursive https://github.com/schallerala/decord $@

build/decord/build: build/decord
	-mkdir $@
	@# https://github.com/dmlc/decord
	cd $@; \
	if which nvcc; then cmake .. -DUSE_CUDA=ON -DCMAKE_BUILD_TYPE=Release; \
	else cmake .. -DCMAKE_BUILD_TYPE=Release; \
	fi;

clean-decord:
	-rm -rf build/decord
	-poetry remove decord

.PHONY: clean-decord

install-decord:
	make build/decord/build
	cd build/decord/build && make
	cd build/decord/python && make clean && make build-wheel
	poetry add build/decord/python/decord*.whl

.PHONY: install-decord
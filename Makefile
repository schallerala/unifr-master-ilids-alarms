DECORD_CMAKE_USER_CUDA := $(shell if which -s nvcc; then echo "ON"; else echo "0"; fi)

build:
	-mkdir $@

build/decord: build
	test -d $@ || git clone --recursive https://github.com/schallerala/decord $@

build/decord/build: build/decord
	test -d $@ || mkdir $@
	@# https://github.com/dmlc/decord
	cd $@ && cmake .. -DUSE_CUDA=$(DECORD_CMAKE_USER_CUDA) -DCMAKE_BUILD_TYPE=Release

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
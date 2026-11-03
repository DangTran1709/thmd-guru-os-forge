# THMD-Guru OS Forge — Makefile
# Owner: os-forge-devops

.PHONY: help test packages stage-desktop stage-server stage-attt iso-desktop iso-server iso-attt all clean

help:
	@bash builder/forge.sh help

test:
	@bash tests/smoke-test.sh

packages:
	@bash builder/forge.sh packages

stage-desktop:
	@bash builder/forge.sh stage desktop

stage-server:
	@bash builder/forge.sh stage server

stage-attt:
	@bash builder/forge.sh stage attt

iso-desktop:
	@bash builder/forge.sh iso desktop

iso-server:
	@bash builder/forge.sh iso server

iso-attt:
	@bash builder/forge.sh iso attt

all:
	@bash builder/forge.sh all

clean:
	@bash builder/forge.sh clean

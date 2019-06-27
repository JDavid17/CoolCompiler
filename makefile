.PHONY: clean

main:
	

clean: clean-build clean-ply clean-vscode

clean-build:
	rm -fr build

clean-ply:
	rm lextab.py
	rm yacctab.py
	rm hello_world.asm

clean-vscode:
	rm -rf /__pycache__
	rm -rf /src/__pycache__


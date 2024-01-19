default:
	echo "no target entered"

ssh-keygen:
	@if [ ! -f ~/.ssh/id_ecdsa ]; then \
		ssh-keygen -t ecdsa -f ~/.ssh/id_ecdsa -N "";\
	fi
	ssh-copy-id -i ~/.ssh/id_ecdsa.pub $(target)

robot-install:
	ssh $(target) "sudo apt-get install -y python3-pip python3.11-venv && sudo raspi-config nonint do_i2c 0 && sudo reboot"

robot-clean:
	echo "cleaning $(target)"
	ssh $(target) "rm -rf ~/src; rm -rf ~/test; rm -f meta.json; rm -f test.sh; rm -f requirements.txt;"

robot-copy: robot-clean
	echo "copying files to $(target)"
	scp -r src $(target):~/
	scp -r test $(target):~/
	scp meta.json test.sh requirements.txt $(target):~/

robot-development-test:
	echo "running module on $(target)"
	ssh $(target) "python3 -m venv .venv && source .venv/bin/activate && pip3 install -r requirements.txt"
	ssh $(target) "source .venv/bin/activate && python3 src/main.py"

robot-build:
	echo "building binary on $(target)"
	ssh $(target) "source .venv/bin/activate && python3 -m PyInstaller --onefile --hidden-import="googleapiclient" ~/src/main.py"

robot-deploy:
	echo "deploying local module on $(target)"
	ssh $(target) "sudo rm /viam-module; sudo cp dist/main /viam-module"

robot-restart:
	ssh $(target) "echo 'restarting viam server... ' && sudo systemctl restart viam-server && echo 'done'"

generate-tar:
	mkdir -p dist
	echo "copying binary from $(target)"
	scp $(target):~/dist/main dist/main
	tar -czvf dist/archive.tar.gz dist/main

development-workflow: robot-copy robot-development-test

test-workflow: robot-copy robot-restart

package-workflow: robot-copy robot-build robot-deploy generate-tar robot-restart

package-mac-workflow:
	python3 -m venv .venv && source .venv/bin/activate && pip3 install -r requirements.txt && python3 -m PyInstaller -v && python3 -m PyInstaller --onefile --hidden-import="googleapiclient" src/main.py
	tar -czvf dist/archive.tar.gz dist/main
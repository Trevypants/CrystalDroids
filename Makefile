### Commands to setup all necessary dependencies for running (and developing) the application ###
setup-deps:
	@echo "################################"
	@echo "## Setting up Dependencies... ##"
	@echo "################################"
	@/bin/bash -c "scripts/setup_deps.sh"

setup-dev:
	@echo "#############################"
	@echo "## Setting up Local Env... ##"
	@echo "#############################"
	@/bin/bash -c "scripts/setup_dev.sh"

	@echo "###############################"
	@echo "## Local Env setup complete! ##"
	@echo "###############################"

setup:
	$(MAKE) setup-deps
	$(MAKE) setup-dev

### Commands to git commit ###
stage:
	@echo "Staging changes..."
	@git add .
	@echo "Changes staged!"

commit:
	@echo "Committing changes..."
	@poetry run cz commit
	@echo "Changes committed!"

push: 
	@echo "Pushing changes..."
	@git push
	@echo "Changes pushed!"
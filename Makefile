gitRepo = /home/felix/web/YAExpandRegion
testsRepo = ../YAExpandRegionTests/*

test:
	pytest-watch -qc --runner="pytest -qs"

test-once:
	pytest -q

move-to-git:
	find $(gitRepo) -mindepth 1 ! -regex '.*\.git.*' -delete
	cp -r . $(gitRepo)
	cp -r $(testsRepo) $(gitRepo)

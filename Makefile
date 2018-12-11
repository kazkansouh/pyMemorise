
UI_DIR=memorise/ui
UI_FILES=$(wildcard $(UI_DIR)/*.ui)
UI_PYCODE=$(patsubst $(UI_DIR)/%.ui,$(UI_DIR)/ui%.py,$(UI_FILES))

$(UI_DIR)/ui%.py: $(UI_DIR)/%.ui
	pyuic5 $< -o $@

.PHONY: build install

build: $(UI_PYCODE)
	python3 setup.py build

install: build
	python3 setup.py install

run: $(UI_PYCODE)
	python3 -m memorise

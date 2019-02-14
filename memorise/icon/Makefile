SIZES=70x70 144x144 150x150 310x310
ICONS=$(patsubst %,icon-%.png,$(SIZES))

SVG=blueicon.svg

.PHONY: default clean

default: $(ICONS)

%.png: $(SVG)
	convert -background none $< -resize $(patsubst icon-%.png,%,$@) $@

clean:
	rm -f $(ICONS)

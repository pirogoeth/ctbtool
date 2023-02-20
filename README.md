# ctbtool

ctbtool is a feature-limited utility for extracting data out of AutoCAD's CTB files and exporting the binary CTB data into human-readable JSON.

## features

- reads compressed CTB data and outputs the contained text (`extract` mode)
- parses the extracted CTB data into JSON

## limitations

- only tested/used on files compressed with the `pmzlibcodec` compression type
- discards the trailer data in custom lineweight tables

## roadmap

- [ ] take the JSON-formatted CTB data and produce an HTML specimen page
- [ ] try to handle 100% of the CTB data properly (looking at you, lineweight trailers)

## contributing

contributions welcome! this code is released into the public domain, and all project code and contributions shall be unencumbered accordingly.
thanks <3

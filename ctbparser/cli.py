# -*- coding: utf-8 -*-

import io
import json
import os
import pathlib
import sys
from typing import Optional

import click

from ctbparser import parser
from ctbparser.ctbfile import CtbFile


def _open_output_stream(outfile: Optional[str], outmode: str) -> io.RawIOBase:
    if outfile is not None:
        return io.open(outfile, outmode)
    else:
        return os.fdopen(sys.stdout.fileno(), "wb", closefd=False)


@click.group()
def root():
    pass


@root.command()
@click.option(
    "-o",
    "--outfile",
    type=click.Path(dir_okay=True, file_okay=True),
    help="Where the extracted CTB should be written",
    default=None,
)
@click.option(
    "-f",
    "--force",
    type=bool,
    help="Whether output file should be overwritten",
    default=False,
)
@click.option(
    "-P",
    "--parse/--no-parse",
    type=bool,
    help="Whether the plot style data should be parsed and output as JSON",
    default=True,

)
@click.argument("infile", type=click.Path(exists=True, dir_okay=False, file_okay=True))
def extract(outfile: str, infile: str, force: bool, parse: bool):
    """Extract the plot style data from the CTB file. Outputs as text."""
    ctb = CtbFile.from_file(infile)
    parse_func = {
        True: lambda data: json.dumps(parser.parse(data)).encode("utf-8"),
        False: lambda data: data,
    }.get(parse)
    try:
        outmode = "xb" if not force else "wb"
        if outfile is not None:
            outfile = pathlib.Path(infile).with_suffix(".txt")

        with _open_output_stream(outfile, outmode) as out:
            out.write(parse_func(ctb.data))
            out.flush()
    except FileExistsError:
        print(f"{outfile} already exists, skipping")

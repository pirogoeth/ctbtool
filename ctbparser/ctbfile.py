# -*- coding: utf -*-

from __future__ import annotations

import io
import struct
import zlib
from copy import copy


class CtbFile:
    struct_format: str = "48sIHHHH"

    @classmethod
    def from_file(cls, inpath: str) -> CtbFile:
        with io.open(inpath, "rb") as infile:
            return cls.parse_container(infile)

    @classmethod
    def parse_container(cls, indata: io.BufferedIOBase) -> CtbFile:
        header_size = struct.calcsize(cls.struct_format)
        header_data = struct.unpack(cls.struct_format, indata.read(header_size))
        metadata, checksum, unknown, m1, compressed_size, m2 = header_data

        assert m1 == 0x0001
        assert m2 == 0x0000

        file_version = metadata[: metadata.index(b",")]
        format_version = metadata[metadata.index(b",") + 1 : metadata.rindex(b",")]
        compressed = metadata[metadata.rindex(b",") + 1 :]
        compression_type = None
        if compressed.startswith(b"compress"):
            # two bytes after `compress` are [0x0d 0x0a], purpose unknown
            compression_type = compressed[10:]

        return cls(
            file_version,
            format_version,
            checksum,
            compression_type,
            indata,
            compressed_size,
        )

    def __init__(
        self,
        file_version: str,
        ctb_version: str,
        expected_checksum: int,
        compression_type: str,
        data: io.BufferedIOBase,
        compressed_size: int,
    ):
        self.file_version = file_version
        self.ctb_version = ctb_version
        self.compression_type = compression_type

        data = data.read()
        if len(data) != compressed_size:
            raise RuntimeError(
                "Size of compressed data does not match recorded compressed size"
            )

        actual_checksum = zlib.adler32(data)
        if actual_checksum != expected_checksum:
            raise RuntimeError(
                "Compressed data checksum does not match recorded checksum"
            )

        self.data = self.deflate(data)

    def deflate(self, data: bytes) -> bytes:
        switch = {
            b"pmzlibcodec": zlib.decompress,
            None: NotImplemented,
        }
        return switch.get(self.compression_type)(data)

    def __repr__(self) -> str:
        return f"<CtbFile {self.file_version=} {self.ctb_version=} {self.compression_type=}>"


assert struct.calcsize(CtbFile.struct_format) == 60

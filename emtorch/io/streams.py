# Copyright (c) 2025-2026 Warsaw University of Technology
# This file is licensed under the MIT License.
# See the LICENSE.txt file in the root of the repository for full details.

"""
Stream (files, pipes etc.) bases I/O components.
"""

import logging
from threading import Event
from typing import IO

from . import Selectable

logger = logging.getLogger(__name__)


class Stream(Selectable):
    def __init__(self, name: str, stream: IO[bytes]):
        super().__init__(name)
        self.stream = stream
        self.logger = logging.LoggerAdapter(logger, extra={"subtask": name})
        self._eof = False

    def close(self) -> None:
        self.stream.close()

    def fileno(self) -> int:
        return self.stream.fileno()

    def is_closed(self) -> bool:
        return self.stream.closed

    def at_eof(self) -> bool:
        return self._eof

    def mark_eof(self) -> None:
        self._eof = True


class InputStream(Stream):
    def write(self) -> None:
        raise RuntimeError("Should be used only for reading")

    def wants_to_write(self) -> bool:
        return False

    def wants_to_read(self) -> bool:
        return True


class OutputStream(Stream):
    def read(self) -> None:
        raise RuntimeError("Should be used only for writing")

    def wants_to_read(self) -> bool:
        return False


class StreamWriter(OutputStream):
    def __init__(self, name: str, stream: IO[bytes], data: bytes):
        super().__init__(name, stream)
        self._data = data
        self._event_done = Event()

    def wait_for_done(self, timeout: float) -> bool:
        return self._event_done.wait(timeout)

    def write(self) -> None:
        self.logger.info(f"writing {len(self._data)} bytes.")

        written = self.stream.write(self._data)
        self._data = self._data[written:]

        self.logger.info(f"wrote {written}, {len(self._data)} bytes remaining.")
        if len(self._data) == 0:
            self.logger.info("closing the stream")
            self.close()
            self._event_done.set()

    def wants_to_write(self) -> bool:
        return len(self._data) > 0


class StreamLogger(InputStream):
    def __init__(self, name: str, subname: str, stream: IO[bytes]):
        super().__init__(name, stream)
        self._subname = subname

        self._buffer = bytearray()

    def read(self) -> None:
        data = self.stream.read(4 * 1024)
        if len(data) == 0:
            self.mark_eof()
        for b in data:
            if b == b"\n"[0]:
                self._flush()
            else:
                self._buffer.append(b)

    def _flush(self) -> None:
        self.logger.info(f"{self._subname} - {bytes(self._buffer.rstrip())!r}")
        self._buffer.clear()

    def close(self) -> None:
        if self._buffer:
            self._flush()
        super().close()

import logging
from contextlib import contextmanager
from pathlib import Path, PurePath
from typing import Iterator

from multilspy.language_server import FileUtils
from multilspy.language_server import LanguageServer as _LanguageServer
from multilspy.language_server import LSPConstants, LSPFileBuffer, MultilspyException
from multilspy.lsp_protocol_handler.lsp_types import SemanticTokens


class LanguageServer(_LanguageServer):
    @contextmanager
    def open_file(
        self,
        relative_file_path: str,
        contents: str | None = None,
    ) -> Iterator[None]:
        """
        Open a file in the Language Server.
        This is required before making any requests to the Language Server.
        This version is extended to support custom file contents.

        :param relative_file_path: The relative path of the file to open.
        """
        if not self.server_started:
            self.logger.log(
                "open_file called before Language Server started",
                logging.ERROR,
            )
            raise MultilspyException("Language Server not started")

        absolute_file_path = str(
            PurePath(self.repository_root_path, relative_file_path)
        )
        uri = Path(absolute_file_path).as_uri()

        if uri in self.open_file_buffers:
            assert self.open_file_buffers[uri].uri == uri
            assert self.open_file_buffers[uri].ref_count >= 1

            self.open_file_buffers[uri].ref_count += 1
            yield
            self.open_file_buffers[uri].ref_count -= 1
        else:
            if contents is None:
                contents = FileUtils.read_file(self.logger, absolute_file_path)

            version = 0
            self.open_file_buffers[uri] = LSPFileBuffer(
                uri, contents, version, self.language_id, 1
            )

            self.server.notify.did_open_text_document(
                {
                    LSPConstants.TEXT_DOCUMENT: {
                        LSPConstants.URI: uri,
                        LSPConstants.LANGUAGE_ID: self.language_id,
                        LSPConstants.VERSION: 0,
                        LSPConstants.TEXT: contents,
                    }
                }
            )
            yield
            self.open_file_buffers[uri].ref_count -= 1

        if self.open_file_buffers[uri].ref_count == 0:
            self.server.notify.did_close_text_document(
                {
                    LSPConstants.TEXT_DOCUMENT: {
                        LSPConstants.URI: uri,
                    }
                }
            )
            del self.open_file_buffers[uri]

    async def semantic_tokens(
        self,
        file: Path,
        contents: str | None = None,
    ) -> SemanticTokens | None:
        """Compute and convert semantic tokens for the given file."""

        if not self.server_started:
            self.logger.log(
                "semantic_tokens called before Language Server started",
                logging.ERROR,
            )
            raise MultilspyException("Language Server not started")

        relative_file_path = str(file.relative_to(self.repository_root_path))
        with self.open_file(relative_file_path, contents):
            return await self.server.send.semantic_tokens_full(
                {"textDocument": {"uri": file.as_uri()}}
            )

import json
import logging
import os
from contextlib import asynccontextmanager
from importlib.resources import files
from pathlib import Path
from typing import AsyncIterator

from multilspy.language_server import Language
from multilspy.lsp_protocol_handler.lsp_types import (
    InitializeParams,
    InitializeResult,
    SemanticTokens,
)
from multilspy.lsp_protocol_handler.server import ProcessLaunchInfo
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger

from ..lsp.download.pyright import get_pyright_path
from .language_server import LanguageServer


class PyrightServer(LanguageServer):
    def __init__(
        self,
        logger: MultilspyLogger,
        root: Path,
        *,
        pyright_cmd: str | Path | None = None,
        trace_lsp_communication: bool = False,
        log_lsp: bool,
    ):
        if pyright_cmd is None:
            pyright_cmd = get_pyright_path(log_lsp)
        super().__init__(
            MultilspyConfig(Language.PYTHON, trace_lsp_communication),
            logger,
            str(root),
            ProcessLaunchInfo(cmd=f"{pyright_cmd} --stdio"),
            "python",
        )
        self.init_response: InitializeResult | None = None

    def _get_initialize_params(self, repository: Path) -> InitializeParams:
        with (files() / "pyright_params.json").open("r") as f:
            d = json.load(f)

        repository = repository.resolve()
        uri = repository.as_uri()

        d["processId"] = os.getpid()
        d["rootPath"] = str(repository)
        d["rootUri"] = uri
        d["workspaceFolders"] = [{"uri": uri, "name": repository.name}]

        return d

    @asynccontextmanager
    async def start_server(self) -> AsyncIterator["PyrightServer"]:
        async def execute_client_command(params):
            return []

        async def noop(params):
            return

        async def window_log_message(msg):
            self.logger.log(f"LSP: window/logMessage: {msg}", logging.INFO)

        self.server.on_request("client/registerCapability", noop)
        self.server.on_notification("language/status", noop)
        self.server.on_notification("window/logMessage", window_log_message)
        self.server.on_request("workspace/executeClientCommand", execute_client_command)
        self.server.on_notification("$/progress", noop)
        self.server.on_notification("textDocument/publishDiagnostics", noop)
        self.server.on_notification("language/actionableNotification", noop)

        async with super().start_server():
            self.logger.log("Starting pyright server process", logging.INFO)
            await self.server.start()
            initialize_params = self._get_initialize_params(
                Path(self.repository_root_path)
            )

            self.logger.log(
                "Sending initialize request to LSP server and awaiting response",
                logging.INFO,
            )
            self.init_response = await self.server.send.initialize(initialize_params)
            assert "semanticTokensProvider" in self.init_response["capabilities"]

            self.server.notify.initialized({})

            yield self

            await self.server.shutdown()
            await self.server.stop()

    async def semantic_tokens_full(self, p: Path) -> SemanticTokens | None:
        return await self.server.send.semantic_tokens_full(
            {"textDocument": {"uri": p.as_uri()}}
        )

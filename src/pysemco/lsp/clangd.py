import json
import logging
import os
import shlex
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from importlib.resources import files
from pathlib import Path

import psutil
from multilspy.lsp_protocol_handler.lsp_types import InitializeParams, InitializeResult
from multilspy.lsp_protocol_handler.server import ProcessLaunchInfo
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger

from ..tokens.defs import StrPath
from .download.clangd import get_clangd_path
from .language_server import LanguageServer


class ClangdServer(LanguageServer):
    def __init__(
        self,
        logger: MultilspyLogger,
        root: Path,
        *,
        clangd_cmd: StrPath | None = None,
        trace_lsp_communication: bool = False,
        log_lsp: bool,
    ):
        if clangd_cmd is None:
            clangd_cmd = get_clangd_path(log_lsp)
        super().__init__(
            MultilspyConfig("cpp", trace_lsp_communication),  # pyright: ignore
            logger,
            str(root),
            ProcessLaunchInfo(cmd=shlex.quote(str(clangd_cmd))),
            "cpp",
        )
        self.init_response: InitializeResult | None = None

    def _get_initialize_params(self, repository: Path) -> InitializeParams:
        with (files() / "clangd_params.json").open("r") as f:
            d = json.load(f)

        repository = repository.resolve()
        uri = repository.as_uri()

        d["processId"] = os.getpid()
        d["rootPath"] = str(repository)
        d["rootUri"] = uri
        d["workspaceFolders"] = [{"uri": uri, "name": repository.name}]

        return d

    @asynccontextmanager
    async def start_server(self) -> AsyncGenerator["ClangdServer"]:
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
            self.logger.log("Starting clangd server process", logging.INFO)
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

            # Best-effort shutdown; if the process already exited, ignore it.
            try:
                await self.server.shutdown()
            except Exception as exc:
                self.logger.log(f"Error during LSP shutdown: {exc}", logging.WARNING)
            try:
                await self.server.stop()
            except psutil.NoSuchProcess:
                # Process is already gone; nothing left to clean up.
                self.logger.log(
                    "LSP process already exited before stop(); ignoring.", logging.INFO
                )
            except Exception as exc:
                self.logger.log(
                    f"Error while stopping LSP server: {exc}", logging.WARNING
                )

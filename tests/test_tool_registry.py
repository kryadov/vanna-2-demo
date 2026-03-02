import asyncio
import logging
import os
import unittest

from app import main
from app.config import DBConfig
from app.logging_config import configure_logging


class ToolRegistryTests(unittest.TestCase):
    def test_run_sql_tool_registered(self) -> None:
        tool_names = asyncio.run(main.tools.list_tools())
        self.assertIn("run_sql", tool_names)

    def test_run_sql_tool_uses_valid_postgres_runner_config(self) -> None:
        run_sql_tool = asyncio.run(main.tools.get_tool("run_sql"))
        sql_runner = run_sql_tool.sql_runner

        connection_string = getattr(sql_runner, "connection_string", None)
        self.assertNotIsInstance(connection_string, DBConfig)

        if connection_string is not None:
            self.assertIsInstance(connection_string, str)
            self.assertTrue(connection_string)
        else:
            connection_params = getattr(sql_runner, "connection_params", None)
            self.assertIsInstance(connection_params, dict)
            self.assertEqual(connection_params["host"], main.settings.db.host)
            self.assertEqual(connection_params["database"], main.settings.db.name)
            self.assertEqual(connection_params["user"], main.settings.db.user)


class LoggingConfigTests(unittest.TestCase):
    def test_httpx_logger_suppressed_when_not_debug(self) -> None:
        original_level = os.environ.get("LOG_LEVEL")
        os.environ["LOG_LEVEL"] = "INFO"
        try:
            configure_logging()
            self.assertEqual(logging.getLogger("httpx").level, logging.WARNING)
            self.assertEqual(logging.getLogger("httpcore").level, logging.WARNING)
        finally:
            if original_level is None:
                os.environ.pop("LOG_LEVEL", None)
            else:
                os.environ["LOG_LEVEL"] = original_level


if __name__ == "__main__":
    unittest.main()

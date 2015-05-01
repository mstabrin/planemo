from collections import namedtuple
import contextlib
import shutil
from tempfile import mkdtemp
import threading
from requests import post

from werkzeug.serving import run_simple

from .shed_app import (
    app,
    InMemoryShedDataModel,
)
from . import network_util

DEFAULT_OP_TIMEOUT = 2


def mock_model(directory):
    return InMemoryShedDataModel(
        directory
    ).add_category(
        "c1", "Text Manipulation"
    ).add_category(
        "c2", "Sequence Analysis"
    ).add_repository(
        "r1",
        name="test_repo_1",
        owner="iuc",
    )


def setup_mock_shed():
    port = network_util.get_free_port()
    directory = mkdtemp()

    def run():
        app.debug = True
        app.config["model"] = mock_model(directory)
        run_simple(
            'localhost',
            port,
            app,
            use_reloader=False,
            use_debugger=True
        )

    t = threading.Thread(target=run)
    t.start()
    network_util.wait_net_service("localhost", port, DEFAULT_OP_TIMEOUT)
    return MockShed("http://localhost:%d" % port, directory, t)


@contextlib.contextmanager
def mock_shed():
    mock_shed_obj = None
    try:
        mock_shed_obj = setup_mock_shed()
        yield mock_shed_obj
    finally:
        if mock_shed_obj is not None:
            mock_shed_obj.shutdown()


def _shutdown(self):
    post("%s/shutdown" % self.url)
    self.thread.join(DEFAULT_OP_TIMEOUT)
    shutil.rmtree(self.directory)

MockShed = namedtuple("MockShed", ["url", "directory", "thread"])
MockShed.shutdown = _shutdown

__all__ = ["setup_mock_shed", "mock_shed"]

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from app import setup


class FakeCatalog:
    def __init__(self, paths):
        pass

    def problems(self):
        return [{"slug": "two-sum"}, {"slug": "valid-anagram"}]


def run_with(result, argv=()):
    out = io.StringIO()
    with mock.patch.object(setup.catalog_mod, "Catalog", FakeCatalog), \
            mock.patch.object(setup.statements, "fetch_all", return_value=result), \
            redirect_stdout(out):
        code = setup.main(list(argv))
    return code, out.getvalue()


class SetupExitTests(unittest.TestCase):
    def test_all_downloads_ok_exits_0(self):
        code, text = run_with({"have": 2, "total": 2, "failed": []})
        self.assertEqual(code, 0)
        self.assertIn("2 of 2 statements on disk.", text)

    def test_a_failed_download_exits_1(self):
        code, text = run_with({"have": 1, "total": 2, "failed": [{"slug": "valid-anagram"}]})
        self.assertEqual(code, 1)
        self.assertIn("--only valid-anagram", text)


if __name__ == "__main__":
    unittest.main()

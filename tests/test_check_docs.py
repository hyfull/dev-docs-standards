from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_docs import check  # noqa: E402


STANDARD = (
    "https://github.com/Rotic-h/dev-docs-standards/"
    "blob/v1.0.0/guidelines/documentation.md"
)


class CheckDocsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="docs-standard-test-")
        self.root = Path(self.temp.name).resolve()
        self.assertTrue(self.root.is_relative_to(Path(tempfile.gettempdir()).resolve()))
        self.write("README.md", "# Example\n\n[文档中心](docs/README.md)\n")
        self.write(
            "docs/README.md",
            "# 文档中心\n\n[约定](CONTRIBUTING.md)\n"
            "[架构](architecture/overview.md)\n",
        )
        self.write(
            "docs/CONTRIBUTING.md",
            "---\ndoc_type: governance\nstatus: current\narea: docs\n"
            "summary: 文档约定\n---\n\n# 文档约定\n\n"
            f"遵循 [团队文档规范 v1.0.0]({STANDARD})。\n",
        )
        self.write(
            "docs/architecture/overview.md",
            "---\ndoc_type: architecture\nstatus: review-needed\n"
            "area: platform\nsummary: 待核对的架构\n---\n\n# 架构\n",
        )

    def tearDown(self) -> None:
        self.assertTrue(self.root.is_relative_to(Path(tempfile.gettempdir()).resolve()))
        self.temp.cleanup()

    def write(self, name: str, content: str) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_valid_project(self) -> None:
        self.assertEqual(check(self.root, "v1.0.0"), [])

    def test_version_mismatch(self) -> None:
        errors = check(self.root, "v1.1.0")
        self.assertTrue(any("版本不一致" in error for error in errors))

    def test_orphan_and_broken_link(self) -> None:
        self.write(
            "docs/reference/hidden.md",
            "---\ndoc_type: reference\nstatus: current\narea: api\n"
            "summary: 隐藏参考\n---\n\n# 隐藏参考\n\n[丢失](missing.md)\n",
        )
        errors = check(self.root, "v1.0.0")
        self.assertTrue(any("无法从 docs/README.md 导航" in error for error in errors))
        self.assertTrue(any("本地链接不存在" in error for error in errors))

    def test_decision_filename(self) -> None:
        self.write(
            "docs/decisions/use-postgresql.md",
            "---\ndoc_type: decision\nstatus: current\narea: data\n"
            "summary: 数据库选择\n---\n\n# 数据库选择\n",
        )
        self.write(
            "docs/README.md",
            "# 文档中心\n\n[约定](CONTRIBUTING.md)\n"
            "[架构](architecture/overview.md)\n"
            "[决策](decisions/use-postgresql.md)\n",
        )
        errors = check(self.root, "v1.0.0")
        self.assertTrue(any("ADR 文件名" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

"""Check project documentation against the shared, versioned convention."""

from __future__ import annotations

import argparse
import re
import sys
from collections import deque
from pathlib import Path
from urllib.parse import unquote, urlsplit


LOCATIONS = {
    "architecture": "architecture",
    "design": "design",
    "decision": "decisions",
    "reference": "reference",
    "guide": "guides",
    "tutorial": "tutorials",
    "explanation": "explanation",
    "record": "records",
    "standard": ".",
    "governance": ".",
}
STATUSES = {"current", "proposed", "review-needed", "historical", "superseded"}
FIELDS = {"doc_type", "status", "area", "summary"}
FILENAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\.md\Z")
DECISION_FILENAME = re.compile(r"[0-9]{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.md\Z")
LINK = re.compile(r"!?\[[^\]]*\]\((<[^>]+>|[^)]+)\)")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
STANDARD_LINK = re.compile(
    r"https://github\.com/hyfull/dev-docs-standards/blob/"
    r"(?P<version>v[0-9]+\.[0-9]+\.[0-9]+)/guidelines/documentation\.md"
)


def metadata_for(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("缺少顶部元数据块")
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("顶部元数据块没有结束标记") from exc
    metadata: dict[str, str] = {}
    for line in lines[1:closing]:
        if ":" not in line:
            raise ValueError(f"无效元数据行: {line}")
        key, value = (part.strip() for part in line.split(":", 1))
        if key in metadata:
            raise ValueError(f"重复元数据字段: {key}")
        metadata[key] = value
    missing = FIELDS - metadata.keys()
    unknown = metadata.keys() - FIELDS - {"superseded_by"}
    if missing or unknown or any(not value for value in metadata.values()):
        raise ValueError(f"元数据无效：缺少 {sorted(missing)}，未知 {sorted(unknown)}")
    if metadata["status"] not in STATUSES:
        raise ValueError(f"未知状态: {metadata['status']}")
    if metadata["status"] == "superseded" and "superseded_by" not in metadata:
        raise ValueError("superseded 文档必须填写 superseded_by")
    if not any(line.startswith("# ") for line in lines[closing + 1 :]):
        raise ValueError("缺少一级标题")
    return metadata


def destinations(path: Path) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    fenced = False
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        for match in LINK.finditer(line):
            destination = match.group(1).strip()
            raw = destination[1:-1] if destination.startswith("<") else destination.split(" ", 1)[0]
            result.append((number, raw))
    return result


def local_target(source: Path, raw: str, root: Path) -> Path | None:
    parsed = urlsplit(raw)
    if parsed.scheme or raw.startswith(("#", "//")) or not parsed.path:
        return None
    target = (source.parent / unquote(parsed.path)).resolve()
    if not target.is_relative_to(root):
        raise ValueError(f"链接越出项目目录: {raw}")
    return target


def check(root: Path, expected_version: str | None) -> list[str]:
    errors: list[str] = []
    docs = root / "docs"
    required = [root / "README.md", docs / "README.md", docs / "CONTRIBUTING.md"]
    for path in required:
        if not path.is_file():
            errors.append(f"{path.relative_to(root)}: 缺少必需入口")
    if not docs.is_dir():
        return errors

    documents = [
        path for path in sorted(docs.rglob("*.md"))
        if path != docs / "README.md" and "_templates" not in path.relative_to(docs).parts
    ]
    for path in documents:
        relative = path.relative_to(docs)
        label = path.relative_to(root).as_posix()
        if path.name not in {"CONTRIBUTING.md", "README.md"} and not FILENAME.fullmatch(path.name):
            errors.append(f"{label}: 文件名应为小写英文 kebab-case")
        try:
            metadata = metadata_for(path)
            kind = metadata["doc_type"]
            if kind not in LOCATIONS:
                raise ValueError(f"未知文档类型: {kind}")
            folder = relative.parent.as_posix()
            if folder != LOCATIONS[kind]:
                raise ValueError(f"{kind} 文档应位于 docs/{LOCATIONS[kind]}/")
            if kind == "decision" and not DECISION_FILENAME.fullmatch(path.name):
                raise ValueError("ADR 文件名应为 NNNN-short-title.md")
            if "superseded_by" in metadata:
                replacement = (docs / metadata["superseded_by"]).resolve()
                if not replacement.is_relative_to(docs) or not replacement.is_file():
                    raise ValueError("superseded_by 指向的文档不存在")
        except ValueError as exc:
            errors.append(f"{label}: {exc}")

    contribution = docs / "CONTRIBUTING.md"
    if contribution.is_file():
        matches = list(STANDARD_LINK.finditer(contribution.read_text(encoding="utf-8-sig")))
        if len(matches) != 1:
            errors.append("docs/CONTRIBUTING.md: 须恰好引用一次固定版本的团队文档规范")
        elif expected_version and matches[0].group("version") != expected_version:
            errors.append(
                "docs/CONTRIBUTING.md: 规范链接版本与 CI 检查器版本不一致"
            )

    linked_docs: dict[Path, set[Path]] = {}
    sources = [root / "README.md", root / "AGENTS.md", *docs.rglob("*.md")]
    for source in sources:
        if not source.is_file():
            continue
        linked_docs[source.resolve()] = set()
        for number, raw in destinations(source):
            try:
                target = local_target(source, raw, root)
            except ValueError as exc:
                errors.append(f"{source.relative_to(root)}:{number}: {exc}")
                continue
            if target is None:
                continue
            if not target.exists():
                errors.append(f"{source.relative_to(root)}:{number}: 本地链接不存在: {raw}")
            elif target.is_file() and target.suffix.lower() == ".md":
                linked_docs[source.resolve()].add(target)

    index = (docs / "README.md").resolve()
    reached = {index}
    pending = deque([index])
    while pending:
        for target in linked_docs.get(pending.popleft(), set()):
            if target.is_relative_to(docs) and target not in reached:
                reached.add(target)
                pending.append(target)
    for path in documents:
        if path.resolve() not in reached:
            errors.append(f"{path.relative_to(root)}: 无法从 docs/README.md 导航到此文档")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="项目根目录")
    parser.add_argument("--standard-version", help="CI 引用的规范发布版本")
    args = parser.parse_args()
    root = args.root.resolve()
    errors = check(root, args.standard_version)
    if errors:
        print("文档检查失败：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("文档检查通过：元数据、路径、命名、导航和本地链接有效。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

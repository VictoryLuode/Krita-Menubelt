#!/usr/bin/env bash
# verify.sh — 一条命令回答「这个仓现在可发布吗？」
#
#   ./verify.sh           全量：结构 + 版本 + 语法（本仓没有自动化测试）
#   ./verify.sh --quick   快速：同全量（此仓步骤本来就快）
#
# 退出码：0 = 全绿可发布；1 = 有失败。
#
# 三条纪律（动这个文件之前先读）：
#   1. 每个 gate 都必须真的能变红。永远绿的 gate 比没有 gate 更糟——它是对
#      坏代码的 ✓ 背书。加 gate 时故意弄坏一次，确认它红了，再改回来。
#   2. 本脚本是验证的唯一入口：本地跑它、发版前跑它、将来 CI 也只调它。
#   3. Krita 没有插件版本清单（pykrita/menubelt.desktop 里没有版本字段），
#      所以本仓的唯一版本真源就是 **git tag**，发版笔记是它的投影。
#
# ⚠️ 本仓目前没有自动化测试（Krita 插件需要一个真 Krita 宿主）。
#    这是最大的缺口：等你愿意时，用带 Krita 的 headless 会话补一个
#    tests/run_tests.sh，然后把它接到第 3 步。
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO"

for a in "$@"; do
  case "$a" in
    --quick) : ;;
    -h|--help) sed -n '2,4p' "$0"; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

failed=0
step() { printf '\n== %s\n' "$1"; }
pass() { printf '   ok   %s\n' "$1"; }
fail() { printf '   FAIL %s\n' "$1"; failed=1; }

PY="$(command -v python || command -v python3 || true)"

# --------------------------------------------------------- 1. 结构
step "1. plugin structure"
for f in pykrita/menubelt.desktop pykrita/menubelt/__init__.py actions/menubelt.action; do
  [ -f "$f" ] && pass "$f present" || fail "$f is missing"
done

# .desktop 必须能被 Krita 认出来
if [ -f pykrita/menubelt.desktop ] && grep -qE '^X-KDE-Library=menubelt' pykrita/menubelt.desktop; then
  pass "menubelt.desktop declares X-KDE-Library=menubelt"
else
  fail "menubelt.desktop must declare X-KDE-Library=menubelt"
fi

# 发布包里不该混进字节码缓存
if [ -n "$(find pykrita -name '__pycache__' -o -name '*.pyc' 2>/dev/null)" ]; then
  fail "pykrita/ contains __pycache__ or .pyc — they must not ship in the plugin"
else
  pass "no __pycache__ / .pyc under pykrita/"
fi

# --------------------------------------------------------- 2. 语法
step "2. syntax"
if [ -z "$PY" ]; then
  fail "no python on PATH — cannot check syntax"
else
  syntax_report="$("$PY" - <<'PYEOF' 2>&1
import ast, pathlib
bad = []
for p in sorted(pathlib.Path("pykrita").rglob("*.py")):
    try:
        ast.parse(p.read_text(encoding="utf-8"), str(p))
    except SyntaxError as e:
        bad.append(f"{p}:{e.lineno}: {e.msg}")
print("\n".join(bad))
PYEOF
)"
  [ -z "$syntax_report" ] && pass "all .py under pykrita/ parse" || fail "$syntax_report"
fi

# --------------------------------------------------------- 3. 版本（tag 是唯一真源）
step "3. version"
NOTES=""
for f in CHANGELOG.md RELEASE_NOTES.md; do
  if [ -f "$f" ]; then NOTES="$f"; break; fi
done
[ -n "$NOTES" ] && pass "release notes file: $NOTES" || fail "no CHANGELOG.md or RELEASE_NOTES.md"

latest_tag="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -z "$latest_tag" ]; then
  fail "no tag in this repository — the tag is the only version source here"
else
  pass "latest tag: $latest_tag"

  # 只对 HEAD 上的 tag 判红：历史 tag 已经发布、不可改，红它是噪音。
  # 发布时若打了 lightweight tag，这里会当场拦住。
  tags_here="$(git tag --points-at HEAD 2>/dev/null || true)"
  if [ -z "$tags_here" ]; then
    pass "HEAD carries no tag (pre-release state)"
  else
    for t in $tags_here; do
      if [ "$(git cat-file -t "$t" 2>/dev/null)" = "tag" ]; then
        pass "tag $t (on HEAD) is annotated"
      else
        fail "tag $t (on HEAD) is lightweight — git describe ignores those; re-tag with: git tag -a"
      fi
    done
  fi
fi

if [ -n "$PY" ] && [ -n "$NOTES" ] && [ -n "$latest_tag" ]; then
  verdict="$("$PY" - "$NOTES" "$latest_tag" <<'PYEOF' 2>&1
import re, sys, pathlib
text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
m = re.search(r"v?(\d+\.\d+\.\d+)", text)
if not m:
    sys.exit("no version in the notes file")
notes = tuple(int(x) for x in m.group(1).split("."))
tag = tuple(int(x) for x in re.sub(r"^[^\d]*", "", sys.argv[2]).split("."))
if notes < tag:
    sys.exit(f"notes say {m.group(1)} but the latest tag is {sys.argv[2]} (notes went backwards)")
print(f"notes {m.group(1)} >= tag {sys.argv[2]}")
PYEOF
)"
  case "$verdict" in
    "notes "*">= tag "*) pass "$verdict" ;;
    *) fail "$verdict" ;;
  esac
fi

# --------------------------------------------------------- 4. 打包依赖
step "4. packaging prerequisites"
if [ -f deploy.bat ]; then
  pass "deploy.bat present (deploys plugin files into the Krita resource dir)"
else
  fail "deploy.bat is missing"
fi
if [ -z "$PY" ]; then
  fail "no python on PATH — cannot check zip packaging"
else
  zip_ok="$("$PY" - <<'PYEOF' 2>&1
import pathlib, zipfile, io
buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as z:
    for p in sorted(pathlib.Path("pykrita").rglob("*")):
        if p.is_file():
            z.write(p, p.relative_to(".").as_posix())
print(f"ok {len(buf.getvalue())} bytes")
PYEOF
)"
  case "$zip_ok" in
    ok\ *) pass "pykrita/ packs into a zip ($(echo "$zip_ok" | cut -d' ' -f2-))" ;;
    *) fail "$zip_ok" ;;
  esac
fi

# --------------------------------------------------------- 汇总
echo
if [ "$failed" -eq 0 ]; then
  echo "VERIFY PASSED — this tree is releasable"
else
  echo "VERIFY FAILED"
fi
exit "$failed"

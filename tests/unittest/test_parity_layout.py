from pr_agent.algo.types import EDIT_TYPE, FilePatchInfo
from pr_agent.parity.config import ParityConfig
from pr_agent.parity.layout import (
    build_layout,
    detect_services,
    discover_languages,
    extract_identifiers,
    identifier_variants,
    rank_candidates,
    suggested_new_paths,
)

TREE = [
    "README.md",
    "src/shared/spec/retry.md",
    "src/typescript/src/http/retry.ts",
    "src/typescript/src/http/client.ts",
    "src/typescript/src/index.ts",
    "src/rust/src/http/retry.rs",
    "src/rust/src/http/client.rs",
    "src/rust/src/lib.rs",
    "src/golang/http/retry.go",
    "src/golang/http/client.go",
    "src/golang/http/retry_test.go",
    "src/python/polyglot/http/retry.py",
    "src/python/polyglot/http/client.py",
    "src/python/tests/test_retry.py",
    "src/kotlin/app/Retry.kt",
    "services/api/main.go",
    "services/worker/main.py",
    "docs/index.md",
]


def _patch(filename, patch="", edit_type=EDIT_TYPE.MODIFIED):
    return FilePatchInfo(base_file="", head_file="", patch=patch, filename=filename, edit_type=edit_type)


TS_PATCH = """@@ -1,4 +1,8 @@
-export function retryWithPolicy(fn, attempts) {
+export function retryWithPolicy(fn, attempts, maxBackoff = 8000) {
+  const computeDelay = (n) => Math.min(maxBackoff, 100 * 2 ** n);
"""


def test_config_defaults_and_flat_round_trip():
    cfg = ParityConfig()
    assert cfg.root == "src" and cfg.shared_dir == "src/shared"
    assert cfg.languages == ["typescript", "rust", "golang", "python"]
    flat = cfg.to_dict()
    assert set(flat) == set(ParityConfig.FIELDS)
    assert all(isinstance(v, (str, bool, int, list)) for v in flat.values())
    assert ParityConfig(**flat).to_dict() == flat


def test_config_normalises_dirs_and_languages():
    cfg = ParityConfig(root="/src/", shared_dir="src/shared/", languages=[" Rust ", "GoLang"],
                       max_candidates_per_language=0)
    assert cfg.root == "src" and cfg.shared_dir == "src/shared"
    assert cfg.languages == ["rust", "golang"]
    assert cfg.max_candidates_per_language == 1


def test_discover_languages_adds_source_bearing_dirs_but_not_shared():
    cfg = ParityConfig()
    assert discover_languages(cfg, TREE) == ["typescript", "rust", "golang", "python", "kotlin"]
    cfg = ParityConfig(auto_detect_languages=False)
    assert discover_languages(cfg, TREE) == ["typescript", "rust", "golang", "python"]


def test_bucketing_touched_missing_shared_outside():
    cfg = ParityConfig(auto_detect_languages=False)
    layout = build_layout(cfg, [
        _patch("src/typescript/src/http/retry.ts", TS_PATCH),
        _patch("src/shared/spec/retry.md"),
        _patch("docs/index.md"),
    ], TREE)
    assert [lang.language for lang in layout.touched_languages] == ["typescript"]
    assert [lang.language for lang in layout.missing_languages] == ["rust", "golang", "python"]
    assert [c.path for c in layout.shared_files] == ["src/shared/spec/retry.md"]
    assert [c.path for c in layout.outside_files] == ["docs/index.md"]
    assert layout.in_layout


def test_outside_only_pr_is_not_in_layout():
    cfg = ParityConfig()
    layout = build_layout(cfg, [_patch("docs/index.md"), _patch("README.md")], TREE)
    assert not layout.in_layout
    assert not layout.touched_languages


def test_identifiers_and_variants():
    ids = extract_identifiers([_patch("a.ts", TS_PATCH)])
    assert "retryWithPolicy" in ids and "computeDelay" in ids and "maxBackoff" in ids
    assert "export" not in ids and "const" not in ids
    assert {"retry_with_policy", "retrywithpolicy"} <= identifier_variants("retryWithPolicy")


def test_rank_candidates_prefers_same_relative_path_then_basename_and_penalises_tests():
    cfg = ParityConfig(auto_detect_languages=False)
    layout = build_layout(cfg, [_patch("src/typescript/src/http/retry.ts", TS_PATCH)], TREE)
    by_lang = {lang.language: lang for lang in layout.languages}
    # Rust mirrors the TS layout exactly: same relative path wins.
    assert by_lang["rust"].candidates[0].path == "src/rust/src/http/retry.rs"
    assert "same relative path" in by_lang["rust"].candidates[0].reasons
    # Go has a different layout: same basename wins; the test file is penalised out (no tests changed).
    go_paths = [c.path for c in by_lang["golang"].candidates]
    assert go_paths[0] == "src/golang/http/retry.go"
    assert "src/golang/http/retry_test.go" not in go_paths
    # Python: basename match.
    assert by_lang["python"].candidates[0].path == "src/python/polyglot/http/retry.py"


def test_rank_candidates_uses_file_content_for_identifier_hits():
    cfg = ParityConfig(auto_detect_languages=False, max_candidate_content_fetches=2)
    contents = {
        "src/rust/src/http/client.rs": "pub fn retry_with_policy(f: F, attempts: u32) {}",
        "src/rust/src/http/retry.rs": "// nothing relevant",
    }
    changed = build_layout(cfg, [_patch("src/typescript/src/http/retry.ts", TS_PATCH)], TREE).touched_languages[0]
    ids = extract_identifiers([_patch("x", TS_PATCH)])
    ranked = rank_candidates(cfg, "rust", TREE, changed.changed_files, ids, read_file=contents.get)
    hit = next(c for c in ranked if c.path == "src/rust/src/http/client.rs")
    assert "retryWithPolicy" in hit.identifier_hits
    assert any("identifier" in r for r in hit.reasons)


def test_rank_candidates_empty_language_dir_and_new_path_suggestion():
    cfg = ParityConfig(languages=["typescript", "rust", "elixir"], auto_detect_languages=False)
    layout = build_layout(cfg, [_patch("src/typescript/src/http/retry.ts", TS_PATCH)], TREE)
    elixir = next(lang for lang in layout.languages if lang.language == "elixir")
    assert elixir.candidates == []
    changed = layout.touched_languages[0].changed_files
    assert suggested_new_paths(cfg, "elixir", changed) == ["src/elixir/src/http/retry.ex"]
    assert suggested_new_paths(cfg, "rust", changed) == ["src/rust/src/http/retry.rs"]


def test_ignored_segments_are_skipped():
    cfg = ParityConfig(auto_detect_languages=False)
    tree = TREE + ["src/rust/target/debug/retry.rs", "src/typescript/node_modules/retry/retry.ts"]
    layout = build_layout(cfg, [_patch("src/typescript/src/http/retry.ts", TS_PATCH)], tree)
    rust = next(lang for lang in layout.languages if lang.language == "rust")
    assert all("target" not in c.path for c in rust.candidates)


def test_detect_services_and_touched():
    cfg = ParityConfig()
    assert detect_services(cfg, TREE) == ["services/api", "services/worker"]
    layout = build_layout(cfg, [_patch("services/api/main.go", "+x := 1\n")], TREE)
    assert layout.services_touched == {"services/api": ["services/api/main.go"]}
    cfg = ParityConfig(check_distribution=False)
    assert build_layout(cfg, [_patch("services/api/main.go")], TREE).services_all == []


def test_renamed_and_deleted_files_bucket_normally():
    cfg = ParityConfig(auto_detect_languages=False)
    layout = build_layout(cfg, [
        _patch("src/typescript/src/http/retry.ts", edit_type=EDIT_TYPE.DELETED),
    ], TREE)
    assert layout.touched_languages[0].changed_files[0].edit_type == EDIT_TYPE.DELETED
    rust = next(lang for lang in layout.languages if lang.language == "rust")
    assert rust.candidates[0].path == "src/rust/src/http/retry.rs"


def test_no_tree_degrades_to_no_candidates():
    cfg = ParityConfig(auto_detect_languages=False)
    layout = build_layout(cfg, [_patch("src/typescript/src/http/retry.ts", TS_PATCH)], [])
    assert [lang.language for lang in layout.missing_languages] == ["rust", "golang", "python"]
    assert all(lang.candidates == [] for lang in layout.missing_languages)

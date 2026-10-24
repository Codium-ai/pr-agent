import pytest

from pr_agent.tools.pr_help_docs import map_documentation_files_to_contents, return_document_headings


@pytest.mark.parametrize(
    ("extension", "content", "expected_heading"),
    [
        pytest.param(".md", "# 安裝說明\n\n請先準備開發環境。\n", "# 安裝說明", id="chinese-markdown"),
        pytest.param(".rst", "設定手順\n========\n\n説明を確認してください。\n", "設定手順", id="japanese-rst"),
        pytest.param(".md", "# Setup\n\nRead the instructions.\n", "# Setup", id="english-markdown"),
        pytest.param(".md", "# 12345\n\n--- 67890 !?\n", "", id="numbers-and-symbols"),
    ],
)
def test_documentation_text_detection(tmp_path, extension, content, expected_heading):
    document = tmp_path / f"guide{extension}"
    document.write_text(content, encoding="utf-8")

    assert return_document_headings(content, extension) == expected_heading
    expected_contents = {f"/{document.name}": content.strip()} if expected_heading else {}
    assert map_documentation_files_to_contents(str(tmp_path), [str(document)]) == expected_contents

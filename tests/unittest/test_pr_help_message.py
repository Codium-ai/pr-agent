import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from pr_agent.tools.pr_help_message import PRHelpMessage, extract_header


def test_extract_header():
    # Test with valid header
    snippet = "Header 1: Test\n===Snippet content==="
    assert extract_header(snippet) == "#test"
    
    # Test with no header
    snippet = "Some content\n===Snippet content==="
    assert extract_header(snippet) == ""
    
    # Test with multiple headers (should take first header in reversed list)
    snippet = "Header 1: First\nHeader 2: Last\n===Snippet content==="
    assert extract_header(snippet) == "#first"


@pytest.fixture
def mock_git_provider():
    mock = Mock()
    mock.pr_url = "https://github.com/test/repo/pull/1"
    return mock


@pytest.mark.asyncio
@patch("pr_agent.tools.pr_help_message.get_git_provider_with_context")
@patch("pr_agent.tools.pr_help_message.get_settings")
async def test_pr_help_message_init(mock_get_settings, mock_get_provider, mock_git_provider):
    # Setup
    mock_get_provider.return_value = mock_git_provider
    mock_get_settings.return_value.get.return_value = 5
    mock_ai_handler = Mock()
    
    # Test initialization with question
    help_msg = PRHelpMessage("test_url", args=["test", "question"], ai_handler=mock_ai_handler)
    
    assert help_msg.question_str == "test question"
    assert help_msg.git_provider == mock_git_provider
    assert help_msg.num_retrieved_snippets == 5
    assert help_msg.vars == {
        "question": "test question",
        "snippets": ""
    }


@pytest.mark.asyncio
@patch("pr_agent.tools.pr_help_message.get_git_provider_with_context")
@patch("pr_agent.tools.pr_help_message.get_settings")
async def test_pr_help_message_run_no_openai_key(mock_get_settings, mock_get_provider, mock_git_provider):
    # Setup
    mock_get_provider.return_value = mock_git_provider
    mock_get_settings.return_value.get.side_effect = [5, None]  # num_snippets, openai key
    mock_get_settings.return_value.config.publish_output = True
    
    help_msg = PRHelpMessage("test_url", args=["test"], ai_handler=Mock())
    
    # Test run with no OpenAI key
    await help_msg.run()
    
    mock_git_provider.publish_comment.assert_called_once_with(
        "The `Help` tool chat feature requires an OpenAI API key for calculating embeddings"
    )
import pytest
from unittest.mock import MagicMock, patch

from pr_agent.tools.pr_help_message import PRHelpMessage, extract_header


@pytest.fixture
def mock_git_provider():
    mock = MagicMock()
    mock.pr_url = "https://github.com/test/repo/pull/1"
    mock.publish_comment = MagicMock()
    return mock


@pytest.fixture
def mock_ai_handler():
    mock = MagicMock()
    mock.chat_completion = MagicMock(return_value=("test response", None))
    return mock


def test_extract_header():
    # Test extracting header from snippet
    snippet = "Header 1: Test Header\n===Snippet content===\nSome content"
    result = extract_header(snippet)
    assert result == "#test-header"

    # Test with no header
    snippet = "===Snippet content===\nSome content"
    result = extract_header(snippet)
    assert result == ""

    # Test with multiple headers - should take first one
    snippet = "Header 1: First Header\nHeader 2: Second Header\n===Snippet content===\nSome content"
    result = extract_header(snippet)
    assert result == "#first-header"


@patch('pr_agent.tools.pr_help_message.get_git_provider_with_context')
def test_pr_help_message_init(mock_get_provider, mock_git_provider, mock_ai_handler):
    mock_get_provider.return_value = mock_git_provider
    
    # Test initialization with question
    help_msg = PRHelpMessage("https://github.com/test/repo/pull/1", args=["test", "question"], ai_handler=lambda: mock_ai_handler)
    assert help_msg.question_str == "test question"
    assert help_msg.git_provider == mock_git_provider
    assert help_msg.ai_handler == mock_ai_handler

    # Test initialization without question
    help_msg = PRHelpMessage("https://github.com/test/repo/pull/1", args=None, ai_handler=lambda: mock_ai_handler)
    assert help_msg.question_str == ""

@patch('pr_agent.tools.pr_help_message.get_git_provider_with_context')
@pytest.mark.asyncio
async def test_run_no_question(mock_get_provider, mock_git_provider, mock_ai_handler):
    mock_get_provider.return_value = mock_git_provider
    help_msg = PRHelpMessage("https://github.com/test/repo/pull/1", args=None, ai_handler=lambda: mock_ai_handler)
    
    mock_git_provider.is_supported.return_value = False
    mock_git_provider.__class__ = type('MockProvider', (), {'__name__': 'NotBitbucketServerProvider'})
    
    await help_msg.run()
    
    mock_git_provider.publish_comment.assert_called_once_with(
        "The `Help` tool requires gfm markdown, which is not supported by your code platform."
    )


@patch('pr_agent.tools.pr_help_message.get_git_provider_with_context')
@pytest.mark.asyncio
async def test_prepare_prediction_error(mock_get_provider, mock_git_provider, mock_ai_handler):
    mock_get_provider.return_value = mock_git_provider
    help_msg = PRHelpMessage("https://github.com/test/repo/pull/1", args=["test", "question"], ai_handler=lambda: mock_ai_handler)
    
    mock_ai_handler.chat_completion.side_effect = Exception("AI model error")
    response = await help_msg._prepare_prediction("gpt-4")
    
    assert response == ""

@patch('pr_agent.tools.pr_help_message.get_settings')
@patch('pr_agent.tools.pr_help_message.get_git_provider_with_context')
@pytest.mark.asyncio
async def test_run_no_openai_key_no_publish(mock_get_provider, mock_settings, mock_git_provider, mock_ai_handler):
    mock_get_provider.return_value = mock_git_provider
    mock_settings.return_value.get.return_value = None
    mock_settings.return_value.config.publish_output = False
    
    help_msg = PRHelpMessage("https://github.com/test/repo/pull/1", args=["test question"], ai_handler=lambda: mock_ai_handler)
    await help_msg.run()
    
    mock_git_provider.publish_comment.assert_not_called()


@patch('pr_agent.tools.pr_help_message.get_settings')
@patch('pr_agent.tools.pr_help_message.get_git_provider_with_context')
@pytest.mark.asyncio  
async def test_run_no_openai_key(mock_get_provider, mock_settings, mock_git_provider, mock_ai_handler):
    mock_get_provider.return_value = mock_git_provider
    mock_settings.return_value.get.return_value = None
    mock_settings.return_value.config.publish_output = True
    
    help_msg = PRHelpMessage("https://github.com/test/repo/pull/1", args=["test question"], ai_handler=lambda: mock_ai_handler)
    await help_msg.run()
    
    mock_git_provider.publish_comment.assert_called_once_with(
        "The `Help` tool chat feature requires an OpenAI API key for calculating embeddings"
    )


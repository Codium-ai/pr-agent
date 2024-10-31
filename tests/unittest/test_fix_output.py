# Generated by CodiumAI

from pr_agent.algo.utils import try_fix_json


from pr_agent.algo.utils import unique_strings
from pr_agent.algo.utils import emphasize_header
class TestTryFixJson:
    # Tests that JSON with complete 'Code suggestions' section returns expected output
    def test_incomplete_code_suggestions(self):
        review = '{"PR Analysis": {"Main theme": "xxx", "Type of PR": "Bug fix"}, "PR Feedback": {"General PR suggestions": "..., `xxx`...", "Code suggestions": [{"relevant file": "xxx.py", "suggestion content": "xxx [important]"}, {"suggestion number": 2, "relevant file": "yyy.py", "suggestion content": "yyy [incomp...'  # noqa: E501
        expected_output = {
            'PR Analysis': {
                'Main theme': 'xxx',
                'Type of PR': 'Bug fix'
            },
            'PR Feedback': {
                'General PR suggestions': '..., `xxx`...',
                'Code suggestions': [
                    {
                        'relevant file': 'xxx.py',
                        'suggestion content': 'xxx [important]'
                    }
                ]
            }
        }
        assert try_fix_json(review) == expected_output

    def test_incomplete_code_suggestions_new_line(self):
        review = '{"PR Analysis": {"Main theme": "xxx", "Type of PR": "Bug fix"}, "PR Feedback": {"General PR suggestions": "..., `xxx`...", "Code suggestions": [{"relevant file": "xxx.py", "suggestion content": "xxx [important]"} \n\t, {"suggestion number": 2, "relevant file": "yyy.py", "suggestion content": "yyy [incomp...'  # noqa: E501
        expected_output = {
            'PR Analysis': {
                'Main theme': 'xxx',
                'Type of PR': 'Bug fix'
            },
            'PR Feedback': {
                'General PR suggestions': '..., `xxx`...',
                'Code suggestions': [
                    {
                        'relevant file': 'xxx.py',
                        'suggestion content': 'xxx [important]'
                    }
                ]
            }
        }
        assert try_fix_json(review) == expected_output

    def test_incomplete_code_suggestions_many_close_brackets(self):
        review = '{"PR Analysis": {"Main theme": "xxx", "Type of PR": "Bug fix"}, "PR Feedback": {"General PR suggestions": "..., `xxx`...", "Code suggestions": [{"relevant file": "xxx.py", "suggestion content": "xxx [important]"} \n, {"suggestion number": 2, "relevant file": "yyy.py", "suggestion content": "yyy }, [}\n ,incomp.}  ,..'  # noqa: E501
        expected_output = {
            'PR Analysis': {
                'Main theme': 'xxx',
                'Type of PR': 'Bug fix'
            },
            'PR Feedback': {
                'General PR suggestions': '..., `xxx`...',
                'Code suggestions': [
                    {
                        'relevant file': 'xxx.py',
                        'suggestion content': 'xxx [important]'
                    }
                ]
            }
        }
        assert try_fix_json(review) == expected_output

    def test_incomplete_code_suggestions_relevant_file(self):
        review = '{"PR Analysis": {"Main theme": "xxx", "Type of PR": "Bug fix"}, "PR Feedback": {"General PR suggestions": "..., `xxx`...", "Code suggestions": [{"relevant file": "xxx.py", "suggestion content": "xxx [important]"}, {"suggestion number": 2, "relevant file": "yyy.p'  # noqa: E501
        expected_output = {
            'PR Analysis': {
                'Main theme': 'xxx',
                'Type of PR': 'Bug fix'
            },
            'PR Feedback': {
                'General PR suggestions': '..., `xxx`...',
                'Code suggestions': [
                    {
                        'relevant file': 'xxx.py',
                        'suggestion content': 'xxx [important]'
                    }
                ]
            }
        }
        assert try_fix_json(review) == expected_output

    def test_unique_strings_empty_list(self):
        input_list = []
        expected_output = []
        assert unique_strings(input_list) == expected_output


    def test_unique_strings_all_unique(self):
        input_list = ["apple", "banana", "cherry"]
        expected_output = ["apple", "banana", "cherry"]
        assert unique_strings(input_list) == expected_output


    def test_emphasize_header_no_colon(self):
        text = "Header without colon"
        result = emphasize_header(text)
        assert result == text


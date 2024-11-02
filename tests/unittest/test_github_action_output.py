import os
import json
from pr_agent.algo.utils import get_settings, github_action_output

class TestGitHubOutput:
    def test_github_action_output_enabled(self, monkeypatch, tmp_path):
        get_settings().set('GITHUB_ACTION_CONFIG.ENABLE_OUTPUT', True)
        monkeypatch.setenv('GITHUB_OUTPUT', str(tmp_path / 'output'))
        output_data = {'key1': {'value1': 1, 'value2': 2}}
        key_name = 'key1'
        
        github_action_output(output_data, key_name)
        
        with open(str(tmp_path / 'output'), 'r') as f:
            env_value = f.read()
        
        actual_key = env_value.split('=')[0]
        actual_data = json.loads(env_value.split('=')[1])
        
        assert actual_key == key_name
        assert actual_data == output_data[key_name]
    
    def test_github_action_output_disabled(self, monkeypatch, tmp_path):
        get_settings().set('GITHUB_ACTION_CONFIG.ENABLE_OUTPUT', False)
        monkeypatch.setenv('GITHUB_OUTPUT', str(tmp_path / 'output'))
        output_data = {'key1': {'value1': 1, 'value2': 2}}
        key_name = 'key1'
        
        github_action_output(output_data, key_name)
        
        assert not os.path.exists(str(tmp_path / 'output'))

    def test_github_action_output_notset(self, monkeypatch, tmp_path):
        # not set config
        monkeypatch.setenv('GITHUB_OUTPUT', str(tmp_path / 'output'))
        output_data = {'key1': {'value1': 1, 'value2': 2}}
        key_name = 'key1'
        
        github_action_output(output_data, key_name)
        
        assert not os.path.exists(str(tmp_path / 'output'))
    
    def test_github_action_output_error_case(self, monkeypatch, tmp_path):
        monkeypatch.setenv('GITHUB_OUTPUT', str(tmp_path / 'output'))
        output_data = None # invalid data
        key_name = 'key1'
        
        github_action_output(output_data, key_name)
        
        assert not os.path.exists(str(tmp_path / 'output'))

    def test_clip_tokens_exceeds_max_with_dots_and_delete(self):
        from pr_agent.algo.utils import clip_tokens
    
        text = "This is a sample text that will be clipped because it exceeds the maximum number of allowed tokens."
        max_tokens = 10
        expected_output_start = "This is a sample text that will be clipped because it exceeds the ma..."
        # Since the exact clipping depends on the TokenEncoder, we check the presence of truncation
        result = clip_tokens(text, max_tokens, add_three_dots=True, delete_last_line=True)
        assert result.endswith("...(truncated)")
        assert len(result) <= len(text)

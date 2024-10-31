import os
import json
from pr_agent.algo.utils import get_settings, github_action_output
from pr_agent.algo.utils import get_max_tokens
from pr_agent.algo.utils import emphasize_header
from pr_agent.algo.utils import try_fix_json

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

    def test_get_max_tokens_custom_model(self):
        from pr_agent.config_loader import get_settings
        custom_model = "custom-model"
        get_settings().set('config.custom_model_max_tokens', 1000)
        result = get_max_tokens(custom_model)
        assert result == 1000
        get_settings().set('config.custom_model_max_tokens', -1)  # Reset


    def test_emphasize_header_error(self):
        from pr_agent.log import get_logger
        text = None  # Invalid input that should trigger exception
        result = emphasize_header(text)
        assert result == text  # Should return input unchanged on error


    def test_try_fix_json_with_code_suggestions(self):
        broken_json = '''{"review": {}, "Code feedback": [
            {"suggestion": "test1"},
            {"suggestion": "test2"},
            {"suggestion": "test3"}, 
        '''
        result = try_fix_json(broken_json, code_suggestions=True)
        assert isinstance(result, dict)
        assert "review" in result

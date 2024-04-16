MAX_TOKENS = {
    'text-embedding-ada-002': 8000,
    'gpt-3.5-turbo': 4000,
    'gpt-3.5-turbo-0613': 4000,
    'gpt-3.5-turbo-0301': 4000,
    'gpt-3.5-turbo-16k': 16000,
    'gpt-3.5-turbo-16k-0613': 16000,
    'gpt-4': 8000,
    'gpt-4-0613': 8000,
    'gpt-4-32k': 32000,
    'gpt-4-1106-preview': 128000, # 128K, but may be limited by config.max_model_tokens
    'gpt-4-0125-preview': 128000,  # 128K, but may be limited by config.max_model_tokens
    'gpt-4-turbo-preview': 128000,  # 128K, but may be limited by config.max_model_tokens
    'gpt-4-turbo-2024-04-09': 128000,  # 128K, but may be limited by config.max_model_tokens
    'gpt-4-turbo': 128000,  # 128K, but may be limited by config.max_model_tokens
    'claude-instant-1': 100000,
    'claude-2': 100000,
    'command-nightly': 4096,
    'replicate/llama-2-70b-chat:2c1608e18606fad2812020dc541930f2d0495ce32eee50074220b87300bc16e1': 4096,
    'meta-llama/Llama-2-7b-chat-hf': 4096,
    'vertex_ai/codechat-bison': 6144,
    'vertex_ai/codechat-bison-32k': 32000,
    'codechat-bison': 6144,
    'codechat-bison-32k': 32000,
    'anthropic.claude-instant-v1': 100000,
    'anthropic.claude-v1': 100000,
    'anthropic.claude-v2': 100000,
    'anthropic/claude-3-opus-20240229': 100000,
    'bedrock/anthropic.claude-instant-v1': 100000,
    'bedrock/anthropic.claude-v2': 100000,
    'bedrock/anthropic.claude-v2:1': 100000,
    'bedrock/anthropic.claude-3-sonnet-20240229-v1:0': 100000,
    'bedrock/anthropic.claude-3-haiku-20240307-v1:0': 100000,
}

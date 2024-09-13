MAX_TOKENS = {
    'text-embedding-ada-002': 8000,
    'gpt-3.5-turbo': 16000,
    'gpt-3.5-turbo-0125': 16000,
    'gpt-3.5-turbo-0613': 4000,
    'gpt-3.5-turbo-1106': 16000,
    'gpt-3.5-turbo-16k': 16000,
    'gpt-3.5-turbo-16k-0613': 16000,
    'gpt-4': 8000,
    'gpt-4-0613': 8000,
    'gpt-4-32k': 32000,
    'gpt-4-1106-preview': 128000,  # 128K, but may be limited by config.max_model_tokens
    'gpt-4-0125-preview': 128000,  # 128K, but may be limited by config.max_model_tokens
    'gpt-4o': 128000,  # 128K, but may be limited by config.max_model_tokens
    'gpt-4o-2024-05-13': 128000,  # 128K, but may be limited by config.max_model_tokens
    'gpt-4-turbo-preview': 128000,  # 128K, but may be limited by config.max_model_tokens
    'gpt-4-turbo-2024-04-09': 128000,  # 128K, but may be limited by config.max_model_tokens
    'gpt-4-turbo': 128000,  # 128K, but may be limited by config.max_model_tokens
    'gpt-4o-mini': 128000,  # 128K, but may be limited by config.max_model_tokens
    'gpt-4o-mini-2024-07-18': 128000,  # 128K, but may be limited by config.max_model_tokens
    'gpt-4o-2024-08-06': 128000,  # 128K, but may be limited by config.max_model_tokens
    'o1-mini': 128000,  # 128K, but may be limited by config.max_model_tokens
    'o1-mini-2024-09-12': 128000,  # 128K, but may be limited by config.max_model_tokens
    'o1-preview': 128000,  # 128K, but may be limited by config.max_model_tokens
    'o1-preview-2024-09-12': 128000,  # 128K, but may be limited by config.max_model_tokens
    'claude-instant-1': 100000,
    'claude-2': 100000,
    'command-nightly': 4096,
    'replicate/llama-2-70b-chat:2c1608e18606fad2812020dc541930f2d0495ce32eee50074220b87300bc16e1': 4096,
    'meta-llama/Llama-2-7b-chat-hf': 4096,
    'vertex_ai/codechat-bison': 6144,
    'vertex_ai/codechat-bison-32k': 32000,
    'vertex_ai/claude-3-haiku@20240307': 100000,
    'vertex_ai/claude-3-sonnet@20240229': 100000,
    'vertex_ai/claude-3-opus@20240229': 100000,
    'vertex_ai/claude-3-5-sonnet@20240620': 100000,
    'vertex_ai/gemini-1.5-pro': 1048576,
    'vertex_ai/gemini-1.5-flash': 1048576,
    'vertex_ai/gemma2': 8200,
    'codechat-bison': 6144,
    'codechat-bison-32k': 32000,
    'anthropic.claude-instant-v1': 100000,
    'anthropic.claude-v1': 100000,
    'anthropic.claude-v2': 100000,
    'anthropic/claude-3-opus-20240229': 100000,
    'anthropic/claude-3-5-sonnet-20240620': 100000,
    'bedrock/anthropic.claude-instant-v1': 100000,
    'bedrock/anthropic.claude-v2': 100000,
    'bedrock/anthropic.claude-v2:1': 100000,
    'bedrock/anthropic.claude-3-sonnet-20240229-v1:0': 100000,
    'bedrock/anthropic.claude-3-haiku-20240307-v1:0': 100000,
    'bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0': 100000,
    'claude-3-5-sonnet': 100000,
    'groq/llama3-8b-8192': 8192,
    'groq/llama3-70b-8192': 8192,
    'groq/mixtral-8x7b-32768': 32768,
    'groq/llama-3.1-8b-instant': 131072,
    'groq/llama-3.1-70b-versatile': 131072,
    'groq/llama-3.1-405b-reasoning': 131072,
    'ollama/llama3': 4096,
    'watsonx/meta-llama/llama-3-8b-instruct': 4096,
    "watsonx/meta-llama/llama-3-70b-instruct": 4096,
    "watsonx/meta-llama/llama-3-405b-instruct": 16384,
    "watsonx/ibm/granite-13b-chat-v2": 8191,
    "watsonx/ibm/granite-34b-code-instruct": 8191,
    "watsonx/mistralai/mistral-large": 32768,
}

import aiohttp
from tenacity import retry


from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger

API_RETRIES = 5

class MultiplierAIHandler(BaseAiHandler):
    def __init__(self):
        try:
            super().__init__()
            self.base_url = "http://localhost:8080/api/agent"
        except Exception as e:
            raise ValueError("Failed to initialize MultiplierAIHandler") from e

    @retry(exceptions=(aiohttp.ClientError, aiohttp.ServerTimeoutError), 
           tries=API_RETRIES, delay=2, backoff=2, jitter=(1, 3))
    async def chat_completion(self, system: str, user: str, temperature: float = 0.2):
        """
        Interact with the Multiplier AI API to get a response.
        """
        try:
            get_logger().info("Sending request to Multiplier AI API")
            payload = {
                "system": system,
                "user": user,
                "temperature": temperature,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=payload) as response:
                    if response.status != 200:
                        error_message = f"Multiplier AI API returned error: {response.status}"
                        get_logger().error(error_message)
                        raise ValueError(error_message)
                    
                    data = await response.json()

                    # Assuming the API returns 'response' and 'stopReason'
                    ai_response = data.get("response", "")
                    stop_reason = data.get("stopReason", "")
                    
                    get_logger().info("AI Response Received", response=ai_response, stop_reason=stop_reason)
                    return ai_response, stop_reason
        except aiohttp.ClientError as e:
            get_logger().error("Client error during Multiplier AI API call: ", e)
            raise
        except Exception as e:
            get_logger().error("Unknown error during Multiplier AI API call: ", e)
            raise

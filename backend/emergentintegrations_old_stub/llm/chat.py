class UserMessage:
    def __init__(self, text: str):
        self.text = text

class _ChatResponse:
    def __init__(self, text: str):
        self.text = text

class LlmChat:
    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key
        self.model = model

    async def send_message(self, message: UserMessage, system_prompt: str = ""):
        # Development stub: return a placeholder response
        return _ChatResponse(text="[stub] AI response not configured. Add real emergentintegrations package for live outputs.")

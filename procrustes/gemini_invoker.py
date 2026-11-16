# ------------------------------------------------------------------------------------------
# gemini_invoker
# ------------------------------------------------------------------------------------------

from google.genai import types


# ------------------------------------------------------------------------------------------

_GEMINI_THINKING_LEVEL = {
    "high": types.ThinkingLevel.HIGH,
    "medium": types.ThinkingLevel.MEDIUM,
    "low": types.ThinkingLevel.LOW,
    "none": types.ThinkingLevel.MINIMAL,
    "minimal": types.ThinkingLevel.MINIMAL,}

# ------------------------------------------------------------------------------------------

def template_to_string_schema(template: list) -> dict:
    return {
        "type": "object",
        "properties": {
            x: {"type": "string"} for x in template
        },
        "required": template,
        "additionalProperties": False,
    }

# ------------------------------------------------------------------------------------------

class Gemini_Invoker:

    def __init__(self, client,
                 entries,
                 instructions,
                 model,
                 reasoning,
                 verbosity,
                 temperature,
                 top_p):

        self.client = client
        self.entries = entries
        self.instructions = instructions
        self.model = model
        self.verbosity = None # Gemini has no verbosity level
        self.temperature = temperature
        self.top_p = top_p

        if reasoning:
            self.reasoning = _GEMINI_THINKING_LEVEL.get((reasoning or "none").lower(),
                                                         types.ThinkingLevel.MINIMAL)
        else:
            self.reasoning = None
            

    def invoke(self, prompt, instructions = None):

        instructions = self.instructions if instructions is None else instructions

        response = self.client.models.generate_content(
            model = self.model,
            contents = [
                        types.Part.from_bytes(
                            data = prompt,
                            mime_type = "application/pdf",),
                        ],
            config = types.GenerateContentConfig(
                system_instruction = instructions,
                **({"thinking_config": types.ThinkingConfig(thinking_level = self.reasoning)}
                   if self.reasoning is not None else {}),
                **({"temperature": self.temperature} if self.temperature is not None else {}),
                **({"top_p": self.top_p} if self.top_p is not None else {}),
                **{
                    "response_mime_type": "application/json",
                    "response_json_schema": template_to_string_schema(self.entries),
                }
            )
        )
        return response.parsed

# ------------------------------------------------------------------------------------------

    def __getstate__(self):
        """Return picklable state (drop the LLM client)."""
        state = self.__dict__.copy()
        # client is not picklable
        state['client'] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.client = None  # PromptGateway will re-bind client

    def bind_client(self, client): # PromptGateway uses this to re-bind client
        self.client = client
        
# ------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------
# gpt_invoker
# ------------------------------------------------------------------------------------------

import json
import base64

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

class GPT_Invoker:

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
        self.verbosity = verbosity
        self.temperature = temperature
        self.top_p = top_p
        self.reasoning = reasoning

    def invoke(self, prompt,
               instructions = None):

        instructions = self.instructions if instructions is None else instructions

        base64_pdf = base64.b64encode(prompt).decode("utf-8")

        response = self.client.responses.create(
                model = self.model,
                instructions = instructions,
                input = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_file",
                                "filename": "page.pdf",
                                "file_data": f"data:application/pdf;base64,{base64_pdf}",
                            }
                        ],
                    }
                ],
                **({"reasoning": {"effort": self.reasoning}} if self.reasoning is not None else {}),
                text = {
                    **({"verbosity": self.verbosity} if self.verbosity is not None else {}),
                        "format": {
                                    "type": "json_schema",
                                    "name": "template_response",
                                    "strict": True,
                                    "schema": template_to_string_schema(self.entries),
                                    },
                        },
                **({"temperature": self.temperature} if self.temperature is not None else {}),
                **({"top_p": self.top_p} if self.top_p is not None else {})
                )
        return json.loads(response.output_text)
            
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

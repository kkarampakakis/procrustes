# ------------------------------------------------------------------------------------------
# prompt_gateway
# ------------------------------------------------------------------------------------------

# potential imports:
# from openai import OpenAI
# from google.genai import Client
# from .gpt_invoker import GPT_Invoker
# from .gemini_invoker import Gemini_Invoker

from pathlib import Path

from . import instructors

# ------------------------------------------------------------------------------------------

GPT_MODELS = ("o1", "o1-mini", "o1-pro",
              "o3", "o3-deep-research", "o4-mini-deep-research",
              "o4-mini")

GEMINI_MODELS = ()

NO_API_KEY_ERROR = "Error: No API key in file."

package_folder = Path(__file__).resolve().parent
parent_folder = package_folder.parent

# ------------------------------------------------------------------------------------------

class PromptGateway:

    def __init__(self, settings):

        self.settings = settings

        self.openai_client = None
        self.google_client = None
        
        self.inquiror = self.create_invoker(
            self.settings["inquiror"],
            self.settings["general"]["entries"],
            instructors.instruct_inquiry(self.settings["general"]["language"],
                                         self.settings["general"]["context_guidelines"]))
        
    
    def create_structure_builder_invoker(self):
        """Create a field-discovery invoker using the existing model settings."""
        return self.create_invoker(
            self.settings["inquiror"],
            ["entries"],
            instructors.instruct_structure(
                self.settings["general"]["language"],
                self.settings["general"].get("context_guidelines", ""),
            ),
        )

    def create_invoker(self, x, entries, instructions):
        if x["model"] in GPT_MODELS or x["model"].startswith("gpt"):
            from .gpt_invoker import GPT_Invoker
            return GPT_Invoker(
                        self.create_client(x["model"]),
                        entries,
                        instructions,
                        x["model"],
                        (x["reasoning"] if x["reasoning"] is not False else None),
                        (x["verbosity"] if x["verbosity"] is not False else None),
                        (x["temperature"] if x["temperature"] is not False else None),
                        (x["top_p"] if x["top_p"] is not False else None))

        elif x["model"] in GEMINI_MODELS or x["model"].startswith("gemini"):
            from .gemini_invoker import Gemini_Invoker
            return Gemini_Invoker(
                        self.create_client(x["model"]),
                        entries,
                        instructions,
                        x["model"],
                        (x["reasoning"] if x["reasoning"] is not False else None),
                        (x["verbosity"] if x["verbosity"] is not False else None),
                        (x["temperature"] if x["temperature"] is not False else None),
                        (x["top_p"] if x["top_p"] is not False else None))
        else:
            raise ValueError("Error: Unknown LLM model.")
                             
    def create_client(self, model):
        
        if model in GPT_MODELS or model.startswith("gpt"):
            if self.openai_client is None:
                if self.settings["api_serial_keys"]["openai"].lower().endswith(".txt"):
                    key_path = parent_folder / self.settings["api_serial_keys"]["openai"].strip()
                    with open(key_path, "r", encoding="utf-8") as f:
                        api_key = f.read().strip()
                        if not api_key:
                            raise ValueError(NO_API_KEY_ERROR)
                else:
                    api_key = self.settings["api_serial_keys"]["openai"].strip()
                    if not api_key:
                        raise ValueError(NO_API_KEY_ERROR)
                from openai import OpenAI
                self.openai_client = OpenAI(api_key = api_key)
            client = self.openai_client

        elif model in GEMINI_MODELS or model.startswith("gemini"):
            if self.google_client is None:
                if self.settings["api_serial_keys"]["google"].lower().endswith(".txt"):
                    key_path = parent_folder / self.settings["api_serial_keys"]["google"].strip()
                    with open(key_path, "r", encoding="utf-8") as f:
                        api_key = f.read().strip()
                        if not api_key:
                            raise ValueError(NO_API_KEY_ERROR)
                else:
                    api_key = self.settings["api_serial_keys"]["google"].strip()
                    if not api_key:
                        raise ValueError(NO_API_KEY_ERROR)
                from google.genai import Client
                self.google_client = Client(api_key = api_key)
            client = self.google_client

        else:
            raise ValueError(f"Unknown model in settings: {model}")

        return client

    def __getstate__(self):
        """Return picklable state (drop the LLM clients)."""
        state = self.__dict__.copy()
        # client is not picklable
        state.pop("openai_client", None)
        state.pop("google_client", None)
        return state


    def __setstate__(self, state):
        """Restore state and recreate the LLM clients."""
        self.__dict__.update(state)
        # empty possible old clients:
        self.openai_client = None
        self.google_client = None
        # re-bind invoker to the client creating new clients on the way:
        self.inquiror.bind_client(self.create_client(self.inquiror.model))

# ------------------------------------------------------------------------------------------

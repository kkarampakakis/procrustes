"""Discover entry names from PDF pages without extracting their values.

StructureBuilder shares the PDF traversal and checkpointing contract of Iterator,
but collects field labels rather than answers to predefined questions.
"""

from .iterator import Iterator, metadata_to_bytes

STRUCTURE_PICKLE_NAME = "procrustean_structure.pkl"
STRUCTURE_CSV_NAME = "procrustean_structure"


class StructureBuilder(Iterator):
    """Create blank slots for fields discovered throughout the source PDFs.

    The model returns a JSON object containing an ``entries`` string. Each line
    names one field. Labels are case-insensitively deduplicated across pages;
    their first spelling and discovery order are preserved.
    """

    def __init__(self, gate):
        super().__init__(gate)
        # The builder deliberately does not seed slots from settings.toml:
        # its purpose is to discover the structure of the documents.
        self.filled_entries = {}
        self.builder = gate.create_structure_builder_invoker()

    def save_as_pickle(self):
        """Save to a distinct file so regular inquiry progress is untouched."""
        import pickle

        with open(STRUCTURE_PICKLE_NAME, "wb") as checkpoint:
            pickle.dump(self, checkpoint)

    def __setstate__(self, state):
        """Reconnect the discovery invoker after restoring a checkpoint.

        PromptGateway already restores its regular inquiry invoker during
        unpickling; the separate structure invoker needs its own binding.
        """
        self.__dict__.update(state)
        if self.builder is not None:
            self.builder.bind_client(self.gate.create_client(self.builder.model))

    @staticmethod
    def parse_entries(response):
        """Parse the builder's strict JSON response into clean entry labels.

        Entries are one per line, optionally prefixed with a common list marker.
        Invalid non-string API results raise an error rather than losing data.
        """
        if not isinstance(response, dict) or not isinstance(response.get("entries"), str):
            raise ValueError("Structure builder must return a JSON object with an 'entries' string")

        labels = []
        for line in response["entries"].splitlines():
            label = line.strip()
            if label.startswith(("- ", "* ", "• ")):
                label = label[2:].strip()
            if not label or label == "-":
                continue
            labels.append(label)
        return labels

    def resume_inquiry(self):
        """Read remaining pages, adding blank fields and saving after each one."""
        length = len(self.pages)
        if not length:
            print("No PDF files found.")
            return

        for page_index in range(self.i, length):
            print(f"{(self.i / length) * 100:.2f}% completed")
            response = self.builder.invoke(metadata_to_bytes(self.pages[page_index]))
            known = {name.casefold() for name in self.filled_entries}
            for name in self.parse_entries(response):
                normalized = name.casefold()
                if normalized not in known:
                    self.filled_entries[name] = []
                    known.add(normalized)

            self.i += 1
            self.save_as_pickle()

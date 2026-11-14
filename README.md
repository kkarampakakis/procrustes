\# Procrustes
========================


An LLM-assisted tool for structured PDF inquiry.


It reads PDF files page by page, asks an LLM to extract requested information, and writes the results into a CSV file.


\ Procrustes is experimental software (Beta).
========================

This project is under development and is made publicly available for research, experimentation, and educational purposes.

Current limitations:

The software has not undergone comprehensive automated testing.

Bugs, unexpected behavior, and incomplete functionality may be present.

Installation and execution may require additional configuration or troubleshooting.

PDF contents may be transmitted to third-party AI service providers (OpenAI or Google Gemini) during processing.

The software uses Python pickle serialization. Users should not load pickle files from untrusted sources.

Use at your own risk. Do not rely on this software for critical workflows or process sensitive or confidential documents without independently assessing its security, privacy, and reliability.

Contributions, bug reports, and suggestions are welcome.


\## What it does
========================


Procrustes:



\- scans all `.pdf` files in the current working folder

\- splits them internally page by page

\- sends each page to an LLM

\- asks the LLM to fill predefined entries

\- saves results in `procrustean\_output.csv`

\- saves progress in `procrustean\_pickle.pkl`

\- can resume after interruption



\## Installation
========================


From the project folder, run:



```bash

python -m pip install -e .

````



Or, for a normal install:



```bash

python -m pip install .

```



\## Requirements
========================


Procrustes requires Python 3.11 or newer.



Runtime dependencies:



```text

openai

google-genai

pypdf

```



These are installed automatically if `pyproject.toml` is configured correctly.



\## Settings
========================


Procrustes uses a `settings.toml` file.



To create or open it, run:



```bash

procrustes open-settings

```



If `settings.toml` does not exist, Procrustes creates it from `default\_settings.toml`.



To reset `settings.toml` back to the default version, run:



```bash

procrustes reset

```



\## API keys
========================


Procrustes runs using LLM models from OpenAI or Google Gemini.
You need an API key from either (or both) to run procrustes.
API keys are configured in `settings.toml`.



You may either write the key directly:



```toml

\[api\_serial\_keys]

openai = "YOUR\_OPENAI\_API\_KEY"

google = "YOUR\_GOOGLE\_API\_KEY"

```



Or point to a `.txt` file:



```toml

\[api\_serial\_keys]

openai = "openai\_key.txt"

google = "google\_key.txt"

```



If using `.txt` files, place them in the parent folder where Procrustes expects `settings.toml`.



Each key file should contain only the API key.



\## Basic usage
========================


Put your PDF files in the folder where you want to run the inquiry.



Then run:



```bash

procrustes inquire

```



Procrustes will process all `.pdf` files in that folder and write the results to:



```text

procrustean\_output.csv

```



\## Resume an interrupted inquiry
========================


If the process is interrupted, run:



```bash

procrustes resume

```



This resumes from the saved pickle file:



```text

procrustean\_pickle.pkl

```



\## CLI commands
========================


```bash

procrustes inquire

```



Start a new inquiry.



```bash

procrustes resume

```



Resume from the saved pickle.



```bash

procrustes open-settings

```



Open `settings.toml`.



```bash

procrustes reset

```



Reset `settings.toml` from `default\_settings.toml`.



\## Output
========================


The main output is:



```text

procrustean\_output.csv

```



Each row contains one requested entry and the values found for that entry.



Example:



```csv

Name,John Smith,Jane Smith

Date,12 March 2024,15 April 2024

Decision,Approved,Rejected

```



\## Configuration example
========================


Example `settings.toml`:



```toml

\[general]

language = "Modern Greek"

entries = \[

&#x20;   "Name",

&#x20;   "Date",

&#x20;   "Decision"

]



\[api\_serial\_keys]

openai = "openai\_key.txt"

google = "google\_key.txt"



\[inquiror]

model = "gpt-4.1"

reasoning = false

verbosity = false

temperature = false

top\_p = false

```



\## Notes
========================


Procrustes does not guarantee that the extracted information is correct. The output should be reviewed, especially when working with legal, bureaucratic, medical, financial, or archival documents.



The tool is designed to assist structured extraction, not replace human verification.



```

```




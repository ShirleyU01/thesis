# load your key into memory ; NEVER push the key file to GitHub
$ export OPENAI_API_KEY=$(cat .openapi.key)

# launch the proxy LLM server on a separate tab
$ litellm --config litellm.yaml

# run the generation of implementations
$ python3 main.py

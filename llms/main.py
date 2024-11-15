# main.py
from ideas_generation import IdeasGeneration
from llm import LLM

def main():
    llm = LLM(model="gpt4o-mini", litellm_url="http://0.0.0.0:4000", master_key="anything",temperature=0.7)
    #llm = LLM(model="gpt4o", litellm_url="http://0.0.0.0:4000", master_key="anything",temperature=0.7)
    # Create an instance of IdeasGeneration
    ideas_generator = IdeasGeneration(nb_ideas=5,attempts=3,llm=llm)
    
    # Call the run method
    ideas_generator.run()

if __name__ == "__main__":
    main()


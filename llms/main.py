import csv
import sys
import os

from ideas_generation import IdeasGeneration
from llm import LLM

def main():
    # Check if the user provided the correct number of arguments
    if len(sys.argv) <= 1:
        print("Usage: python main.py <Level:integer>")
        print("Level: 0 - Prompt options: Basic")
        print("Level: 1 - Prompt options: Basic + Syntax")
        print("Level: 2 - Prompt options: Basic + Library")
        print("Level: 3 - Prompt options: Basic + Diversity")
        print("Level: 4 - Prompt options: Basic + Syntax + Library + Diversity")
        sys.exit(1)

    # Open the CSV file and read its contents
    with open('../prompt/description.csv', mode='r') as file:
        reader = csv.reader(file)
        
        # Skip the header row if your CSV file has one
        header = next(reader, None)
        
        # Read rows and process them
        for row in reader:
            if len(row) == 7:  # Ensure the row has exactly two columns
                column1, column2, column3, column4, column5, column6, column7 = row
                #print(row)

                #llm = LLM(model="gpt41-mini", litellm_url="http://0.0.0.0:4000", master_key="anything",temperature=0.7)
                llm = LLM(model="gpt41", litellm_url="http://0.0.0.0:4000", master_key="anything",temperature=0.7)
                #llm = LLM(model="gpt4o-mini", litellm_url="http://0.0.0.0:4000", master_key="anything",temperature=1.0)
                #llm = LLM(model="gpt4o", litellm_url="http://0.0.0.0:4000", master_key="anything",temperature=0.7)

                if int(sys.argv[1]) <= 4:

                    # Create an instance of IdeasGeneration
                    ideas_generator = IdeasGeneration(level=int(sys.argv[1]),nb_ideas=10,attempts=3,llm=llm,description=column2,filename=column1,function_name=column3,module_name=column4,signature=column5,verified_file=None)
                    
                    # Call the run method
                    ideas_generator.run()

                else:
                    print(column1)
                    prefix = column1
                    prefix_base = column1.removesuffix(".mlw")
                    target = os.path.basename(sys.argv[2])

                    if target.startswith(prefix_base):
                        # Create an instance of IdeasGeneration
                        ideas_generator = IdeasGeneration(level=int(sys.argv[1]),nb_ideas=1,attempts=3,llm=llm,description=column2,filename=column1,function_name=column3,module_name=column4,signature=column5,verified_file=None)
                        
                        # Call the run method
                        ideas_generator.run_verification(sys.argv[2])
                        exit()
                    else:
                        continue


if __name__ == "__main__":
    main()


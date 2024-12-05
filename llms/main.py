import csv
import sys

from ideas_generation import IdeasGeneration
from llm import LLM

def main():
    # Check if the user provided the correct number of arguments
    if len(sys.argv) != 2:
        print("Usage: python main.py <integer>")
        sys.exit(1)


    # Open the CSV file and read its contents
    with open('../prompt/description.csv', mode='r') as file:
        reader = csv.reader(file)
        
        # Skip the header row if your CSV file has one
        header = next(reader, None)
        
        # Read rows and process them
        for row in reader:
            if len(row) == 5:  # Ensure the row has exactly two columns
                column1, column2, column3, column4, column5 = row
                #print(row)

                #llm = LLM(model="gpt4o-mini", litellm_url="http://0.0.0.0:4000", master_key="anything",temperature=0.7)
                llm = LLM(model="gpt4o", litellm_url="http://0.0.0.0:4000", master_key="anything",temperature=0.7)

                # Create an instance of IdeasGeneration
                ideas_generator = IdeasGeneration(level=int(sys.argv[1]),nb_ideas=10,attempts=3,llm=llm,description=column2,filename=column1,function_name=column3,module_name=column4,signature=column5)
                
                # Call the run method
                ideas_generator.run()

if __name__ == "__main__":
    main()


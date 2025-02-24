import pandas as pd
from blue import calculate_bleu

output_folder = "dec5-gpt4o-basic+all/"
output_table_path = "llms/compile/"+ output_folder + "info.csv"

df = pd.read_csv(output_table_path)

# filter success implementation for given benchmark
def filter_implementation (df, benchmark : str):
    success_df = df[df["Compile"] == [] &
                    df["Implementation"].astype(str).str.contains(benchmark[:-4])]
    success_implementation_list = []
    for _, row in success_df.iterrows():
        implementation = row["Implementation"]
        number = implementation.split("_")[-1].split(".")[0]
        implementation_file_path = "llms/implementation/" + output_folder + implementation
        with open(implementation_file_path, "r", encoding="utf-8") as f:
            implementation_content = f.read()
        success_implementation_list.append([number, implementation_content])
    return success_implementation_list

# calculate BLEU for each pair in the given list
def bleu_check (l : list):
    score_list = []
    for i in range (len(l)):
        for j in range (i+1, len(l)):
            score = calculate_bleu(l[i][1], l[j][1])
            score_list.append([(l[i][0], l[j][0]), score])
    return score

def calculate_all (df) :
    file_path = "prompt/description.csv"  
    description = pd.read_csv(file_path)

    benchmark_list = description.iloc[:, 0].tolist()

    scores_list = []
    for benchmark in benchmark_list:
        success_implementation = filter_implementation(df, benchmark)
        scores = bleu_check(success_implementation)
        scores_list.append([benchmark, scores])
    
    return scores_list

calculate_all(df)
        

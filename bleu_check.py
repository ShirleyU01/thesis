import pandas as pd
from blue import calculate_bleu
from refinement_prompt import extract_code
import os

output_folder = "dec5-gpt4o-basic+all/" # the GPT generation that we want to look at
output_table_path = "llms/compile/"+ output_folder + "info.csv"

df = pd.read_csv(output_table_path)

# filter success implementation for given benchmark
def filter_implementation(df, benchmark : str):
    success_df = df[(df["Complie"].astype(str) != "[]") &
                    (df["Implementation"].astype(str).str.contains(benchmark[:-4]))]
    success_implementation_list = []
    for _, row in success_df.iterrows():
        implementation = row["Implementation"]
        number = implementation.split("_")[-1].split(".")[0]
        implementation_file_path = "llms/implementation/" + output_folder + implementation
        with open(implementation_file_path, "r", encoding="utf-8") as f:
            implementation_content = f.read()
        implementation_content = extract_code(implementation_content)
        success_implementation_list.append([number, implementation_content])
    return success_implementation_list

# calculate BLEU for each pair in the given list
def bleu_check(l : list):
    score_list = []
    for i in range (len(l)):
        for j in range (i+1, len(l)):
            score = calculate_bleu(l[i][1], l[j][1])
            score_list.append([(l[i][0], l[j][0]), score])
    return score_list

def calculate_all(df) :
    file_path = "prompt/description.csv"  
    description = pd.read_csv(file_path)

    benchmark_list = description.iloc[:, 0].tolist()

    scores_list = []
    for benchmark in benchmark_list:
        success_implementation = filter_implementation(df, benchmark)
        scores = bleu_check(success_implementation)
        scores_list.append([benchmark, scores])
    return scores_list

# input: 
# df: the csv (info.csv generated after compile GPT implementations) that aims to analysis
# threshold: threshold for similar implementation (0 - 1)
# output_file: stored those information into a csv file
import csv

def bleu_analysis(df, threshold, output_file):
    result = calculate_all(df)

    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write the header row
        writer.writerow(["Benchmark", "Average Score", "Min Score", "Max Score", "Bad Pairs"])

        for row in result:
            sum_scores = 0
            min_score = 1
            max_score = 0
            benchmark = row[0]
            bad_pairs = []

            for pair in row[1]:
                score = pair[1]
                sum_scores += score
                if score > threshold:
                    bad_pairs.append(f"{pair[0]} ({score})")  # Store as "pair_name (score)"
                if score < min_score:
                    min_score = score
                if score > max_score:
                    max_score = score

            avg_score = sum_scores / len(row[1])

            # Convert bad pairs list to a string for CSV storage
            bad_pairs_str = "; ".join(bad_pairs) if bad_pairs else "No Similar Implementation"

            # Write the row
            writer.writerow([benchmark, avg_score, min_score, max_score, bad_pairs_str])

    print(f"Results saved to {output_file}")


os.makedirs("diversity/" + output_folder, exist_ok=True)  # Creates folder if it doesn't exist
output_file_path = "diversity/" + output_folder + "analysis.csv"
bleu_analysis(df, 0.4, output_file_path)

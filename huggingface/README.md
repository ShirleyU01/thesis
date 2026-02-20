# 📘 Filtered LeetCode Integer/List Benchmark

## Overview

This repository contains a filtered subset of the **LeetCodeDataset** from Hugging Face:

https://huggingface.co/datasets/newfacade/LeetCodeDataset

The original dataset contains approximately 2,600 Python programming problems with rich metadata, including problem descriptions, starter code, structured test cases (`input_output`), difficulty labels, tags, and temporal metadata.

We construct a **controlled benchmark subset** consisting only of problems whose inputs and outputs involve:

- `int`
- `List[int]`
- `None` (optional output)

The resulting dataset is saved as:

`valid_int_list_only_train.jsonl`

This benchmark is designed for controlled experiments in code generation and program verification.

---

## Motivation

The full LeetCode dataset contains heterogeneous data types such as strings, nested lists (e.g., `List[List[int]]`), matrices, trees (`TreeNode`), linked lists (`ListNode`), and other custom objects.

For research involving:

- LLM-based code generation  
- Program synthesis  
- Execution-based evaluation  
- SMT-based verification  
- Symbolic reasoning  

it is desirable to remove structural complexity and restrict to simple, well-defined input/output types.

By limiting problems to scalar integers and one-dimensional integer lists, we:

- Eliminate object construction overhead  
- Avoid custom class dependencies  
- Reduce parsing ambiguity  
- Simplify symbolic modeling  
- Improve verification tractability  
- Enable controlled, reproducible evaluation  

---

## Filtering Pipeline

The dataset filtering process consists of the following steps.

### Step 1 — Load the Original Dataset

We load the dataset from Hugging Face using the `datasets` library. The `train` split is used for filtering. Each example contains fields such as `prompt`, `completion`, `starter_code`, `input_output`, `difficulty`, `tags`, and metadata fields (including timestamps).

### Step 2 — Parse the `input_output` Field

Each problem contains structured test cases of the form:

`[{"input": "nums = [3,3], target = 6", "output": "[0, 1]"}, ...]`

We extract assignment values from the `input` string and safely parse them into Python objects using `ast.literal_eval()`. For example:

`"nums = [3,3], target = 6"`  
is parsed into:  
`[[3, 3], 6]`

Malformed or unparsable entries are excluded.

### Step 3 — Validate Input Types

For each test case, we verify that all parsed input values are either:

- `int`, or  
- `List[int]`

We explicitly reject:

- Nested lists (e.g., `List[List[int]]`)  
- Strings  
- Floats  
- Custom objects  
- Trees or linked lists  
- Malformed literals  

### Step 4 — Validate Output Types

Each output is parsed using `ast.literal_eval()` and retained only if it is:

- `int`  
- `List[int]`  
- `None`

We normalize special tokens such as `"None"`, `"null"`, `"true"`, and `"false"` where necessary. Invalid or malformed outputs are excluded.

### Step 5 — Exclude Non-Conforming Problems

If **any test case** within a problem violates the constraints above, the entire problem is excluded. This ensures type consistency across all retained problems.

### Step 6 — Preserve All Original Features

For retained problems:

- All original dataset fields are preserved  
- No columns are removed  
- Metadata (including datetime fields) is serialized safely  

### Step 7 — Save as JSONL

The filtered dataset is saved as:

`valid_int_list_only_train.jsonl`

The file format is **JSON Lines (JSONL)**, where each line contains one complete problem entry, preserving all original fields.

---

## Resulting Dataset

The final dataset:

- Contains only problems with scalar and 1D integer inputs/outputs  
- Preserves all metadata fields  
- Supports streaming evaluation  
- Eliminates structural complexity  
- Provides a clean experimental environment  

---

## File Structure
data/
├── data_extraction.py
├── valid_int_list_only_train.jsonl
└── README.md


---

## How to Regenerate the Dataset

1. Load the original LeetCode dataset.
2. Apply the filtering function described above.
3. Export the filtered split to JSONL format.

The process is deterministic and reproducible.

---

## Dataset Characteristics

- Source: LeetCode Python problems  
- License: Apache-2.0  
- Split used: `train`  
- Filtered for scalar and 1D integer-only input/output  

---

## Intended Use

This benchmark is designed for:

- LLM code generation evaluation  
- Controlled program synthesis experiments  
- Formal verification benchmarking  
- SMT-based correctness checking  
- Execution-based evaluation without complex type handling  

---

## Reproducibility Notes

- The filtering procedure is deterministic.  
- Malformed test cases are excluded.  
- Datetime metadata is serialized in ISO format.  
- JSONL format supports scalable streaming and batch evaluation.  

---

## Summary

This filtered benchmark provides a clean, well-defined subset of LeetCode problems focused exclusively on integer and one-dimensional list inputs and outputs. It is suitable for rigorous and controlled experimentation in code generation and verification research.
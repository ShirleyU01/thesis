from datasets import load_dataset

import ast
import re
import json
import datetime
import numpy as np

ASSIGN_RE = re.compile(r"(\w+)\s*=\s*")
_INVALID = object()


def make_json_safe(obj):
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    else:
        return obj


def safe_literal_eval(s: str):
    s = s.strip()

    # common JSON tokens
    if s in ("null", "NULL"):
        return None
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False

    try:
        return ast.literal_eval(s)
    except (SyntaxError, ValueError):
        # common dataset glitch: a dangling quote at the end: ...]]"
        if s.endswith('"') and not s.startswith('"'):
            try:
                return ast.literal_eval(s[:-1])
            except (SyntaxError, ValueError):
                return _INVALID
        return _INVALID

def parse_input_string(input_str: str):
    matches = list(ASSIGN_RE.finditer(input_str))
    if not matches:
        return _INVALID

    values = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(input_str)
        value_str = input_str[start:end].strip().rstrip(",").strip()

        v = safe_literal_eval(value_str)
        if v is _INVALID:
            return _INVALID

        values.append(v)

    return values

def parse_output_string(output_str):
    s = output_str.strip()

    # normalize common non-Python tokens
    if s in ("None", "null", "NULL"):
        return None
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False

    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return _INVALID

def is_int_or_list_of_int(x):
    return isinstance(x, int) or (isinstance(x, list) and all(isinstance(i, int) for i in x))

def is_int_list_only_problem(example):
    for case in example["input_output"]:
        inputs = parse_input_string(case["input"])
        if inputs is _INVALID:
            return False

        output = safe_literal_eval(case["output"])
        if output is _INVALID:
            return False

        if not all(is_int_or_list_of_int(v) for v in inputs):
            return False
        if output is not None and not is_int_or_list_of_int(output):
            return False
    return True

if __name__=="__main__":
    ds = load_dataset("newfacade/LeetCodeDataset")
    train = ds["train"]
    test = ds["test"]   

    print(test[0])

    # valid = train.filter(is_int_list_only_problem)
    # print("valid:", len(valid), "out of", len(train))
    # out_path = "valid_int_list_only_train.jsonl"

    # with open(out_path, "w", encoding="utf-8") as f:
    #     for ex in valid:
    #         safe_ex = make_json_safe(ex)
    #         f.write(json.dumps(safe_ex, ensure_ascii=False) + "\n")


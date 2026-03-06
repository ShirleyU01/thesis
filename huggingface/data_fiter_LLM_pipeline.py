import os
import re
import json
import ast
import argparse
from typing import Any, Dict, List, Optional, Tuple

ALLOWED_BUCKETS = {
    "int",
    "list_int",
    "int_and_list_int",
    "list_list_int",
    "node",
    "tree",
    "string",
    "other",
    "unknown",
}

SYSTEM_PROMPT = """You are a careful static-analysis assistant for programming datasets.

Your task is to classify the input/output type of a coding problem using:
1. the problem description,
2. the function signature or starter code, if provided,
3. the example testcases.

You must infer the most likely function name, signature, and coarse type bucket.

You must be conservative:
- Do not simplify the type if the evidence suggests a more complex structure.
- Use the testcases as strong evidence.
- If the signature and testcase conflict, mention that in the justification and choose the interpretation most strongly supported by the evidence.
- If the type cannot be confidently determined, output "unknown".

Return exactly one valid JSON object and nothing else.

Output JSON schema:
{
  "problem_id": string,
  "function_name": string,
  "signature": string,
  "input_type": string,
  "output_type": string,
  "type_bucket": string,
  "uses_node_or_tree": boolean,
  "justification": string,
  "confidence": "high" | "medium" | "low"
}

Allowed values for type_bucket:
- "int"
- "list_int"
- "int_and_list_int"
- "list_list_int"
- "node"
- "tree"
- "string"
- "other"
- "unknown"

Classification rules:
- "int": all inputs are integers and output is integer or None.
- "list_int": all inputs are List[int] and output is int, List[int], or None.
- "int_and_list_int": inputs and outputs involve only int and List[int].
- "list_list_int": nested integer lists or matrix-like integer structures are involved.
- "node": linked-list node or similar node-based structure.
- "tree": tree node or tree structure.
- "string": string is a primary input or output type.
- "other": structured or mixed types not covered above.
- "unknown": evidence is insufficient or contradictory.

Additional rules:
- Infer the function name from the starter code if available; otherwise infer from the description or testcases.
- Infer a Python-style signature when possible.
- The justification must explicitly reference evidence from the description and/or testcase format.
- Set uses_node_or_tree to true only when linked-list or tree structures are clearly involved.

Return only valid JSON. No markdown. No extra text.
"""

USER_PROMPT_TEMPLATE = """Analyze the following coding problem and classify its input/output types.

Problem ID: {problem_id}

Question description:
{question_description}

Starter code / signature:
{starter_code}

Example testcases:
{input_output}

Instructions:
1. Infer the intended function name.
2. Infer the most likely Python-style function signature.
3. Identify the input type and output type.
4. Assign exactly one type_bucket from:
   int, list_int, int_and_list_int, list_list_int, node, tree, string, other, unknown.
5. Set uses_node_or_tree to true only if linked-list or tree structures are clearly involved.
6. Write a brief justification based on the description and testcases.
7. Set confidence to high, medium, or low.

Return exactly one JSON object.
"""

INVALID = object()
ASSIGN_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*")
DEF_RE = re.compile(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*(?:->\s*([^:]+))?:")
LISTNODE_RE = re.compile(r"\bListNode\b|\blinked list\b|\bnext\b", re.IGNORECASE)
TREENODE_RE = re.compile(r"\bTreeNode\b|\bbinary tree\b|\bBST\b|\broot\b|\bleft\b|\bright\b", re.IGNORECASE)
STRING_HINT_RE = re.compile(r"\bstr\b|string", re.IGNORECASE)
MATRIX_WORD_RE = re.compile(r"\bmatrix\b|\bgrid\b|\bboard\b|\bsudoku\b", re.IGNORECASE)

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def read_jsonl(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(make_json_safe(row), ensure_ascii=False) + "\n")

def make_json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(v) for v in obj]
    if isinstance(obj, tuple):
        return [make_json_safe(v) for v in obj]
    if hasattr(obj, "isoformat"):
        try:
            return obj.isoformat()
        except Exception:
            return str(obj)
    try:
        import numpy as np
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
    except Exception:
        pass
    return obj

def extract_question_description(row: Dict[str, Any]) -> str:
    candidates = [
        row.get("question_description"),
        row.get("description"),
        row.get("prompt"),
        row.get("problem_description"),
        row.get("question"),
    ]
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c.strip()
    return ""

def extract_starter_code(row: Dict[str, Any]) -> str:
    candidates = [
        row.get("starter_code"),
        row.get("signature"),
        row.get("code_prompt"),
    ]
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c.strip()
    return ""

def extract_input_output(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    io = row.get("input_output", [])
    if isinstance(io, list):
        return io
    return []

def normalize_row(row: Dict[str, Any], idx: int, split: str) -> Dict[str, Any]:
    return {
        "problem_id": row.get("problem_id") or f"leetcode_{split}_{idx:06d}",
        "source_split": split,
        "question_description": extract_question_description(row),
        "starter_code": extract_starter_code(row),
        "input_output": extract_input_output(row),
        "difficulty": row.get("difficulty", ""),
        "tags": row.get("tags", []),
        "raw_record": row,
    }

def safe_literal_eval(s: str) -> Any:
    s = s.strip()
    if not s:
        return INVALID
    lowered = s.lower()
    if lowered == "none" or lowered == "null":
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return ast.literal_eval(s)
    except Exception:
        if s.endswith('"') and not s.startswith('"'):
            try:
                return ast.literal_eval(s[:-1])
            except Exception:
                return INVALID
        return INVALID

def split_assignments(input_str: str) -> List[str]:
    matches = list(ASSIGN_RE.finditer(input_str))
    if not matches:
        return []
    values = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(input_str)
        value_str = input_str[start:end].strip().rstrip(",").strip()
        values.append(value_str)
    return values

def parse_input_string(input_str: str) -> Any:
    value_strs = split_assignments(input_str)
    if not value_strs:
        return INVALID
    values = []
    for s in value_strs:
        v = safe_literal_eval(s)
        if v is INVALID:
            return INVALID
        values.append(v)
    return values

def parse_output_string(output_str: str) -> Any:
    return safe_literal_eval(output_str)

def is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)

def is_list_int(x: Any) -> bool:
    return isinstance(x, list) and all(is_int(v) for v in x)

def is_list_list_int(x: Any) -> bool:
    return isinstance(x, list) and all(is_list_int(v) for v in x)

def contains_string(x: Any) -> bool:
    if isinstance(x, str):
        return True
    if isinstance(x, list):
        return any(contains_string(v) for v in x)
    if isinstance(x, dict):
        return any(contains_string(v) for v in x.values())
    return False

def infer_bucket_from_values(inputs: List[Any], output: Any) -> str:
    all_values = list(inputs)
    if output is not None:
        all_values.append(output)
    if any(contains_string(v) for v in all_values):
        return "string"
    if any(is_list_list_int(v) for v in all_values):
        return "list_list_int"
    if all(is_int(v) for v in inputs) and (output is None or is_int(output)):
        return "int"
    if all(is_list_int(v) for v in inputs) and (output is None or is_int(output) or is_list_int(output)):
        return "list_int"
    if all(is_int(v) or is_list_int(v) for v in inputs) and (output is None or is_int(output) or is_list_int(output)):
        return "int_and_list_int"
    return "other"

def parse_signature_from_starter_code(starter_code: str) -> Tuple[str, str]:
    if not starter_code:
        return "", ""
    m = DEF_RE.search(starter_code)
    if not m:
        return "", ""
    fn = m.group(1).strip()
    params = m.group(2).strip()
    ret = (m.group(3) or "").strip()
    if ret:
        sig = f"def {fn}({params}) -> {ret}"
    else:
        sig = f"def {fn}({params})"
    return fn, sig

def infer_function_name_from_description(description: str) -> str:
    m = re.search(r"\bdef\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", description)
    if m:
        return m.group(1)
    m = re.search(r"`([A-Za-z_][A-Za-z0-9_]*)`", description)
    if m:
        return m.group(1)
    return ""

def infer_signature_fallback(function_name: str, bucket: str) -> str:
    if not function_name:
        return ""
    defaults = {
        "int": f"def {function_name}(x: int) -> int",
        "list_int": f"def {function_name}(nums: List[int]) -> List[int]",
        "int_and_list_int": f"def {function_name}(nums: List[int], x: int) -> List[int]",
        "list_list_int": f"def {function_name}(grid: List[List[int]]) -> List[int]",
        "node": f"def {function_name}(head: ListNode) -> ListNode",
        "tree": f"def {function_name}(root: TreeNode) -> TreeNode",
        "string": f"def {function_name}(s: str) -> str",
        "other": f"def {function_name}(...)",
        "unknown": f"def {function_name}(...)",
    }
    return defaults.get(bucket, f"def {function_name}(...)")

def detect_node_tree(description: str, starter_code: str, input_output: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    text = "\n".join([
        description or "",
        starter_code or "",
        json.dumps(input_output, ensure_ascii=False),
    ])
    if LISTNODE_RE.search(text):
        return {
            "type_bucket": "node",
            "confidence": "high",
            "justification": "Detected ListNode or linked-list indicators in description, starter code, or testcases.",
            "uses_node_or_tree": True,
        }
    if TREENODE_RE.search(text):
        return {
            "type_bucket": "tree",
            "confidence": "high",
            "justification": "Detected TreeNode or tree indicators in description, starter code, or testcases.",
            "uses_node_or_tree": True,
        }
    return None

def detect_string_type(description: str, starter_code: str, input_output: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    text = "\n".join([
        description or "",
        starter_code or "",
        json.dumps(input_output, ensure_ascii=False),
    ])
    if STRING_HINT_RE.search(text):
        return {
            "type_bucket": "string",
            "confidence": "medium",
            "justification": "Detected string-related markers in description or starter code.",
            "uses_node_or_tree": False,
        }
    return None

def detect_list_list_or_matrix(description: str, starter_code: str, input_output: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    text = "\n".join([
        description or "",
        starter_code or "",
        json.dumps(input_output, ensure_ascii=False),
    ])
    if MATRIX_WORD_RE.search(text):
        return {
            "type_bucket": "list_list_int",
            "confidence": "medium",
            "justification": "Detected matrix/grid/board language suggesting nested list structure.",
            "uses_node_or_tree": False,
        }
    for case in input_output[:10]:
        parsed_inputs = parse_input_string(case.get("input", ""))
        parsed_output = parse_output_string(case.get("output", ""))
        if parsed_inputs is INVALID or parsed_output is INVALID:
            continue
        vals = list(parsed_inputs)
        if parsed_output is not None:
            vals.append(parsed_output)
        if any(is_list_list_int(v) for v in vals):
            return {
                "type_bucket": "list_list_int",
                "confidence": "high",
                "justification": "Parsed testcase values include nested integer lists.",
                "uses_node_or_tree": False,
            }
    return None

def rule_based_classify(row: Dict[str, Any]) -> Dict[str, Any]:
    problem_id = row["problem_id"]
    description = row["question_description"]
    starter_code = row["starter_code"]
    input_output = row["input_output"]

    fn_name, sig = parse_signature_from_starter_code(starter_code)
    if not fn_name:
        fn_name = infer_function_name_from_description(description)

    node_tree = detect_node_tree(description, starter_code, input_output)
    if node_tree:
        return {
            "problem_id": problem_id,
            "function_name": fn_name,
            "signature": sig or infer_signature_fallback(fn_name or "solution", node_tree["type_bucket"]),
            "input_type": "",
            "output_type": "",
            "type_bucket": node_tree["type_bucket"],
            "uses_node_or_tree": node_tree["uses_node_or_tree"],
            "justification": node_tree["justification"],
            "confidence": node_tree["confidence"],
            "classification_source": "rule",
        }

    matrix_like = detect_list_list_or_matrix(description, starter_code, input_output)
    if matrix_like:
        return {
            "problem_id": problem_id,
            "function_name": fn_name,
            "signature": sig or infer_signature_fallback(fn_name or "solution", matrix_like["type_bucket"]),
            "input_type": "List[List[int]] or similar",
            "output_type": "",
            "type_bucket": matrix_like["type_bucket"],
            "uses_node_or_tree": matrix_like["uses_node_or_tree"],
            "justification": matrix_like["justification"],
            "confidence": matrix_like["confidence"],
            "classification_source": "rule",
        }

    string_like = detect_string_type(description, starter_code, input_output)
    if string_like:
        return {
            "problem_id": problem_id,
            "function_name": fn_name,
            "signature": sig or infer_signature_fallback(fn_name or "solution", string_like["type_bucket"]),
            "input_type": "str or related",
            "output_type": "",
            "type_bucket": string_like["type_bucket"],
            "uses_node_or_tree": string_like["uses_node_or_tree"],
            "justification": string_like["justification"],
            "confidence": string_like["confidence"],
            "classification_source": "rule",
        }

    parsed_cases = []
    for case in input_output[:10]:
        parsed_inputs = parse_input_string(case.get("input", ""))
        parsed_output = parse_output_string(case.get("output", ""))
        if parsed_inputs is INVALID or parsed_output is INVALID:
            return {
                "problem_id": problem_id,
                "function_name": fn_name,
                "signature": sig or "",
                "input_type": "",
                "output_type": "",
                "type_bucket": "unknown",
                "uses_node_or_tree": False,
                "justification": "At least one testcase could not be parsed reliably.",
                "confidence": "low",
                "classification_source": "rule",
            }
        parsed_cases.append((parsed_inputs, parsed_output))

    if not parsed_cases:
        return {
            "problem_id": problem_id,
            "function_name": fn_name,
            "signature": sig or "",
            "input_type": "",
            "output_type": "",
            "type_bucket": "unknown",
            "uses_node_or_tree": False,
            "justification": "No parseable testcases available.",
            "confidence": "low",
            "classification_source": "rule",
        }

    buckets = set()
    for parsed_inputs, parsed_output in parsed_cases:
        buckets.add(infer_bucket_from_values(parsed_inputs, parsed_output))

    if len(buckets) == 1:
        bucket = next(iter(buckets))
        input_types = summarize_input_types(parsed_cases)
        output_type = summarize_output_types(parsed_cases)
        conf = "high" if bucket in {"int", "list_int", "int_and_list_int", "list_list_int"} else "medium"
        return {
            "problem_id": problem_id,
            "function_name": fn_name,
            "signature": sig or infer_signature_fallback(fn_name or "solution", bucket),
            "input_type": input_types,
            "output_type": output_type,
            "type_bucket": bucket,
            "uses_node_or_tree": False,
            "justification": f"Rule-based classification from parsed testcase values indicates bucket '{bucket}'.",
            "confidence": conf,
            "classification_source": "rule",
        }

    return {
        "problem_id": problem_id,
        "function_name": fn_name,
        "signature": sig or "",
        "input_type": summarize_input_types(parsed_cases),
        "output_type": summarize_output_types(parsed_cases),
        "type_bucket": "unknown",
        "uses_node_or_tree": False,
        "justification": f"Parsed testcase values suggest inconsistent buckets: {sorted(buckets)}.",
        "confidence": "low",
        "classification_source": "rule",
    }

def summarize_value_type(x: Any) -> str:
    if x is None:
        return "None"
    if is_int(x):
        return "int"
    if is_list_int(x):
        return "List[int]"
    if is_list_list_int(x):
        return "List[List[int]]"
    if isinstance(x, str):
        return "str"
    if isinstance(x, list):
        return "list"
    if isinstance(x, dict):
        return "dict"
    return type(x).__name__

def summarize_input_types(parsed_cases: List[Tuple[List[Any], Any]]) -> str:
    seen = set()
    for inputs, _ in parsed_cases:
        for v in inputs:
            seen.add(summarize_value_type(v))
    return ", ".join(sorted(seen)) if seen else ""

def summarize_output_types(parsed_cases: List[Tuple[List[Any], Any]]) -> str:
    seen = set()
    for _, output in parsed_cases:
        seen.add(summarize_value_type(output))
    return ", ".join(sorted(seen)) if seen else ""

def should_send_to_llm(rule_result: Dict[str, Any]) -> bool:
    if rule_result["type_bucket"] == "unknown":
        return True
    if rule_result["confidence"] in {"low"}:
        return True
    return False

def build_user_prompt(row: Dict[str, Any]) -> str:
    return USER_PROMPT_TEMPLATE.format(
        problem_id=row["problem_id"],
        question_description=row["question_description"] or "",
        starter_code=row["starter_code"] or "",
        input_output=json.dumps(row["input_output"], ensure_ascii=False, indent=2),
    )

def validate_llm_result(result: Dict[str, Any], problem_id: str) -> Dict[str, Any]:
    out = {
        "problem_id": problem_id,
        "function_name": str(result.get("function_name", "") or ""),
        "signature": str(result.get("signature", "") or ""),
        "input_type": str(result.get("input_type", "") or ""),
        "output_type": str(result.get("output_type", "") or ""),
        "type_bucket": str(result.get("type_bucket", "unknown") or "unknown"),
        "uses_node_or_tree": bool(result.get("uses_node_or_tree", False)),
        "justification": str(result.get("justification", "") or ""),
        "confidence": str(result.get("confidence", "low") or "low"),
        "classification_source": "llm",
    }
    if out["type_bucket"] not in ALLOWED_BUCKETS:
        out["type_bucket"] = "unknown"
    if out["confidence"] not in {"high", "medium", "low"}:
        out["confidence"] = "low"
    return out

def llm_classify_openai(row: Dict[str, Any], model: str) -> Dict[str, Any]:
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError("Please install the openai package: pip install openai") from e

    client = OpenAI()
    user_prompt = build_user_prompt(row)

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content
    result = json.loads(content)
    return validate_llm_result(result, row["problem_id"])

def llm_classify_stub(row: Dict[str, Any]) -> Dict[str, Any]:
    fn_name, sig = parse_signature_from_starter_code(row["starter_code"])
    if not fn_name:
        fn_name = infer_function_name_from_description(row["question_description"])
    return {
        "problem_id": row["problem_id"],
        "function_name": fn_name,
        "signature": sig,
        "input_type": "",
        "output_type": "",
        "type_bucket": "unknown",
        "uses_node_or_tree": False,
        "justification": "LLM classification not enabled.",
        "confidence": "low",
        "classification_source": "llm",
    }

def merge_results(row: Dict[str, Any], rule_result: Dict[str, Any], llm_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    use_llm = False
    conflict_flag = False

    if llm_result is None:
        final = rule_result
    elif rule_result["confidence"] == "high" and rule_result["type_bucket"] != "unknown":
        final = rule_result
        if llm_result["type_bucket"] != rule_result["type_bucket"] and llm_result["type_bucket"] != "unknown":
            conflict_flag = True
    else:
        final = llm_result
        use_llm = True
        if llm_result["type_bucket"] != rule_result["type_bucket"] and rule_result["type_bucket"] != "unknown":
            conflict_flag = True

    return {
        "problem_id": row["problem_id"],
        "question_description": row["question_description"],
        "starter_code": row["starter_code"],
        "input_output": row["input_output"],
        "difficulty": row["difficulty"],
        "tags": row["tags"],
        "function_name": final.get("function_name", ""),
        "signature": final.get("signature", ""),
        "input_type": final.get("input_type", ""),
        "output_type": final.get("output_type", ""),
        "type_bucket": final.get("type_bucket", "unknown"),
        "uses_node_or_tree": final.get("uses_node_or_tree", False),
        "justification": final.get("justification", ""),
        "confidence": final.get("confidence", "low"),
        "classification_source": "llm" if use_llm else "rule",
        "conflict_flag": conflict_flag,
    }

def export_bucket_files(rows: List[Dict[str, Any]], out_dir: str) -> None:
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        bucket = row["type_bucket"]
        buckets.setdefault(bucket, []).append(row)
    for bucket, bucket_rows in buckets.items():
        path = os.path.join(out_dir, f"reduced_{bucket}.jsonl")
        write_jsonl(path, bucket_rows)

def build_generation_manifest(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    manifest = []
    for row in rows:
        module_name = to_module_name(row["problem_id"])
        extension = ".mlw"
        manifest.append({
            "problem_id": row["problem_id"],
            "filename": row["problem_id"] + extension,
            "module_name": module_name,
            "function_name": row.get("function_name", ""),
            "signature": row.get("signature", ""),
            "description": row.get("question_description", ""),
            "type_bucket": row.get("type_bucket", "unknown"),
            "starter_code": row.get("starter_code", ""),
            "input_output": row.get("input_output", []),
            "difficulty": row.get("difficulty", ""),
            "tags": row.get("tags", []),
        })
    return manifest

def to_module_name(problem_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", " ", problem_id).title().replace(" ", "")
    if not cleaned:
        cleaned = "Problem"
    if cleaned[0].isdigit():
        cleaned = "P" + cleaned
    return cleaned

def export_review_file(rows: List[Dict[str, Any]], out_path: str) -> None:
    flagged = [
        row for row in rows
        if row["confidence"] == "low" or row["type_bucket"] == "unknown" or row["conflict_flag"]
    ]
    write_jsonl(out_path, flagged)

def normalize_dataset(input_path: str, split: str) -> List[Dict[str, Any]]:
    raw_rows = read_jsonl(input_path)
    return [normalize_row(row, idx, split) for idx, row in enumerate(raw_rows)]

def run_pipeline(
    input_path: str,
    output_dir: str,
    split: str = "train",
    use_llm: bool = False,
    llm_model: str = "gpt-4o-mini",
    limit: Optional[int] = None,
) -> None:
    ensure_dir(output_dir)
    normalized = normalize_dataset(input_path, split)
    if limit is not None:
        normalized = normalized[:limit]

    normalized_path = os.path.join(output_dir, "normalized.jsonl")
    write_jsonl(normalized_path, normalized)

    rule_rows = []
    llm_rows = []
    merged_rows = []

    for row in normalized:
        rule_result = rule_based_classify(row)
        rule_rows.append(rule_result)

        llm_result = None
        if should_send_to_llm(rule_result):
            if use_llm:
                try:
                    llm_result = llm_classify_openai(row, llm_model)
                except Exception as e:
                    llm_result = {
                        "problem_id": row["problem_id"],
                        "function_name": rule_result.get("function_name", ""),
                        "signature": rule_result.get("signature", ""),
                        "input_type": "",
                        "output_type": "",
                        "type_bucket": "unknown",
                        "uses_node_or_tree": False,
                        "justification": f"LLM classification failed: {str(e)}",
                        "confidence": "low",
                        "classification_source": "llm",
                    }
            else:
                llm_result = llm_classify_stub(row)
            llm_rows.append(llm_result)

        merged_rows.append(merge_results(row, rule_result, llm_result))

    write_jsonl(os.path.join(output_dir, "rule_classified.jsonl"), rule_rows)
    write_jsonl(os.path.join(output_dir, "llm_classified.jsonl"), llm_rows)
    write_jsonl(os.path.join(output_dir, "classified.jsonl"), merged_rows)

    export_review_file(merged_rows, os.path.join(output_dir, "review_low_confidence.jsonl"))
    export_bucket_files(merged_rows, output_dir)

    int_list_rows = [
        row for row in merged_rows
        if row["type_bucket"] in {"int", "list_int", "int_and_list_int"}
    ]
    write_jsonl(os.path.join(output_dir, "reduced_int_list.jsonl"), int_list_rows)

    node_tree_rows = [
        row for row in merged_rows
        if row["type_bucket"] in {"node", "tree"}
    ]
    write_jsonl(os.path.join(output_dir, "reduced_node_tree.jsonl"), node_tree_rows)

    manifest = build_generation_manifest(int_list_rows)
    write_jsonl(os.path.join(output_dir, "manifest_generation.jsonl"), manifest)

    summary = {
        "total_rows": len(normalized),
        "rule_classified": len(rule_rows),
        "llm_classified": len(llm_rows),
        "final_counts": count_buckets(merged_rows),
        "int_list_rows": len(int_list_rows),
        "node_tree_rows": len(node_tree_rows),
        "manifest_rows": len(manifest),
    }
    with open(os.path.join(output_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

def count_buckets(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        bucket = row["type_bucket"]
        counts[bucket] = counts.get(bucket, 0) + 1
    return counts

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to raw input JSONL")
    parser.add_argument("--output_dir", required=True, help="Directory for processed outputs")
    parser.add_argument("--split", default="train")
    parser.add_argument("--use_llm", action="store_true")
    parser.add_argument("--llm_model", default="gpt-4o-mini")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    run_pipeline(
        input_path=args.input,
        output_dir=args.output_dir,
        split=args.split,
        use_llm=args.use_llm,
        llm_model=args.llm_model,
        limit=args.limit,
    )

if __name__ == "__main__":
    main()
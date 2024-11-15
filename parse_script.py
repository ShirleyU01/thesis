import re

# deal with why3 list
def parse_nested_cons(cons_string):
    def find_balanced_parentheses(s):
        stack = []
        for i, char in enumerate(s):
            if char == '(':
                stack.append(char)
            elif char == ')':
                stack.pop()
                if not stack:  
                    return i
        return -1 

    cons_string = cons_string.strip()

    if cons_string == "Nil" or cons_string == "(Nil)":
        return []
    
    if cons_string.startswith("(Cons"):
        head_start = cons_string.find('(') + 1
        head_end = head_start + find_balanced_parentheses(cons_string[head_start:])

        head = cons_string[head_start:head_end + 1]

        rest_start = head_end + 2 
        rest_end = rest_start + find_balanced_parentheses(cons_string[rest_start:])

        rest = cons_string[rest_start:rest_end + 1]

        parsed_head = parse_nested_cons(head)
        parsed_rest = parse_nested_cons(rest)

        return [parsed_head] + parsed_rest
    else:
        try:
            return int(cons_string)  
        except ValueError:
            return cons_string  


def extract_and_parse_result(stdout):
    match = re.search(r"result:.*?=\s+((?:\(.+?\)))(?=\nglobals:|$)", stdout, re.DOTALL)
    result_string = match.group(1).strip() if match else None
    if not result_string:
        return None
    
    return parse_nested_cons(result_string)


def parse_result(stdout : str) :
    parsed_result = extract_and_parse_result(stdout)
    r = []
    if not parsed_result:
        return "Passed!"
    for pair in parsed_result:
        l = pair.split(',\n')
        l = [s.lstrip() for s in l]
        r += [l]

    all_failed_output = ''
    for pair in r:
        input_pair = 'for input '
        input_num = len(pair) - 2
        for i in range (input_num):
            if i == input_num - 1:
                input_pair += pair[i] + "; "
            else:
                input_pair += pair[i] + " and "
        actual_output = 'the output we obtained with current implementation is ' + pair[input_num] + "; "
        expected_output = 'but the expected output is ' + pair[input_num+1] + '\n'
        output_str = input_pair + actual_output + expected_output
        all_failed_output += output_str
    return all_failed_output

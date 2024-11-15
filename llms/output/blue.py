from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

def calculate_bleu(reference, candidate):
    """
    Calculate BLEU score for a candidate paragraph against a reference paragraph.

    :param reference: The reference paragraph
    :param candidate: The candidate paragraph
    :return: BLEU score
    """
    # Tokenize the paragraphs
    reference_tokens = [reference.split()]  # List of tokenized references
    candidate_tokens = candidate.split()    # Tokenized candidate paragraph
    
    # Use smoothing to avoid zero scores for short paragraphs
    smoothing_function = SmoothingFunction().method1
    
    # Calculate BLEU score
    bleu_score = sentence_bleu(reference_tokens, candidate_tokens, smoothing_function=smoothing_function)
    return bleu_score

# Paragraphs to compare
reference_paragraph = """module SumProduct4

    use int.Int
    use list.List
    use list.Length

    let rec sum_product_recur_2_accumulator (t : list int) (acc_sum : int) (acc_product : int) : (int, int) =
        match t with
        | Nil -> (acc_sum, acc_product)
        | Cons x xs -> sum_product_recur_2_accumulator xs (acc_sum + x) (acc_product * x)
        end

    let sum_product_recur_2 (t : list int) : (int, int) =
        sum_product_recur_2_accumulator t 0 1

end
"""

reference_paragraph2 = """module SumProduct3

    use int.Int
    use list.List
    use list.Length

    let rec sum_product_recur_1 (t : list int) : (int, int) =
        match t with
        | Nil -> (0, 1)
        | Cons x xs ->
            let (sum, product) = sum_product_recur_1 xs in
            (x + sum, x * product)
        end

end"""

candidate_paragraph = """module SumProduct5

    use int.Int
    use list.List
    use list.Length

    let rec sum_product_recur_3 (t : list int) : (int, int) =
        match t with
        | Nil -> (0, 1)
        | Cons x xs ->
            let (sum, product) = sum_product_recur_3 xs in
            (x + sum, x * product)
        end

end"""

# Calculate BLEU score
bleu_score = calculate_bleu(reference_paragraph, candidate_paragraph)

# Print the BLEU score
print(f"BLEU score: {bleu_score:.4f}")


from typing import List, Dict, Tuple, Any

def calculate_gap_level(score_percent: float) -> str:
    """
    Categorizes learner competency gap level based on score percentage thresholds:
    - Score >= 75%: Strong (High proficiency)
    - 50% <= Score < 75%: Moderate (Needs minor reinforcement)
    - Score < 50%: Weak (Significant competency gap identified)
    """
    if score_percent >= 75.0:
        return "Strong"
    elif score_percent >= 50.0:
        return "Moderate"
    return "Weak"

def grade_quiz_attempt(
    user_answers: List[int],
    quiz_questions: List[Dict[str, Any]]
) -> Tuple[float, int, int, str, List[Dict[str, Any]]]:
    """
    Grades user answers against stored correct answers.
    Returns (score_percent, correct_count, total_questions, gap_level, question_reviews)
    """
    total_questions = len(quiz_questions)
    if total_questions == 0:
        return 0.0, 0, 0, "Weak", []

    correct_count = 0
    question_reviews = []

    for idx, question in enumerate(quiz_questions):
        user_ans = user_answers[idx] if idx < len(user_answers) else -1
        correct_ans = question.get("correct_index", 0)
        is_correct = (user_ans == correct_ans)

        if is_correct:
            correct_count += 1

        question_reviews.append({
            "question_index": idx,
            "question": question.get("question", ""),
            "options": question.get("options", []),
            "user_answer_index": user_ans,
            "correct_index": correct_ans,
            "is_correct": is_correct,
            "explanation": question.get("explanation", "")
        })

    score_percent = round((correct_count / total_questions) * 100.0, 2)
    gap_lvl = calculate_gap_level(score_percent)

    return score_percent, correct_count, total_questions, gap_lvl, question_reviews

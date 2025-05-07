import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from models.course import Course

def load_llm_model(
    model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
    torch_dtype: torch.dtype = torch.bfloat16,
    device_map: str | dict = "auto",
    trust_remote_code: bool = True
) -> tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load and return the LLM and its tokenizer.
    """
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch_dtype,
        device_map=device_map,
        trust_remote_code=trust_remote_code
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=trust_remote_code
    )
    return model, tokenizer


async def generate_answer(
    query: str,
    courses: list[Course],
    chat_history: list[dict[str, str]],
    model,
    tokenizer,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9
) -> str:
    """
    Given a user query, a list of Course models, and prior chat history,
    construct the chat prompt and return the model’s answer.

    :param query:         The user’s learning objective.
    :param courses:       Candidate courses (Course instances).
    :param chat_history:  Previous messages, each with 'role' and 'content'.
    :param model:         The language generation model.
    :param tokenizer:     Tokenizer with chat-template support.
    :param max_new_tokens: Max tokens to generate.
    :param temperature:   Sampling temperature.
    :param top_p:         Nucleus sampling threshold.
    :return:              Generated assistant reply.
    """
    # System instruction
    system_msg = {
        "role": "system",
        "content": (
            "You are an intelligent academic course advisor. "
            "Your job is to help users find the most relevant online courses from a list, based on their learning goals.\n\n"
            "For each course, consider:\n"
            "  - Title and description\n"
            "  - Tags and topics\n"
            "  - Duration, difficulty, learner feedback, and popularity\n\n"
            "Your task:\n"
            "  1. Evaluate and compare the provided courses.\n"
            "  2. Recommend the top 3 courses that best match the user’s objective.\n"
            "  3. For each recommendation, include:\n"
            "     - Title\n"
            "     - Rationale (why it fits the user's goal)\n"
            "     - Duration and estimated difficulty\n"
            "     - Learner feedback summary (if ratings available)\n"
        )
    }

    # Format the course metadata into numbered entries
    formatted_courses = []
    for idx, course in enumerate(courses, start=1):
        parts = [f"{idx}. {course.title or 'Untitled Course'}"]
        if course.description:
            parts.append(f"Description: {course.description}")
        if course.duration is not None:
            parts.append(f"Duration: {course.duration} minutes")
        if course.learners_amount is not None:
            parts.append(f"Learners: {course.learners_amount}")
        if course.star_rating is not None:
            rating_text = f"Rating: {course.star_rating:.1f} / 5"
            if course.star_num_ratings:
                rating_text += f" ({course.star_num_ratings} ratings)"
            parts.append(rating_text)
        if course.tags:
            parts.append(f"Tags: {', '.join(course.tags)}")
        formatted_courses.append("\n".join(parts))

    course_list_text = "\n\n".join(formatted_courses)

    user_content = (
        f"User Goal: **{query}**\n\n"
        "Here is a list of candidate courses:\n\n"
        f"{course_list_text}\n\n"
        "Please recommend the top **3** courses based on this goal.\n"
        "For each, include:\n"
        "  - Title\n"
        "  - Rationale and alignment with the goal\n"
        "  - Duration and difficulty\n"
        "  - Summary of learner feedback (if applicable)\n\n"
        "If any key information is missing, ask a single concise follow-up question."
    )
    user_msg = {"role": "user", "content": user_content}

    messages = [system_msg, *chat_history, user_msg]
    full_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        do_sample=True
    )

    prompt_len = inputs["input_ids"].shape[-1]
    gen_tokens = outputs[0, prompt_len:]
    return tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()


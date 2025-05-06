import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

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
    courses: list[dict],
    chat_history: list[dict[str, str]],
    model,
    tokenizer,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9
) -> str:
    """
    Given:
      - a new user query (learning goal),
      - a list of candidate course descriptions,
      - and the prior chat history,
    construct the full chat prompt and return the model’s answer.
    """

    system_msg = {
        "role": "system",
        "content": (
            "You are an expert academic course recommendation assistant. "
            "When given a user’s learning objective and a collection of course metadata, you should:\n"
            "  1. Evaluate each course’s relevance to the learning objective using title, description, and tags.\n"
            "  2. Compare courses by difficulty level, estimated duration, learner engagement, and ratings, handling missing values gracefully.\n"
            "  3. Recommend the top three courses, providing for each:\n"
            "     - Title\n"
            "     - Key strengths vs. alternatives\n"
            "     - Estimated duration and difficulty level\n"
            "     - Summary of learner feedback (e.g. rating and number of ratings) if available\n"
            "  4. Suggest follow-up questions only if essential context is missing."
        )
    }

    # Build a formatted list of courses with metadata
    formatted_courses = []
    for idx, c in enumerate(courses, start=1):
        parts = [f"{idx}. {c.get('title', 'Untitled Course')}"]
        if desc := c.get('description'):
            parts.append(f"Description: {desc}")
        if duration := c.get('duration'):
            parts.append(f"Duration: {duration}")
        if learners := c.get('learners') is not None:
            parts.append(f"Learners: {c['learners']}")
        if rating := c.get('rating') is not None:
            rating_info = f"Rating: {c['rating']} / 5"
            if c.get('ratings_count'):
                rating_info += f" ({c['ratings_count']} ratings)"
            parts.append(rating_info)
        if tags := c.get('tags'):
            parts.append(f"Tags: {', '.join(tags)}")
        formatted_courses.append("\n".join(parts))
    course_list_text = "\n\n".join(formatted_courses)

    # User prompt incorporating course metadata
    user_content = (
        f"I would like to **{query}**. Below are candidate courses with metadata:\n\n"
        f"{course_list_text}\n\n"
        "Please:\n"
        "  • Identify and recommend the top **3** courses for this objective.\n"
        "  • For each, provide:\n"
        "      – Title\n"
        "      – Rationale for selection, highlighting strengths\n"
        "      – Estimated duration, difficulty level\n"
        "      – Learner feedback summary (if available)\n"
        "  • If necessary, ask one concise follow-up question to clarify my background or constraints.\n"
        "\nAnswer in clear, numbered bullet points using formal academic tone."
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
    generated = outputs[0, prompt_len:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


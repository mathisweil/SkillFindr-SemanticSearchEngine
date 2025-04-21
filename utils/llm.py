import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Tuple, List

def load_llm_model(
    model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
    torch_dtype: torch.dtype = torch.bfloat16,
    device_map: str | dict = "auto",
    trust_remote_code: bool = True
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
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
    contexts: List[str],
    model,
    tokenizer,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.9
) -> str:
    """
    Given a user query and a list of contexts, build the chat
    prompt and return the model’s answer.
    """
    system_msg = {
        "role": "system",
        "content": (
            "You are an expert course‑recommendation assistant. "
            "When given a user’s learning goal and a set of course descriptions, "
            "you should:\n"
            "  1. Identify which courses best align with the goal.\n"
            "  2. Compare them on difficulty, duration, and learner feedback.\n"
            "  3. Recommend the top 3, giving a brief rationale for each.\n"
            "  4. If you need more context (e.g. user background), ask a follow‑up question."
        )
    }

    user_content = (
        f"I want to **{query}**. Here are the candidate courses:\n\n"
        + "\n\n".join(f"{i+1}. {c}" for i, c in enumerate(contexts))
        + (
            "\n\nPlease:\n"
            "  • Rank and recommend the **3 best** courses to achieve my goal.\n"
            "  • For each recommendation, include:\n"
            "      – Course title\n"
            "      – Why it’s a good fit (strengths vs. others)\n"
            "      – Estimated duration and level\n"
            "  • If you need more details about me, ask one clarifying question.\n"
            "\nAnswer in clear, numbered bullet points."
        )
    )
    user_msg = {"role": "user", "content": user_content}

    full_prompt = tokenizer.apply_chat_template(
        [system_msg, user_msg],
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

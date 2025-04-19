from fastapi import FastAPI

app = FastAPI()

prompt_template = jinja_env.get_template("course_prompt.j2")


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/rag")
async def answer(query: str, filters: dict):
    courses = vector_store.similarity_search(question, k=k, filter={"lang": "en"})

    prompt = prompt_template.render(
        question=question,
        docs=docs,
        max_results=3,
    )

    # Hugging Face Inference API
    gen = client.text_generation(prompt, stream=True, max_new_tokens=512)
    return StreamingResponse(gen, media_type="application/json")
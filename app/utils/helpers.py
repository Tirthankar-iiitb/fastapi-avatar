from groq import Groq
import os

os.environ["GROQ_API_KEY"] = os.environ.get('GROQ_KEY')
os.environ["LLAMAINDEX_API_KEY"]=os.environ.get('LLAMAINDEX_KEY')
os.environ["LLAMA_CLOUD_API_KEY"]=os.environ.get('LLAMAINDEX_KEY')

client=Groq()

def replyback(user_sentence):
    completion = client.chat.completions.create(
        model="Llama-3.3-70b-versatile",
        #meta-llama/Meta-Llama-3-8B
        messages=[
            {
                "role": "system",
                "content": "\n"
            },
            {
                "role": "user",
                # "content": f"Give a reasonable short response to the given sentence: \
                # {user_sentence}"
                "content": f": Give a short response to the following sentence:\
                    {user_sentence}"
            }
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )

    # Collect the corrected text from the streamed response
    reply_text = ""
    for chunk in completion:
        reply_text += chunk.choices[0].delta.content or ""

    return reply_text


def modify_text(text):
    newtext=f'Give me some time. I will revert on your query: "{text}"'
    return newtext


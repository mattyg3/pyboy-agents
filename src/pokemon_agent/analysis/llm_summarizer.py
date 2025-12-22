import lmstudio as lms
from typing import Any, TypedDict
from langgraph.graph import StateGraph, END
import json
import pandas as pd

llm = lms.llm("google/gemma-3-4b")



with open('src/pokemon_agent/saves/agent_states/goals_agent_state.json', 'r', encoding="utf-8") as f:
    response_dict = json.load(f)

# 
# messages=[]
thoughts=[]
# for msg in response_dict["messages"]:
#     messages.append(msg["content"])
for thought in response_dict["goals_thoughts"]:
    thoughts.append(thought["content"])

# print(f"{len(messages)}; {len(thoughts)}")
response_pdf = pd.DataFrame({'thoughts': thoughts})

summary_list=[]
index=[]
counter=0
for val in response_pdf["thoughts"]:
    sys_prompt = f"""
    # Role & Task
    You are tasked with summarizing another LLM's thought process. Summarize the provided text in 200 words or less.

    # Thought to Summarize
    {val}

    # Output
    **ONLY** summarized response
    """
    result = llm.respond(sys_prompt)
    summary_list.append(result.content)
    index.append(counter)
    counter+=1

response_pdf["index"] = index
response_pdf["summaries"] = summary_list

# print(response_pdf["summaries"])

output_path = 'src/pokemon_agent/analysis/llm_thoughts_summarized.csv'
response_pdf.to_csv(output_path, index=False)

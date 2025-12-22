from llm_summarizer import * #run llm summary

import pandas as pd
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 0)

def to_string_pretty(obj, width=120):
    if isinstance(obj, pd.Series):
        return obj.to_frame().to_string(line_width=width)
    return obj.to_string(line_width=width)


pdf = pd.read_csv('src/pokemon_agent/analysis/llm_thoughts_summarized.csv')
# print(to_string_pretty(pdf["summaries"]))
print(to_string_pretty(pdf))


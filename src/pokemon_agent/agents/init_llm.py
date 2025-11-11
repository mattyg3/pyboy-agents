# # OpenAI
# import os
# import keyring
# from langchain_openai import ChatOpenAI
# os.environ["OPENAI_API_KEY"] = keyring.get_password('openai', 'api_key')
# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# # Ollama
# from langchain_ollama import ChatOllama
# llm = ChatOllama(model="gemma3:4b", temperature=1.0, top_k = 64, top_p = 0.95 , validate_model_on_init=True)  #can use pydantic BaseModel for structured output

# # ====== Tool Enabled LLMs ======
# tool_calling_llm = ChatOllama(model="gpt-oss:20b", validate_model_on_init=True)

# LM STUDIO
import lmstudio as lms
# llm_model = lms.llm("qwen/qwen3-4b-thinking-2507") 
llm_model = lms.llm("qwen/qwen3-4b-thinking-2507@q4_k_m")
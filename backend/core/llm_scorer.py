from ollama import Client
import json


ollama_client = Client(host='http://localhost:11434')  # Adjust if needed

def score_resume_with_gemma(resume_text: str, jd_text: str, llm_prompt: str):

    try:
        response = ollama_client.chat(
            model='gemma3:12b',
            messages=[
                {'role': 'user', 'content': llm_prompt}
            ],
            options={
                'temperature': 0.1,
                'seed': 42
            }
        )
        raw_output = response['message']['content']

        # Attempt to locate JSON in the output
        json_start = raw_output.find('{')
        json_end = raw_output.rfind('}')
        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_str = raw_output[json_start: json_end + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"[LLM Scorer] JSON decode error: {e}")
                return {
                    "error": "Failed to parse LLM response as JSON",
                    "details": str(e),
                    "raw_output": raw_output
                }
        else:
            print("[LLM Scorer] No valid JSON structure found.")
            return {
                "error": "No valid JSON structure found in LLM response",
                "raw_output": raw_output
            }

    except Exception as e:
        print(f"[LLM Scorer] Exception during LLM call: {e}")
        return {"error": f"LLM processing failed: {e}"}

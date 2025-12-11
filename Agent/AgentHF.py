import os
import re
from huggingface_hub import InferenceClient
from colorama import init, Fore, Style

init(autoreset=True)

class HuggingFace:
    def __init__(self, API_Token: str, model: str = "deepseek-ai/DeepSeek-R1"):
        self.model = model
        self.client = InferenceClient(token= API_Token)

    def chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 256, temperature: float = 0.2) -> str:
        payload = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            raw_answer = self._send_request(payload, max_tokens=max_tokens, temperature=temperature)
            return raw_answer
        except Exception as exc:
            print(f"{Fore.RED}[ERROR contacting HuggingFace] {exc}{Style.RESET_ALL}")
            return "error"
        
    def ai_answer(self, answer: str):
        print(f"{Fore.LIGHTYELLOW_EX}[HF]:\n{answer}{Style.RESET_ALL}")
        
    def _send_request(self, messages: list, max_tokens: int = 256, temperature: float = 0.2) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        raw_output = response.choices[0].message.content.strip()
        cleaned = re.sub(r"<think>.*?</think>", "", raw_output, flags=re.DOTALL).strip()
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        return cleaned

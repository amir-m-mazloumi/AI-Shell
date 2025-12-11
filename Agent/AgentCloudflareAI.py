import os
import re
import requests
from colorama import init, Fore, Back, Style

init(autoreset=True)

class CloudflareAI:
    def __init__(self, account_id: str, api_token: str, model: str = "@cf/meta/llama-3.1-8b-instruct"):
        if not account_id or not api_token:
            raise ValueError("CLOUDFLARE_ACCOUNT_ID & CLOUDFLARE_API_TOKEN most have value.")

        if len(account_id) != 32 or not all(c in "0123456789abcdef" for c in account_id.lower()):
            raise ValueError("Account ID most have 32 value (a-z) (0-9).")

        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id.strip()}/ai/run/{model}"
        self.headers = {
            "Authorization": f"Bearer {api_token.strip()}",
            "Content-Type": "application/json",
        }

    def Chat(self, system_prompt: str, user_prompt: str,max_tokens: int = 128, temperature: float = 0.2) -> str:
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            raw_answer = self._send_request(payload).lower()
            return raw_answer
        except Exception as exc:
            print(f"{Fore.RED}[ERROR contacting Cloudflare Workers AI] {exc}{Style.RESET_ALL}")
            return "error"

    def ai_answer(self, answer :str) -> str:
        print(f"{Fore.LIGHTYELLOW_EX}[CloudflareAI]:\n{answer}{Style.RESET_ALL}")

    def _send_request(self, payload: dict) -> str:
        response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=60)
        response.raise_for_status()
        raw_answer = response.json()["result"]["response"].strip()
        cleaned_answer = re.sub(r"<think>.*?</think>", "", raw_answer, flags=re.DOTALL).strip()
        text = re.sub(r'^```[a-zA-Z]*\n?', '', cleaned_answer, flags=re.MULTILINE)
        final_raw_text = re.sub(r'\n?```$', '', text)
        return final_raw_text
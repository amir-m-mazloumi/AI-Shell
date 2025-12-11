import argparse
import os
import sys
import json
import platform
import subprocess
import re
from pathlib import Path
from colorama import init, Fore, Back, Style

init(autoreset=True)

CONFIG_FILE = Path.home() / ".ai_shell_config.json"

def load_or_create_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        print(f"{Fore.CYAN}First-time setup. Please provide your API credentials.{Style.RESET_ALL}")
        config = {}
        config['hf_token'] = input("HuggingFace API Token: ").strip()
        config['cf_account_id'] = input("Cloudflare Account ID: ").strip()
        config['cf_api_token'] = input("Cloudflare API Token: ").strip()
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        print(f"{Fore.GREEN}Configuration saved to {CONFIG_FILE}{Style.RESET_ALL}")
        return config

class Controller:
    def __init__(self, agent_name: str, config: dict, model: str = "@cf/meta/llama-3.1-8b-instruct"):
        os_info = platform.system().lower()
        processor = platform.processor()
        try:
            term = os.environ.get('TERM', 'unknown')
        except:
            term = 'unknown'
        
        self.os_info = os_info
        self.processor = processor
        self.term = term
        self.base_info = f"""OS: {os_info}
                            Architecture/CPU: {processor}
                            Terminal: {term}"""
        
        if agent_name == "HF" and model == "@cf/meta/llama-3.1-8b-instruct":
            model = "deepseek-ai/DeepSeek-R1"
        
        self.chat_system_prompt = f"""You are a helpful, conversational AI assistant knowledgeable in computing, CLI tasks, scripting, troubleshooting, and general topics.
                    {self.base_info}
                    Respond naturally, concisely, and helpfully to the user's messages. When providing commands or scripts, be precise and compatible with the system above."""
        
        self.command_system_prompt = f"""You are an expert CLI command generator.
                    {self.base_info}
                    Respond to the user's request with ONLY the exact, executable command line. Absolutely no explanations, introductions, markdown, or extra text. Ensure full compatibility with the specified OS and terminal."""
        
        self.script_system_prompt = f"""You are an expert script writer for the given OS.
                    {self.base_info}
                    Respond to the user's request with ONLY the complete, executable script content. Include appropriate shebang for Unix-like systems or start with @echo off for Windows batch files. No explanations, no markdown, no extra text. Make it self-contained and ready to run."""
        
        self.troubleshoot_system_prompt = f"""You are an expert system troubleshooter.
                    {self.base_info}
                    Given the user's issue description and the provided system context (files, processes, etc.), respond with ONLY a sequence of diagnostic and fix commands or a short script, one per line, prefixed with numbers (e.g., 1. command). No introductory text, no explanations, just the actionable steps."""

        if agent_name == "CF":
            from Agent.AgentCloudflareAI import CloudflareAI
            self.agent = CloudflareAI(config['cf_account_id'], config['cf_api_token'], model)
            self.agent_name = agent_name
        elif agent_name == "HF":
            from Agent.AgentHF import HuggingFace
            self.agent = HuggingFace(config['hf_token'], model)
            self.agent_name = agent_name
        else:
            raise ValueError("Invalid agent name. Use 'CF' or 'HF'.")

    def get_ai_response(self, user_prompt: str, system_prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        if hasattr(self.agent, 'Chat'):
            response = self.agent.Chat(system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature)
        else:
            response = self.agent.chat(system_prompt, user_prompt, max_tokens=max_tokens, temperature=temperature)
        if response == "error":
            print(f"{Fore.RED}[ERROR] Issue connecting to AI.{Style.RESET_ALL}")
            return ""
        return response.strip()

    def shell_chat(self):
        while True:
            try:
                user_input = input(f"{Fore.CYAN}AI_Shell> {Style.RESET_ALL}").strip()
                if not user_input:
                    continue
                if user_input.lower() in ['exit', 'quit']:
                    print(f"{Fore.YELLOW}[EXIT] Goodbye!{Style.RESET_ALL}")
                    break
                
                response = self.get_ai_response(user_input, self.chat_system_prompt)
                if response:
                    self.agent.ai_answer(response)
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}[EXIT] Stopped with Ctrl+C.{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}[ERROR] {e}{Style.RESET_ALL}")

    def run_command(self, user_prompt: str):
        response = self.get_ai_response(user_prompt, self.command_system_prompt)
        if not response:
            return
        if not re.match(r'^(?!<).+?(?<!\n)$', response, re.MULTILINE):
            print(f"{Fore.RED}[ERROR] Invalid command response.{Style.RESET_ALL}")
            return
        confirm = input(f"{Fore.YELLOW}Execute: {response}\nYes/No? {Style.RESET_ALL}").strip().lower()
        if confirm in ['yes', 'y']:
            try:
                os.system(response)
            except Exception as e:
                print(f"{Fore.RED}[ERROR executing] {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[CANCELLED]{Style.RESET_ALL}")

    def save_script(self, user_prompt: str):
        response = self.get_ai_response(user_prompt, self.script_system_prompt)
        if not response:
            return
        os_info = self.os_info
        current_dir = Path.cwd()
        if os_info == 'linux' or os_info == 'darwin':
            ext = '.sh'
            filename = current_dir / f"script{ext}"
        else:
            ext = '.bat'
            filename = current_dir / f"script{ext}"
        
        script_content = response
        with open(filename, 'w') as f:
            f.write(script_content)
        if ext == '.sh':
            os.chmod(filename, 0o755)
        print(f"{Fore.GREEN}Script saved to {filename}{Style.RESET_ALL}")

    def troubleshoot(self, user_prompt: str):
        current_dir = Path.cwd()
        file_summary = []
        for root, dirs, files in os.walk(current_dir):
            file_summary.append(f"{root}: {len(files)} files, {len(dirs)} dirs")
            if len(file_summary) > 10:
                file_summary.append("... (truncated)")
                break

        try:
            if self.os_info == 'windows':
                proc_output = subprocess.check_output(['tasklist'], text=True)
            else:
                proc_output = subprocess.check_output(['ps', 'aux'], text=True)
            proc_summary = proc_output.split('\n')[:10]
        except:
            proc_summary = ["Unable to fetch processes."]
        
        cpu_info = f"CPU: {self.processor}"
        
        full_user_prompt = f"{user_prompt}\n\nSystem files summary:\n" + '\n'.join(file_summary) + \
                      f"\n\nActive processes (top):\n" + '\n'.join(proc_summary) + \
                      f"\n\n{cpu_info}"
        
        response = self.get_ai_response(full_user_prompt, self.troubleshoot_system_prompt)
        if response:
            self.agent.ai_answer(response)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AI-powered interactive chat shell",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--model", type=str, default="@cf/meta/llama-3.1-8b-instruct", help="AI model to use")
    parser.add_argument("--use-hf", action="store_true", help="Use HuggingFace instead of Cloudflare")
    parser.add_argument("--r", "--run", nargs='?', const=True, help="Run mode: provide prompt as arg or input")
    parser.add_argument("--s", "--script", nargs='?', const=True, help="Script mode: save output as script")
    parser.add_argument("--c", "--chat", action="store_true", help="Chat mode: interactive shell")
    parser.add_argument("--t", "--troubleshoot", nargs='?', const=True, help="Troubleshoot mode: provide issue as arg or input")
    args = parser.parse_args()

    config = load_or_create_config()
    agent_name = "HF" if args.use_hf else "CF"
    controller = Controller(agent_name, config, args.model)
    try:
        if args.c:
            controller.shell_chat()
        elif args.r is not None:
            prompt = args.r if args.r is not True else input(f"{Fore.CYAN}Prompt for run: {Style.RESET_ALL}").strip()
            if prompt:
                controller.run_command(prompt)
        elif args.s is not None:
            prompt = args.s if args.s is not True else input(f"{Fore.CYAN}Prompt for script: {Style.RESET_ALL}").strip()
            if prompt:
                controller.save_script(prompt)
        elif args.t is not None:
            prompt = args.t if args.t is not True else input(f"{Fore.CYAN}Describe the issue: {Style.RESET_ALL}").strip()
            if prompt:
                controller.troubleshoot(prompt)
        else:
            controller.shell_chat()
    except AttributeError as e:
        print(f"{Fore.RED}[ERROR] Invalid argument: {e}{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}[ERROR] {e}{Style.RESET_ALL}")
        sys.exit(1)
# AI-Shell
AI-Shell Helps You Remember And Generate Shell Commands On Any Platform.

## Overview
AI-Shell is a cross-platform command-line assistant powered by artificial intelligence.
It converts natural language descriptions into real shell commands, helping you work faster without memorizing complex syntax.

## Features
- Generate shell commands using natural language
- Supports Windows, Linux, and macOS
- Increases productivity inside the terminal
- Helps beginners learn shell commands step-by-step

## Installation

Clone the repository:

    git clone https://github.com/amir-m-mazloumi/AI-Shell.git
    cd AI-Shell

Install required packages:

    pip install -r requirements.txt

## API Setup
You need two free API keys:
1. Cloudflare Workers AI (Account ID + API Token)
2. HuggingFace API Token

The application primarily uses Cloudflare for inference.
Optionally, you can switch to HuggingFace via the --use-hf flag.

## Building Executables (Optional)
For convenience, you can build a standalone binary using PyInstaller:

    pyinstaller -i "NONE" --onefile ai.py

Then place the generated executable in your system PATH
so you can access it globally from any shell.

## Usage

Basic usage:

    ai

Program help:

    ai -h

Available modes:

usage:

     ai [-h] [--model MODEL] [--use-hf] [--r [R]] [--s [S]] [--c] [--t [T]]

AI-powered interactive chat shell

options:

  -h, --help            show this help message and exit

  --model MODEL         AI model to use (default: @cf/meta/llama-3.1-8b-instruct)

  --use-hf              Use HuggingFace instead of Cloudflare (default: False)

  --r, --run [R]        Run mode: provide prompt as arg or input (default: None)

  --s, --script [S]     Script mode: save output as script (default: None)

  --c, --chat           Chat mode: interactive shell (default: False)

  --t, --troubleshoot [T]
                        Troubleshoot mode: provide issue as arg or input (default: None)

NOTE:
    you can use any MODEL you want ,provide in Cloudflare and HuggingFace.
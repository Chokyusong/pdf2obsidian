# Ollama Setup Guide for PDF2Obsidian

This guide is for beginners who want to use optional local AI for lecture reconstruction Markdown.

PDF2Obsidian works without Ollama. Ollama is only needed when you choose `Local AI (Ollama)`.

## What Ollama Does

Ollama runs an AI model on your own computer.

When used with PDF2Obsidian:

1. Your transcript file stays on your PC.
2. PDF2Obsidian cleans and prepares the transcript.
3. Ollama reconstructs it locally.
4. PDF2Obsidian writes an Obsidian Markdown study material.

Local AI output is saved as the final Markdown returned by Ollama. PDF2Obsidian does not wrap the AI result in a second template.

## Step 1. Automatic Setup

1. Open PDF2Obsidian.
2. Set `AI Mode` to `Local AI (Ollama)`.
3. Click `Auto Install Ollama`.
4. Confirm the setup message.
5. If Windows shows a permission prompt, approve it.
6. Wait while Ollama and the selected model are installed.

PDF2Obsidian first tries `winget`. If that fails, it downloads and runs the official Ollama installer.

Automatic setup starts only after the user clicks the setup button and confirms the prompt.

## Step 2. Check Ollama in PDF2Obsidian

1. Open PDF2Obsidian.
2. Find the `Ollama status` row.
3. Click `Check Ollama`.

Expected result:

```text
Running
```

If it says `Not detected`, start Ollama from the Windows Start menu and try again.

## Step 3. Choose or Refresh a Model

PDF2Obsidian reads installed Ollama models automatically from your PC.

Click:

```text
Refresh Models
```

Recommended model:

```text
qwen2.5:7b
```

Use `qwen2.5:7b` for better lecture reconstruction quality. Use `qwen2.5:3b` only when your PC is slow or memory is limited.

Ollama runs locally for free after installation, but conversion speed and output
quality depend on the selected model and the user's hardware. PDF2Obsidian's
default Local AI conversion saves the first cleaned result instead of running
slow repeated retries.

Large experimental models such as `qwen3.6` are not recommended for most users.
They can require much more memory and may be slow or unstable during repeated
lecture reconstruction.

## Step 4. Download a Model

In PDF2Obsidian:

1. Choose a model in the model box, or type a model name directly.
2. Click `Pull Model`.
3. Wait until the download finishes.

Model downloads can take time. Larger models need more disk space.

## Step 5. Use Local AI

1. Add an SRT, VTT, TXT, or Markdown transcript file.
2. Set `AI Mode` to `Local AI (Ollama)`.
3. Set `Output Mode` to `Lecture Reconstruction MD`.
4. Click `Start conversion`.

If Ollama is not running or the selected model is unavailable, conversion stops and shows an error. It does not silently fall back to `Basic (No AI)`.

## Manual Install Fallback

If automatic setup fails:

1. Click `Open Manual Install Page`.
2. Download Ollama from <https://ollama.com/download>.
3. Run the installer.
4. Start Ollama.
5. Return to PDF2Obsidian and click `Check Ollama`.

## Optional: Store Models on HDD

The Ollama program can stay on your SSD while model files are stored on another drive.

On Windows, the default model folder is:

```text
%USERPROFILE%\.ollama\models
```

To use another folder, set a Windows user environment variable:

```text
OLLAMA_MODELS=D:\OllamaModels
```

Then restart Ollama.

HDD storage works, but models may load more slowly. SSD is faster.

## Troubleshooting

### Check Ollama says Not detected

Try this:

1. Start Ollama from the Windows Start menu.
2. Wait a few seconds.
3. Click `Check Ollama` again.

### Model Pull does not work

Check:

1. Internet is connected.
2. Ollama status is `Running`.
3. The model name is typed correctly.

Example:

```text
qwen2.5:3b
```

### My PC is slow

Use a smaller model first:

```text
qwen2.5:3b
```

Close other heavy programs before running local AI.

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

## Step 1. Install Ollama

1. Open the official download page:
   <https://ollama.com/download>
2. Download the Windows installer.
3. Run the installer.
4. Start Ollama from the Windows Start menu.

PDF2Obsidian does not install Ollama automatically.

## Step 2. Check Ollama in PDF2Obsidian

1. Open PDF2Obsidian.
2. Find the `Ollama status` row.
3. Click `Check Ollama`.

Expected result:

```text
Running
```

If it says `Not detected`, start Ollama from the Windows Start menu and try again.

## Step 3. Choose a Model

Recommended beginner model:

```text
qwen2.5:3b
```

Other options:

```text
llama3.2:3b
qwen2.5:7b
```

Use `qwen2.5:3b` first. It is smaller and easier to test.

## Step 4. Download a Model

In PDF2Obsidian:

1. Choose `qwen2.5:3b` in the model box.
2. Click `Pull Model`.
3. Wait until the download finishes.

Model downloads can take time. Larger models need more disk space.

## Step 5. Use Local AI

1. Add an SRT, VTT, TXT, or Markdown transcript file.
2. Set `AI Mode` to `Local AI (Ollama)`.
3. Set `Output Mode` to `Lecture Reconstruction MD`.
4. Click `Start conversion`.

If Ollama is not running or the selected model is unavailable, conversion stops and shows an error. It does not silently fall back to `Basic (No AI)`.

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

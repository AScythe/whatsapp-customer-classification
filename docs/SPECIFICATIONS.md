# Specifications — WhatsApp Customer Lead Pipeline

> **Last verified:** 2026-06-24 12:30 EDT

## Problem

Sales teams running product campaigns receive hundreds of WhatsApp messages daily — questions, voice notes, purchase requests, complaints. Manually reading every chat to identify which customers are ready to buy is slow, error-prone, and doesn't scale. Darija voice messages add a language barrier that most text-based tools can't handle.

## Solution

An automated 6-step pipeline that ingests raw WhatsApp exports, extracts conversations, decodes media, transcribes Darija voice notes into text, builds a compact LLM-ready context file, and classifies each customer into a lead tier — all without sending data to external APIs.

## How It Works

1. **Place a WhatsApp export** as a JSON file in the `whatsapp_raw_messages/` folder
2. **Run extraction** — the pipeline reads the export, separates messages into hourly JSONL files, and tracks what's been processed
3. **Decode media** — embedded voice messages, images, and documents are decoded from base64 to local files
4. **Transcribe voice notes** — Darija audio is transcribed using a fine-tuned Whisper model, adding text transcripts to each voice message
5. **Build customer context** — all messages and transcripts are merged into a single plain-text file, one line per message
6. **Classify the lead** — a Qwen3.5 LLM reads the context and returns a tier: HOT_LEAD (ready to buy), EXISTING_CUSTOMER (post-purchase inquiry), or COLD_LEAD (browsing)

## Core Features

- **Darija voice transcription** — fine-tuned Whisper model (`ychafiqui/whisper-medium-darija`) transcribes Moroccan Arabic voice notes. Rationale: Darija is an oral dialect with limited ASR support; generic speech-to-text models perform poorly, making manual listening the only alternative.

- **Idempotent re-runs** — every step tracks timestamps and skips already-processed data. Rationale: campaign conversations span days or weeks; users should be able to re-run the pipeline incrementally without duplicating work.

- **Local-first architecture** — all processing runs on the user's machine. No data leaves the local environment. Rationale: WhatsApp message data contains PII (phone numbers, names, conversation content); shipping it to third-party APIs introduces privacy and compliance risk.

- **Model flexibility** — two model sizes (2B CPU-compatible, 4B GPU-required) for the classification LLM. Rationale: users without a GPU can still classify leads locally using the 2B model (~5GB RAM), while GPU-equipped machines can use the more capable 4B variant.

- **Interactive voice message player** — a CLI browser to browse days and play voice messages. Rationale: users may want to manually review specific audio before or after transcription for quality assurance.

## Privacy First

| Concern | How It's Handled |
|---------|------------------|
| Message content | Stored locally in `*_chat_archives/` — excluded from version control |
| Phone numbers | Used only as folder identifiers — never transmitted |
| Voice messages | Decoded and transcribed locally — no audio leaves the machine |
| Classification | LLM runs on local hardware — no API calls to external services |
| User control | All data can be deleted by removing the chat archives folder |

### Hard Constraints

- The pipeline has **no telemetry, no analytics, no phone-home mechanism**
- `whatsapp_raw_messages/` and `*_chat_archives/` are in `.gitignore` — cannot be accidentally committed
- All model inference runs on local CPU or GPU — no cloud dependency for classification

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-language transcription | The Whisper model is fine-tuned specifically for Darija; other dialects or languages are not supported |
| Sentiment analysis | The classifier outputs lead tier, not sentiment — these are distinct axes |
| Automated reply / chatbot | The pipeline is analysis-only; it does not send messages to customers |
| Real-time ingestion | The pipeline processes exported JSON files, not live WhatsApp API streams |
| Cloud / SaaS deployment | By design; local-first is a privacy requirement, not a technical limitation |

## Why Users Love It

| Before (manual) | After (pipeline) |
|-----------------|------------------|
| Read every WhatsApp chat to find hot leads | Pipeline classifies all leads automatically |
| Listen to every voice message to understand intent | Darija Whisper model transcribes voice to text |
| Keep mental notes on which customer is where | Each classification is saved to a timestamped result file |
| Re-process everything when new messages arrive | Idempotent — only new messages are processed |
| Worry about data privacy with cloud tools | Everything runs locally, no data leaves the machine |

## Tech Stack

### Architecture Overview

A series of standalone Python scripts that pass data through the filesystem — each script reads from and writes to `*_chat_archives/` directories. There is no server, no database, and no API layer. The classification LLM (Qwen3.5) and transcription model (Whisper) are loaded locally via the Transformers library.

### Technology Table

| Layer | Technology | Why |
|-------|------------|-----|
| Runtime | Python 3.12+ | Universal, zero-config on most machines; scripts are standalone with no framework overhead |
| LLM inference | PyTorch + Transformers | Industry standard for local model loading; supports both CPU and GPU without code changes |
| Darija transcription | ychafiqui/whisper-medium-darija | One of few publicly available models fine-tuned for Moroccan Arabic; runs locally via Transformers pipeline |
| Lead classification | Qwen3.5 (2B / 4B) | Strong instruction-following and JSON output capabilities for structured classification; 2B variant fits in ~5GB RAM for CPU usage |
| Classification prompt | YAML (`prompts/classify_customer.yaml`) | Prompt is version-controlled and editable without touching Python code — enables prompt engineering iterations |

### Product Decisions

| Decision | Why |
|----------|-----|
| Filesystem-based data passing instead of a database | Keeps each script independently runnable and debuggable; JSONL is human-readable and trivially inspectable |
| Separate scripts instead of a unified CLI | Each step has a distinct purpose and optionality (e.g., playing voice messages is entirely optional); users run only what they need |
| Timestamp-based idempotency instead of hash-based | Timestamps are natural keys in message data; hash comparison would require storing hashes of every message body |
| Plain-text context file instead of structured format | LLMs consume plain text more naturally than JSON/structured data; reduces token count and prompt engineering complexity |

## Pitch

Thousands of WhatsApp messages, one hot lead? Find it without reading every chat. Automatically extract, transcribe, and classify every lead into sales-ready tiers. All on your machine, zero manual review.

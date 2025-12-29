# inkbloom

Inkbloom is a package that allows users to add illustrations to their (open, non-kindle) ebooks. The software produces consistent illustrations showing characters and scenes seamlessly throughout the book.

## Overview

Inkbloom uses a generative image model to automatically generate and insert illustrations into EPUB ebooks. It analyzes each chapter to extract character and scene descriptions, then generates contextually appropriate images in your chosen style.

Example expired U.S. Copyright epubs are included in the repo to play with, from Project Gutenberg.

Here are some example chapter illustrations created by DALL-E 3 for Grimm's Fairy Tales.
    <img src="resources/chapter_0_illustration.png" width="50%" alt="Generated Illustration for Grimm's Fairy Tales Chapter 0" />
    <img src="resources/chapter_3_illustration.png" width="50%" alt="Generated Illustration for Grimm's Fairy Tales Chapter 3" />

## Features

- Automatically extracts character and scene descriptions from chapters using Anthropic's Claude
- Generates AI illustrations using OpenAI's DALL-E 3
- Maintains consistency across illustrations throughout the book
- Supports custom illustration styles
- Creates a new EPUB with illustrations embedded

## Requirements

- Python 3.x
- API keys for:
  - Anthropic (Claude API)
  - OpenAI (DALL-E API)

## Installation

Install the required dependencies:

```bash
pip install anthropic ebooklib beautifulsoup4 openai requests pillow pyyaml
```

## Setup

Create API key files in `~/.secret/`:

1. Create `anthropic_api_key.json`:
```json
{
  "SECRET_KEY": "your-anthropic-api-key-here"
}
```

2. Create `openai_api_key.json`:
```json
{
  "SECRET_KEY": "your-openai-api-key-here"
}
```

## Usage

Run inkbloom from the command line:

```bash
python inkbloom.py <ebook_file> <style>
```

### Arguments

- `ebook_file`: Path to your EPUB file
- `style`: The artistic style for illustrations (e.g., "watercolor", "oil painting", "cartoon", "pencil sketch")

### Example

```bash
python inkbloom.py "my_book.epub" "watercolor"
```

This will:
1. Read and analyze each chapter of `my_book.epub`
2. Extract character and scene descriptions
3. Generate watercolor-style illustrations for each chapter
4. Create a new file: `my_book WITH PICTURES.epub`

## How It Works

1. **Chapter Analysis**: Claude AI analyzes each chapter to identify character physical descriptions and scenes
2. **Scene Selection**: The AI selects the most representative scene from each chapter
3. **Prompt Generation**: Creates detailed image generation prompts combining character descriptions with scene context
4. **Image Generation**: DALL-E 3 generates illustrations based on the prompts
5. **EPUB Creation**: Illustrations are inserted at the beginning of each chapter (after the chapter heading)
6. **Output**: A new EPUB file is created with " WITH PICTURES" appended to the original filename

## Notes

- Illustrations are generated for chapters longer than 1000 characters
- Title pages and blank pages are skipped
- All content is filtered to be appropriate for children's books
- Images are saved as PNG files (1024x1024 pixels)
- The process uses API calls which may incur costs

## Generated Files

During execution, the following files are created:
- `chapter_N_illustration.png`: Individual illustration files for each chapter
- `<original_filename> WITH PICTURES.epub`: The final ebook with illustrations

## Limitations

- Only works with EPUB format
- Requires active internet connection for API calls
- API rate limits may affect processing speed
- Image generation costs apply based on OpenAI pricing

## Ideas for Future Improvements

- Support for different ebook formats
- Multi-language support with translation
- Additional image style options
- Batch processing multiple books
- Character consistency tracking across chapters

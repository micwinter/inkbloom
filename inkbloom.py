"""Main script for adding generated illustrations to e-books"""

import anthropic
from bs4 import BeautifulSoup
from ebooklib import epub
import json
from openai import OpenAI

# from transformers import AutoTokenizer, pipeline
from typing import List, Tuple, Dict
import yaml


# TODO: Assert that input file is an epub.
# TODO: Extract non english text and translate? Filter out?
# TODO: Add ability to generate different image styles.
# TODO: Do something fancy with YAMLS - aggregate them over the book?

class EpubReader:
    def __init__(
        self,
        ebook_filepath: str,
    ):
        self.ebook_filepath = ebook_filepath
        self.book = epub.read_epub(ebook_filepath)
        self.book_items = [x for x in self.book.get_items()]
        self.batch_size = 16
        self.load_keys()
        self.description_dict = {}

    def load_keys(self):
        """Load API keys"""
        with open("/Users/minty/.secret/anthropic_api_key.json") as f:
            self.claude_key = json.load(f)["SECRET_KEY"]
        with open("/Users/minty/.secret/openai_api_key.json") as f:
            self.openai_key = json.load(f)["SECRET_KEY"]

    def chapter_to_str(self, chapter):
        """Convert body content of chapters into strings"""
        soup = BeautifulSoup(chapter.get_body_content(), "html.parser")
        text = [para.get_text() for para in soup.find_all("p")]
        return "" "".join(text)

    def read_chapters(self):
        """Read chapters from ebook into list of strings"""
        self.chapters = [
            self.chapter_to_str(x)
            for x in self.book_items
            if (
                hasattr(x, "is_chapter")
                and x.is_chapter()
                and hasattr(x, "get_body_content")
                and 
            )
        ]

    def clean_passage(self, passage: str):
        """Clean up text in a string"""
        passage = passage.replace("<br />", "")
        passage = passage.replace("\n", "")
        passage = passage.replace("....", "")
        passage = passage.replace("...", "")
        passage = passage.replace("\t", "")
        passage = passage.replace("\xa0", "")
        passage = passage.replace("    ", "")
        passage = passage.replace("   ", "")
        passage = passage.replace("  ", "")
        return passage

    def process_chapters(self):
        for idx, _ in enumerate(self.chapters):
            self.chapters[idx] = self.clean_passage(self.chapters[idx])

    def extract_chapter_info(self):
        client = anthropic.Anthropic(api_key=self.claude_key)
        self.extracted_info = []
        starter_text = """What are the physical descriptions of characters in the
                            following book chapter? Book chapter: """
        system_prompt = """You are a reader of a book and are tasked with summarizing 
                    the physical descriptions of characters and scenes such that someone
                    could paint them based on your descriptions. Return results in a
                    YAML-like format where the dictionary is called Descriptions, each
                    character and scene is prepended with 'Entry: ', and the descriptions
                    have the key 'Descriptions: '. Characters should have 'char -' at the
                    beginning of the description and scenes should have 'scene -' in the
                    beginning of the description. The scene entry should include a short
                    description of what the characters are doing at the scene. If no
                    physical description of a character or scene is provided, do not
                    include it."""
        for chapter in self.chapters[:2]:  # DEBUGGING, remove [:2] later
            query = starter_text + chapter
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": [{"type": "text", "text": query}]}
                ],
            )
            # Add to dictionary
            # Load the YAML text into a Python dictionary
            data = yaml.safe_load(message.content[0].text)

            # Convert the structured format to the desired dictionary format
            self.description_dict = {
                item["Entry"]: item["Description"] for item in data["Descriptions"]
            }
            gen_prompt = """Use the following descriptions to generate an image
                                of a scene in an old black and white drawing style. \n"""
            self.generate_illustrations(gen_prompt + message.content[0].text)

    def generate_illustrations(self, prompt):
        """Generate illustrations per chapter using the dictionary"""
        client = OpenAI(api_key=self.openai_key)

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        print(response.data[0].url)
        return response.data[0].url

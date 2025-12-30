"""Main script for adding generated illustrations to e-books"""

import anthropic
from bs4 import BeautifulSoup
from ebooklib import epub
import json
from openai import (
    OpenAI,
    APIConnectionError,
    RateLimitError,
    APIStatusError,
    BadRequestError,
)
import requests
from PIL import Image
from io import BytesIO
import os

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
        style: str,
    ):
        self.ebook_filepath = ebook_filepath
        self.book = epub.read_epub(ebook_filepath)
        self.book_items = [x for x in self.book.get_items()]
        self.batch_size = 16
        self.load_keys()
        self.description_dict = {}
        self.style = style
        self.image_outdir = "generated_illustrations/"

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

    def extract_chapter_info(self, chapter):
        client = anthropic.Anthropic(api_key=self.claude_key)
        self.extracted_info = []

        starter_text = """What are the physical descriptions of characters in the
                            following book chapter? Rewrite
                            descriptions such that they would be appropriate for
                            a children's book. Do not include deceased characters.
                            Avoid any content that may be considered inappropriate
                            or offensive, ensuring the image aligns with content policies.
                            Book chapter: """
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
                    include it. """

        query = starter_text + chapter
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": [{"type": "text", "text": query}]}],
        )
        # Add to dictionary
        # Load the YAML text into a Python dictionary
        # data = yaml.safe_load(message.content[0].text)

        # Convert the structured format to the desired dictionary format
        # self.description_dict = {
        #     item["Entry"]: item["Description"] for item in data["Descriptions"]
        # # }

        # Send another prompt to Claude to create one scene description to send to Dalle
        query = (
            """Select one scene from the following list of character and scene
                        descriptions and use the following character and scene descriptions
                        to write a description of a scene in this book, as if you were an author. Avoid any
                        content that may be considered inappropriate or
                        offensive, ensuring the image aligns with content policies. Rewrite
                            descriptions such that they would be appropriate for
                            a children's book."""
            + message.content[0].text
        )
        system_prompt = """You are an author tasked with describing a scene in a book.
                        The scene and character descriptions have been given to you.
                        You must select one scene and incorporate the descriptions
                        of the characters that are in that scene based on the information
                        given to you. Please description the scene such that someone could
                        draw a picture of it based on your desciption. Avoid any content
                        that may be considered inappropriate or
                        offensive, ensuring the image aligns with content policies."""

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": [{"type": "text", "text": query}]}],
        )

        gen_prompt = f"""Use the following description
                        to generate an image of a scene in a {self.style}
                        style. Avoid any content that may be considered inappropriate or
                        offensive, ensuring the image aligns with content policies. Description:"""

        return gen_prompt + message.content[0].text

    def generate_illustrations(self, prompt, chapter_num):
        """Generate illustrations per chapter using the dictionary"""

        client = OpenAI(api_key=self.openai_key)

        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
        except APIConnectionError as e:
            print("Server connection error: {e.__cause__}")  # from httpx.
            raise
        except RateLimitError as e:
            print(f"OpenAI RATE LIMIT error {e.status_code}: (e.response)")
            raise
        except APIStatusError as e:
            print(f"OpenAI STATUS error {e.status_code}: (e.response)")
            print(prompt)
            raise
        except BadRequestError as e:
            print(f"OpenAI BAD REQUEST error {e.status_code}: (e.response)")
            print(prompt)
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise

        print(response.data[0].url)
        response = requests.get(response.data[0].url)
        # Append the Image object to the list
        image_object = Image.open(BytesIO(response.content))
        image_filename = f"chapter_{chapter_num}_illustration.png"
        image_object.save(os.path.join(self.image_outdir, image_filename))

    def add_image_to_content(self, chapter_content, chapter_num):
        """Add illustration image to chapter content"""
        curr_body_content = chapter_content.get_body_content().decode("utf-8")
        image_tag = f'<img src="chapter_{chapter_num}_illustration.png" />'
        curr_body_content = curr_body_content.replace(
            "</h2>\n", f"</h2>\n{image_tag}\n", 1
        )
        chapter_with_image = chapter_content
        chapter_with_image.content = curr_body_content
        # chapter_with_image = chapter_with_image.encode("utf-8")
        return chapter_with_image

    # Generate new epub
    def generate_new_book(self, use_existing_illustrations=False):
        """Generate new epub book with illustrations"""
        # Go through book, chapter by chapter and generate new ebook
        self.new_book = epub.EpubBook()
        chapter_num = 0
        for book_item in self.book_items:
            if (
                hasattr(book_item, "is_chapter")
                and book_item.is_chapter()
                and hasattr(book_item, "get_body_content")
            ):
                # If book item is a chapter, add chapter text with
                # illustration
                # Make sure not to add image to a chapter that
                # isn't a real chapter (starting title and blank pages)
                # Get string from chapter
                curr_chapter_string = self.chapter_to_str(book_item)
                # Filter out title page, blank pages, short excerpts
                if (
                    curr_chapter_string == ""
                    or "Title" in curr_chapter_string
                    or len(curr_chapter_string) < 1000
                ):
                    # Do not continue with image generation
                    self.new_book.add_item(book_item)
                else:
                    image_prompt = self.extract_chapter_info(curr_chapter_string)
                    if not use_existing_illustrations:
                        self.generate_illustrations(
                            image_prompt,
                            chapter_num,
                        )
                    self.new_book.add_item(
                        self.add_image_to_content(
                            book_item,
                            chapter_num,
                        )
                    )
                    image_filename = os.path.join(
                        self.image_outdir, f"chapter_{chapter_num}_illustration.png"
                    )
                    image_content = open(image_filename, "rb").read()
                    img = epub.EpubImage(
                        uid=f"image_{chapter_num}",
                        file_name=f"{image_filename}",
                        media_type="image/png",
                        content=image_content,
                    )

                    self.new_book.add_item(img)

                    chapter_num += 1
            else:
                self.new_book.add_item(book_item)

    def save_new_epub(self, new_epub_filename):
        """Write out epub book with illustrations."""
        self.new_book.set_identifier(self.book.get_metadata("DC", "identifier")[0][0])
        self.new_book.set_title(
            self.book.get_metadata("DC", "title")[0][0] + " WITH PICTURES"
        )
        self.new_book.set_language("en")

        self.new_book.add_author(self.book.get_metadata("DC", "creator")[0][0])
        self.new_book.toc = self.book.toc
        self.new_book.spine = self.book.spine
        epub.write_epub(new_epub_filename, self.new_book)


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("ebook")
    parser.add_argument("style")

    args = parser.parse_args()

    ereader = EpubReader(args.ebook, args.style)
    ereader.generate_new_book(use_existing_illustrations=False)

    # change out filename
    new_outname = args.ebook.split(".epub")[0] + " WITH PICTURES.epub"
    ereader.save_new_epub(new_outname)
    print(f"New ebook with illustrations saved to {new_outname}")

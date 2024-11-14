"""Main script for adding generated illustrations to e-books"""

from bs4 import BeautifulSoup
from ebooklib import epub

# from transformers import AutoTokenizer, pipeline
from typing import List, Tuple, Dict


# TODO: Assert that input file is an epub.
# TODO: Extract characters, scenes, plot.
# TODO: Extract non english text and translate? Filter out?
# TODO: Move keys to JSON then add to gitignore


class EpubReader:
    def __init__(
        self,
        ebook_filepath: str,
        model_checkpoint: str = "distilbert-base-cased-distilled-squad",
    ):
        self.ebook_filepath = ebook_filepath
        self.book = epub.read_epub(ebook_filepath)
        self.book_items = [x for x in self.book.get_items()]
        self.batch_size = 16
        self.model_checkpoint = model_checkpoint
        # self.model_checkpoint = "distilbert-base-uncased"  # change default model

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
        # FOR DEBUGGING
        # self.chapters = []
        # for idx, x in enumerate(self.book_items):
        #     if hasattr(x, "is_chapter") and x.is_chapter():
        #         try:
        #             self.chapters.append(self.chapter_to_str(x))
        #         except:
        #             print(x)
        #             print(idx)
        #             break

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

    # def extract_chapter_info(self):
    #     self.extracted_info = []
    #     for chapter in self.chapters:
    #         question_answerer = pipeline(
    #             "question-answering", model="distilbert-base-cased-distilled-squad"
    #         )
    #         self.extracted_info.append(
    #             question_answerer(
    #                 question="What is a good example of a question answering dataset?",
    #                 context=chapter,
    #             )
    #         )

    # def preprocess_function(self, passage):
    #     """Wrapper function for preprocessing mapper on dset text"""
    #     return self.tokenizer(passage, truncation=True)

    # def extract_chapter_info(self):
    #     """Return summary of character descriptions and plot
    #     from chapter"""
    #     # Load auto tokenizer to tokenize the text in a way that matches the model
    #     self.tokenizer = AutoTokenizer.from_pretrained(
    #         self.model_checkpoint, use_fast=True
    #     )
    #     self.encoded_chapters = self.chapters.map(
    #         self.preprocess_function, batched=True
    #     )
    #     self. model = AutoModelForSequenceClassification.from_pretrained(self.model_checkpoint, num_labels=num_labels)

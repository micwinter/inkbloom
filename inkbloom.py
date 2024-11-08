"""Main script for adding generated illustrations to e-books"""

from bs4 import BeautifulSoup
from ebooklib import epub
from typing import List, Tuple, Dict


# TODO: Assert that input file is an epub.


class EpubReader:
    def _init_(self, ebook_filepath: str):
        self.ebook_filepath = ebook_filepath
        self.book = epub.read_epub(ebook_filepath)
        self.book_items = [x for x in self.book.get_items()]

    def chapter_to_str(chapter):
        soup = BeautifulSoup(chapter.get_body_content(), "html.parser")
        text = [para.get_text() for para in soup.find_all("p")]
        return "" "".join(text)

    def read_chapters(self):
        self.chapters = [
            self.chapter_to_str(x) for x in self.book_items if x.is_chapter()
        ]

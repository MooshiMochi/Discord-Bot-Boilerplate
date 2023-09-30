from discord.ext.commands import Paginator as CommandPaginator


class TextPageSource:
    """Get pages for text paginator"""

    def __init__(
        self,
        text,
        *,
        prefix="```",
        suffix="```",
        max_size=2000,
        code_block=False,
        block_prefix="py",
    ):
        self._max_size = max_size

        if code_block:
            prefix += (
                block_prefix + "\n" if not block_prefix.endswith("\n") else block_prefix
            )
        pages = CommandPaginator(prefix=prefix, suffix=suffix, max_size=max_size - 200)
        for line in text.split("\n"):
            try:
                pages.add_line(line)
            except RuntimeError:
                converted_lines = self.__convert_to_chunks(line)
                for line in converted_lines:  # noqa
                    pages.add_line(line)
        self.pages = pages

    def getPages(self, *, page_number=True):
        """Gets the pages."""
        pages = []
        page_num = 1  # noqa
        for page in self.pages.pages:
            if page_number:
                page += f"\nPage {page_num}/{len(self.pages.pages)}"
                page_num += 1
            pages.append(page)
        return pages

    def __convert_to_chunks(self, text):
        """Convert the text to chunks of size max_size-300"""
        chunks = []
        for i in range(0, len(text), self._max_size - 300):
            chunks.append(text[i : i + self._max_size - 300])
        return chunks

# PySpelling

PySpelling is wrapper around Aspell that is used to automating spell checking of different file types. Essentially you set up spelling tasks for different file types and it will iterate through them applying your search options and filters for each specific task. Its aim is not to provide an system for interactively replacing misspelled words, but to provide a quick way to setup, filter, test, and automate spell checking for your project.

Since PySpelling doesn't need to track exactly where a misspelled word is for replace, it can leverage other libraries that augment the buffer making filtering of the content more flexible and easier. This makes it much easier to write your own filter or parser for your specific file type.

PySpelling will return all the misspelled words for each file under testing, and depending on the file parser, it may even return misspelled words for specific text blocks within the file.

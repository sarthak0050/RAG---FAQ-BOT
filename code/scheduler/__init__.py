"""Corpus refresh for the FAQ bot.

Re-fetches the five official Groww fund pages, compares the extracted text
with what is already stored, and rebuilds only the pipeline stages that are
affected when the source content has actually changed.
"""
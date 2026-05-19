# test_search.py
from app.backend.search import web_search

result = web_search("latest AI news today", engine="duckduckgo")
print(result)
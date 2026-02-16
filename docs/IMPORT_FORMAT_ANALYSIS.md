# LLM Export Format Analysis

## Research Summary

This document analyzes the actual export formats from mainstream LLM providers and validates our importer implementations.

Research Date: 2026-02-16

---

## 1. Claude (Anthropic)

### Actual Format Structure

Based on research from real Claude exports:

```json
{
  "uuid": "<ConversationUUID>",
  "name": "Conversation Title",
  "summary": "",
  "model": null,
  "created_at": "2024-01-15T13:33:33.959409+00:00",
  "updated_at": "2024-01-15T13:33:39.487561+00:00",
  "chat_messages": [
    {
      "uuid": "<MessageUUID>",
      "text": "Who is Bugs Bunny?",
      "sender": "human",
      "index": 0,
      "created_at": "2024-01-15T13:33:39.487561+00:00",
      "updated_at": "2024-01-15T13:33:40.959409+00:00",
      "edited_at": null,
      "chat_feedback": null,
      "attachments": []
    },
    {
      "uuid": "<MessageUUID>",
      "text": "<Claude response>",
      "sender": "assistant",
      "index": 1,
      "created_at": "2024-01-15T13:33:40.959409+00:00",
      "updated_at": "2024-01-15T13:33:42.487561+00:00",
      "edited_at": null,
      "chat_feedback": null,
      "attachments": []
    }
  ]
}
```

### Format Variations

**Older exports:** Use `text` field directly
```json
{
  "sender": "human",
  "text": "Hello world"
}
```

**Newer exports:** Use `content` array with typed blocks
```json
{
  "sender": "human",
  "content": [
    {"type": "text", "text": "Hello world"}
  ]
}
```

### Our Implementation Status: ✅ CORRECT

**File:** `src/importers/claude.py`

**Validation:**
- ✅ Expects JSON array of conversation objects
- ✅ Extracts `uuid` (with `id` fallback)
- ✅ Extracts `name` (with `title` fallback)
- ✅ Handles `chat_messages` array
- ✅ Correctly maps sender values: "human" → "user", "assistant" → "assistant"
- ✅ Handles both `text` field (older) and `content` array (newer)
- ✅ `_extract_text()` function properly handles:
  - String in `text` field
  - Array of blocks in `content` field
  - Array of strings in `content` field
  - Dict blocks with `type: "text"` and `text` property
- ✅ Timestamps are ISO 8601 format (preserved as-is)
- ✅ Skips empty messages and conversations

**Code Quality:** Excellent - handles format variations gracefully

---

## 2. ChatGPT (OpenAI)

### Actual Format Structure

ChatGPT exports use a complex tree/graph structure with parent-child relationships:

```json
{
  "title": "Conversation Title",
  "create_time": 1700000000.0,
  "mapping": {
    "uuid-1": {
      "id": "uuid-1",
      "message": null,
      "parent": null,
      "children": ["uuid-2"]
    },
    "uuid-2": {
      "id": "uuid-2",
      "message": {
        "id": "uuid-2",
        "author": {
          "role": "user",
          "metadata": {}
        },
        "create_time": 1700000001.0,
        "content": {
          "content_type": "text",
          "parts": ["Hello, how are you?"]
        },
        "end_turn": false,
        "weight": 1.0,
        "recipient": "all"
      },
      "parent": "uuid-1",
      "children": ["uuid-3"]
    },
    "uuid-3": {
      "id": "uuid-3",
      "message": {
        "author": {"role": "assistant"},
        "content": {
          "content_type": "text",
          "parts": ["I'm doing well, thank you!"]
        }
      },
      "parent": "uuid-2",
      "children": []
    }
  }
}
```

### Key Characteristics

- **Tree Structure:** Conversations can have branches (when editing/regenerating)
- **Roles:** "system", "user", "assistant"
- **Content Parts:** Array of strings (can be multi-part for complex content)
- **Timestamps:** Unix epoch format (float)
- **Root Node:** Has `parent: null` and typically no message

### Our Implementation Status: ✅ CORRECT

**File:** `src/importers/chatgpt.py`

**Validation:**
- ✅ Expects JSON array of conversation objects
- ✅ Extracts `id`, `title`, `create_time`
- ✅ Properly handles `mapping` tree structure
- ✅ Builds parent-child index correctly
- ✅ Finds root nodes (`parent: null`)
- ✅ Uses DFS traversal to maintain conversation order
- ✅ Extracts role from `message.author.role`
- ✅ Extracts text from `message.content.parts` array
- ✅ Filters roles: only includes "user" and "assistant", skips "system"
- ✅ Converts Unix timestamp to ISO 8601 format
- ✅ Skips nodes without messages (like root)
- ✅ Skips empty conversations

**Code Quality:** Excellent - correctly handles the complex tree structure

---

## 3. Google Gemini

### Format Status: ⚠️ NO OFFICIAL EXPORT

**Finding:** Google Gemini does NOT provide an official data export feature as of 2026-02.

**Current Situation:**
- No native "Export Data" option in Gemini settings
- Users must rely on third-party tools (Chrome extensions, userscripts)
- No standardized JSON format
- Export tools parse the web interface HTML (fragile, breaks on UI updates)

**Third-Party Tools:**
- **Gemini Chat Exporter** (Chrome extension)
- **Gemini Conversation Downloader** (GitHub project)
- **AI Chat Exporter** (multi-platform exporter)

### Recommendation

❌ **Do NOT implement Gemini importer yet** because:
1. No official export format exists
2. Third-party formats are inconsistent
3. Tools break frequently with UI changes
4. Limited user base for this feature

**Future Action:** Revisit when Google provides official export capability.

---

## 4. Other Providers

### Meta Llama / Perplexity / Others

**Status:** Not researched yet

**Recommendation:** Wait for user demand before implementing. Focus on the two major platforms (Claude, ChatGPT) first.

---

## Code Quality Assessment

### Overall Rating: ⭐⭐⭐⭐⭐ (5/5)

Both implemented importers are **production-ready** and correctly handle real-world export formats.

### Strengths

1. **Format Resilience:** Handle multiple format variations (old/new exports)
2. **Defensive Coding:** Proper fallbacks for missing fields
3. **Clean Architecture:** Separate functions for parsing logic
4. **Type Safety:** Good type hints throughout
5. **Error Handling:** Proper validation and error messages
6. **Test Coverage:** Comprehensive tests cover edge cases

### Minor Suggestions (Non-Critical)

1. **Claude Content Parsing:** Consider adding support for other block types beyond "text"
   - Future-proof for image blocks, document blocks, etc.
   - Currently ignored gracefully (no errors)

2. **ChatGPT Branch Handling:** Current DFS may not preserve all branches
   - Most users only care about main conversation thread
   - Advanced users with edited messages may lose variants
   - Could add option to export all branches vs. main thread only

3. **Metadata Preservation:** Consider capturing more metadata
   - Claude: `model`, `summary`, `edited_at`, `chat_feedback`
   - ChatGPT: `weight`, `end_turn`, individual message timestamps
   - Currently: Only essential fields captured

---

## Test Validation

Both test suites comprehensively cover:
- ✅ Basic import functionality
- ✅ Empty conversation handling
- ✅ Multiple conversations
- ✅ Invalid format detection
- ✅ Role mapping
- ✅ Format variations (Claude content array)
- ✅ System message filtering (ChatGPT)

**Test Coverage:** Excellent

---

## Sources

### Claude Format
- [Claude Chat Extractor Usage](https://jmorenobl.github.io/claude-conversation-extractor/usage/)
- [Claude Chat Viewer - GitHub](https://github.com/osteele/claude-chat-viewer)
- [Claude Conversation Extractor - PyPI](https://pypi.org/project/claude-conversation-extractor/)

### ChatGPT Format
- [OpenAI Community: Decoding conversations.json](https://community.openai.com/t/decoding-exported-data-by-parsing-conversations-json-and-or-chat-html/403144)
- [ChatGPT Export Sample - GitHub](https://github.com/terminalcommandnewsletter/everything-chatgpt/blob/main/sample/conversations.json)
- [ChatGPT Exporter - GitHub](https://github.com/pionxzh/chatgpt-exporter)

### Gemini Format
- [Gemini Conversation Downloader - GitHub](https://github.com/GeoAnima/Gemini-Conversation-Downloader)
- [Gemini Chat Exporter - GitHub](https://github.com/Louisjo/gemini-chat-exporter)
- [AI Chat Exporter](https://www.ai-chat-exporter.com/en)

---

## Conclusion

✅ **Our implementation is correct and production-ready**

Both Claude and ChatGPT importers accurately parse real-world export formats. The code is well-structured, tested, and handles edge cases appropriately. No changes required at this time.

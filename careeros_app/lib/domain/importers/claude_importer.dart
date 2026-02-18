/// Port of Python `src/importers/claude.py` to Dart.
///
/// Claude exports are a JSON array of conversation objects with flat
/// `chat_messages` arrays. Each message has a `sender` field ("human" or
/// "assistant") and a `text` field (or `content` array).
import 'dart:convert';
import 'dart:io';

import '../models/conversation.dart';

List<Conversation> importClaude(String filePath) {
  final content = File(filePath).readAsStringSync();
  final data = jsonDecode(content);

  if (data is! List) {
    throw FormatException('Expected JSON array, got ${data.runtimeType}');
  }

  final conversations = <Conversation>[];

  for (final conv in data) {
    if (conv is! Map<String, dynamic>) continue;

    final convId = (conv['uuid'] ?? conv['id'] ?? '') as String;
    final title = (conv['name'] ?? conv['title'] ?? 'Untitled') as String;
    final createdAt = conv['created_at'] ?? conv['create_time'];
    final startedAt = _parseTimestamp(createdAt);

    final chatMessages = conv['chat_messages'] as List<dynamic>? ?? [];
    final messages = <Message>[];

    for (final msg in chatMessages) {
      if (msg is! Map<String, dynamic>) continue;

      final sender = msg['sender'] as String? ?? '';
      const roleMap = {
        'human': 'user',
        'user': 'user',
        'assistant': 'assistant',
      };
      final role = roleMap[sender];
      if (role == null) continue;

      final text = _extractText(msg);
      if (text.isNotEmpty) {
        messages.add(Message(role: role, text: text));
      }
    }

    if (messages.isEmpty) continue;

    conversations.add(Conversation(
      id: convId,
      source: 'claude',
      title: title,
      messages: messages,
      startedAt: startedAt,
    ));
  }

  return conversations;
}

String _parseTimestamp(dynamic ts) {
  if (ts == null) return DateTime.now().toUtc().toIso8601String();
  // Claude timestamps are already ISO 8601.
  return ts.toString();
}

String _extractText(Map<String, dynamic> msg) {
  // Try `text` field first (older exports).
  if (msg.containsKey('text') && msg['text'] is String) {
    return (msg['text'] as String).trim();
  }

  // Try `content` array (newer exports).
  final content = msg['content'];
  if (content is List) {
    final buffer = StringBuffer();
    for (final block in content) {
      if (block is String) {
        buffer.write(block);
      } else if (block is Map<String, dynamic> &&
          block['type'] == 'text') {
        buffer.write(block['text'] ?? '');
      }
    }
    return buffer.toString().trim();
  }

  if (content is String) {
    return content.trim();
  }

  return '';
}

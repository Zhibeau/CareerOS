/// Port of Python `src/importers/chatgpt.py` to Dart.
///
/// ChatGPT exports are a JSON array of conversation objects where messages
/// live in a `mapping` tree structure with parent-child relationships.
import 'dart:convert';
import 'dart:io';

import '../models/conversation.dart';

List<Conversation> importChatGPT(String filePath) {
  final content = File(filePath).readAsStringSync();
  final data = jsonDecode(content);

  if (data is! List) {
    throw FormatException('Expected JSON array, got ${data.runtimeType}');
  }

  final conversations = <Conversation>[];

  for (final conv in data) {
    if (conv is! Map<String, dynamic>) continue;

    final convId = conv['id'] as String? ?? '';
    final title = conv['title'] as String? ?? 'Untitled';
    final createTime = conv['create_time'];
    final startedAt = _parseTimestamp(createTime);
    final mapping = conv['mapping'] as Map<String, dynamic>? ?? {};

    final messages = _extractMessages(mapping);

    if (messages.isEmpty) continue;

    conversations.add(Conversation(
      id: convId,
      source: 'chatgpt',
      title: title,
      messages: messages,
      startedAt: startedAt,
    ));
  }

  return conversations;
}

String _parseTimestamp(dynamic ts) {
  if (ts == null) return DateTime.now().toUtc().toIso8601String();
  if (ts is num) {
    return DateTime.fromMillisecondsSinceEpoch(
      (ts * 1000).toInt(),
      isUtc: true,
    ).toIso8601String();
  }
  return ts.toString();
}

List<Message> _extractMessages(Map<String, dynamic> mapping) {
  // Build parent → children index.
  final childrenOf = <String, List<String>>{};
  String? rootId;

  for (final entry in mapping.entries) {
    final nodeId = entry.key;
    final node = entry.value as Map<String, dynamic>;
    final parentId = node['parent'] as String?;

    if (parentId == null) {
      rootId = nodeId;
    } else {
      childrenOf.putIfAbsent(parentId, () => []).add(nodeId);
    }
  }

  if (rootId == null) return [];

  // Walk tree depth-first, collecting messages in order.
  final messages = <Message>[];
  final stack = <String>[rootId];

  while (stack.isNotEmpty) {
    final nodeId = stack.removeLast();
    final node = mapping[nodeId] as Map<String, dynamic>?;
    if (node == null) continue;

    final msg = node['message'] as Map<String, dynamic>?;
    if (msg != null) {
      final author = msg['author'] as Map<String, dynamic>? ?? {};
      final role = author['role'] as String? ?? '';

      if (role == 'user' || role == 'assistant') {
        final text = _extractText(msg);
        if (text.isNotEmpty) {
          messages.add(Message(role: role, text: text));
        }
      }
    }

    // Push children in reverse so first child is processed first.
    final children = childrenOf[nodeId] ?? [];
    for (final child in children.reversed) {
      stack.add(child);
    }
  }

  return messages;
}

String _extractText(Map<String, dynamic> msg) {
  final content = msg['content'] as Map<String, dynamic>? ?? {};
  final parts = content['parts'] as List<dynamic>? ?? [];

  final buffer = StringBuffer();
  for (final part in parts) {
    if (part is String) {
      buffer.write(part);
    }
  }
  return buffer.toString().trim();
}

class Message {
  final String role; // "user" or "assistant"
  final String text;

  const Message({required this.role, required this.text});

  Map<String, dynamic> toJson() => {'role': role, 'text': text};

  factory Message.fromJson(Map<String, dynamic> json) => Message(
        role: json['role'] as String,
        text: json['text'] as String,
      );
}

class Conversation {
  final String id;
  final String source; // "chatgpt" or "claude"
  final String title;
  final List<Message> messages;
  final String startedAt; // ISO 8601

  const Conversation({
    required this.id,
    required this.source,
    required this.title,
    required this.messages,
    required this.startedAt,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'source': source,
        'title': title,
        'messages': messages.map((m) => m.toJson()).toList(),
        'started_at': startedAt,
      };
}

import 'package:uuid/uuid.dart';

class Achievement {
  final String id;
  final String summary;
  final String? impact;
  final String? achievedAt;

  Achievement({
    String? id,
    required this.summary,
    this.impact,
    this.achievedAt,
  }) : id = id ?? const Uuid().v4();

  Achievement copyWith({
    String? summary,
    String? impact,
    String? achievedAt,
  }) {
    return Achievement(
      id: id,
      summary: summary ?? this.summary,
      impact: impact ?? this.impact,
      achievedAt: achievedAt ?? this.achievedAt,
    );
  }

  factory Achievement.fromJson(Map<String, dynamic> json) => Achievement(
        id: json['id'] as String,
        summary: json['summary'] as String,
        impact: json['impact'] as String?,
        achievedAt: json['achieved_at'] as String?,
      );
}

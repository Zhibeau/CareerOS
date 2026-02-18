import 'package:uuid/uuid.dart';

import 'project.dart';

class Role {
  final String id;
  final String title;
  final String? company;
  final String? startedAt;
  final String? endedAt;

  // Joined from queries
  final List<Project> projects;

  Role({
    String? id,
    required this.title,
    this.company,
    this.startedAt,
    this.endedAt,
    this.projects = const [],
  }) : id = id ?? const Uuid().v4();

  Role copyWith({
    String? title,
    String? company,
    String? startedAt,
    String? endedAt,
    List<Project>? projects,
  }) {
    return Role(
      id: id,
      title: title ?? this.title,
      company: company ?? this.company,
      startedAt: startedAt ?? this.startedAt,
      endedAt: endedAt ?? this.endedAt,
      projects: projects ?? this.projects,
    );
  }

  factory Role.fromJson(Map<String, dynamic> json) => Role(
        id: json['id'] as String,
        title: json['title'] as String,
        company: json['company'] as String?,
        startedAt: json['started_at'] as String?,
        endedAt: json['ended_at'] as String?,
      );
}

import 'package:uuid/uuid.dart';

class Project {
  final String id;
  final String name;
  final String summary;
  final String status;
  final String? startedAt;
  final String? endedAt;
  final String? roleId;

  // Joined fields (from queries)
  final String? roleTitle;
  final String? roleCompany;
  final List<String> skills;

  Project({
    String? id,
    required this.name,
    required this.summary,
    this.status = 'active',
    this.startedAt,
    this.endedAt,
    this.roleId,
    this.roleTitle,
    this.roleCompany,
    this.skills = const [],
  }) : id = id ?? const Uuid().v4();

  Project copyWith({
    String? name,
    String? summary,
    String? status,
    String? startedAt,
    String? endedAt,
    String? roleId,
    String? roleTitle,
    String? roleCompany,
    List<String>? skills,
  }) {
    return Project(
      id: id,
      name: name ?? this.name,
      summary: summary ?? this.summary,
      status: status ?? this.status,
      startedAt: startedAt ?? this.startedAt,
      endedAt: endedAt ?? this.endedAt,
      roleId: roleId ?? this.roleId,
      roleTitle: roleTitle ?? this.roleTitle,
      roleCompany: roleCompany ?? this.roleCompany,
      skills: skills ?? this.skills,
    );
  }

  factory Project.fromJson(Map<String, dynamic> json) => Project(
        id: json['id'] as String,
        name: json['name'] as String,
        summary: (json['summary'] as String?) ?? '',
        status: (json['status'] as String?) ?? 'active',
        startedAt: json['started_at'] as String?,
        endedAt: json['ended_at'] as String?,
        roleId: json['role_id'] as String?,
      );
}

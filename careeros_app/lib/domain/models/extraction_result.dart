import 'achievement.dart';
import 'project.dart';
import 'skill.dart';

class ExtractionResult {
  final bool isWork;
  final List<Project> projects;
  final List<Skill> skills;
  final List<Achievement> achievements;
  final Map<String, List<String>> projectSkills;
  final Map<String, List<String>> projectAchievements;

  const ExtractionResult({
    required this.isWork,
    this.projects = const [],
    this.skills = const [],
    this.achievements = const [],
    this.projectSkills = const {},
    this.projectAchievements = const {},
  });

  factory ExtractionResult.fromJson(Map<String, dynamic> json) {
    return ExtractionResult(
      isWork: json['is_work'] as bool? ?? false,
      projects: (json['projects'] as List<dynamic>?)
              ?.map((p) => Project.fromJson(p as Map<String, dynamic>))
              .toList() ??
          [],
      skills: (json['skills'] as List<dynamic>?)
              ?.map((s) => Skill.fromJson(s as Map<String, dynamic>))
              .toList() ??
          [],
      achievements: (json['achievements'] as List<dynamic>?)
              ?.map((a) => Achievement.fromJson(a as Map<String, dynamic>))
              .toList() ??
          [],
      projectSkills: _parseStringListMap(json['project_skills']),
      projectAchievements: _parseStringListMap(json['project_achievements']),
    );
  }

  static Map<String, List<String>> _parseStringListMap(dynamic value) {
    if (value is! Map) return {};
    return value.map(
      (key, val) => MapEntry(
        key as String,
        (val as List<dynamic>).map((e) => e as String).toList(),
      ),
    );
  }
}

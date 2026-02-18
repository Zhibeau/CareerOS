import 'package:uuid/uuid.dart';

class Skill {
  final String id;
  final String name;
  final String category; // language, framework, tool, platform, concept, soft_skill

  Skill({
    String? id,
    required this.name,
    required this.category,
  }) : id = id ?? const Uuid().v4();

  Skill copyWith({String? name, String? category}) {
    return Skill(
      id: id,
      name: name ?? this.name,
      category: category ?? this.category,
    );
  }

  factory Skill.fromJson(Map<String, dynamic> json) => Skill(
        id: json['id'] as String,
        name: json['name'] as String,
        category: json['category'] as String,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'category': category,
      };
}

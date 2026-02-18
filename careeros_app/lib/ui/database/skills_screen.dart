import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/career_provider.dart';

class SkillsScreen extends ConsumerWidget {
  const SkillsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final skills = ref.watch(skillsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Skills')),
      body: skills.when(
        data: (list) {
          if (list.isEmpty) {
            return Center(
              child: Text(
                'No skills found.\nImport chat history to extract skills.',
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            );
          }

          // Group by category.
          final grouped = <String, List<Skill>>{};
          for (final skill in list) {
            grouped.putIfAbsent(skill.category, () => []).add(skill);
          }

          final categories = grouped.keys.toList()..sort();

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: categories.length,
            itemBuilder: (context, index) {
              final category = categories[index];
              final categorySkills = grouped[category]!;

              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (index > 0) const SizedBox(height: 20),
                  Text(
                    _formatCategory(category),
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: categorySkills.map((skill) {
                      return Chip(
                        label: Text(skill.name),
                        deleteIcon: const Icon(Icons.close, size: 16),
                        onDeleted: () async {
                          final db = ref.read(databaseProvider);
                          await db.deleteSkill(skill.id);
                          ref.invalidate(skillsProvider);
                        },
                      );
                    }).toList(),
                  ),
                ],
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
      ),
    );
  }

  String _formatCategory(String category) {
    return category
        .replaceAll('_', ' ')
        .split(' ')
        .map((w) => w.isEmpty ? w : '${w[0].toUpperCase()}${w.substring(1)}')
        .join(' ');
  }
}

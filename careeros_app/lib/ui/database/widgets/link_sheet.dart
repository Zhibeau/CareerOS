import 'package:drift/drift.dart' show Value;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/local/database.dart';
import '../../../providers/career_provider.dart';

/// Bottom sheet that lets the user link a project to a role (or unlink).
class LinkProjectToRoleSheet extends ConsumerWidget {
  final Project project;

  const LinkProjectToRoleSheet({super.key, required this.project});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rolesAsync = ref.watch(rolesProvider);
    final theme = Theme.of(context);

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Text(
                'Link "${project.name}" to a Role',
                style: theme.textTheme.titleMedium,
              ),
            ),
            const Divider(),

            // Unlink option
            ListTile(
              leading: Icon(Icons.link_off,
                  color: theme.colorScheme.onSurfaceVariant),
              title: const Text('No role (unlink)'),
              selected: project.roleId == null,
              onTap: () => _linkToRole(context, ref, null),
            ),

            // Role list
            rolesAsync.when(
              loading: () => const Padding(
                padding: EdgeInsets.all(16),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (e, _) => Padding(
                padding: const EdgeInsets.all(16),
                child: Text('Error loading roles: $e'),
              ),
              data: (roles) {
                if (roles.isEmpty) {
                  return const Padding(
                    padding: EdgeInsets.all(16),
                    child: Text(
                      'No roles yet. Add roles from the Roles tab first.',
                    ),
                  );
                }
                return Column(
                  mainAxisSize: MainAxisSize.min,
                  children: roles.map((role) {
                    final label = role.company != null
                        ? '${role.title} @ ${role.company}'
                        : role.title;
                    final subtitle = role.startedAt != null
                        ? '${role.startedAt} — ${role.endedAt ?? "Present"}'
                        : null;

                    return ListTile(
                      leading: const Icon(Icons.work_outline),
                      title: Text(label),
                      subtitle: subtitle != null ? Text(subtitle) : null,
                      selected: project.roleId == role.id,
                      selectedTileColor:
                          theme.colorScheme.primaryContainer.withValues(alpha: 0.3),
                      onTap: () => _linkToRole(context, ref, role.id),
                    );
                  }).toList(),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _linkToRole(
    BuildContext context,
    WidgetRef ref,
    String? roleId,
  ) async {
    final db = ref.read(databaseProvider);
    await db.updateProject(ProjectsCompanion(
      id: Value(project.id),
      roleId: Value(roleId),
    ));
    ref.invalidate(projectsProvider);
    if (context.mounted) Navigator.pop(context);
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/career_provider.dart';
import 'widgets/edit_dialog.dart';

class ProjectsScreen extends ConsumerWidget {
  const ProjectsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final projects = ref.watch(projectsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Projects')),
      body: projects.when(
        data: (list) {
          if (list.isEmpty) {
            return Center(
              child: Text(
                'No projects found.\nImport chat history to extract projects.',
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: list.length,
            itemBuilder: (context, index) {
              final project = list[index];
              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  contentPadding: const EdgeInsets.all(16),
                  title: Text(
                    project.name,
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (project.summary != null) ...[
                        const SizedBox(height: 4),
                        Text(project.summary!),
                      ],
                      const SizedBox(height: 8),
                      if (project.roleId != null)
                        _RoleChip(roleId: project.roleId!)
                      else
                        Text(
                          'No role linked',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.error,
                          ),
                        ),
                    ],
                  ),
                  trailing: IconButton(
                    icon: const Icon(Icons.edit_outlined),
                    onPressed: () => showProjectEditDialog(
                      context,
                      project: project,
                      onSaved: () => ref.invalidate(projectsProvider),
                    ),
                  ),
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
      ),
    );
  }
}

class _RoleChip extends ConsumerWidget {
  final String roleId;

  const _RoleChip({required this.roleId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final roles = ref.watch(rolesProvider);

    return roles.when(
      data: (list) {
        final role = list.where((r) => r.id == roleId).firstOrNull;
        if (role == null) return const SizedBox.shrink();

        final label = role.company != null
            ? '${role.title} @ ${role.company}'
            : role.title;
        return Chip(
          label: Text(label),
          avatar: const Icon(Icons.business_center_outlined, size: 16),
          visualDensity: VisualDensity.compact,
        );
      },
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
    );
  }
}

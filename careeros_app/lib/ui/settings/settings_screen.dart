import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/auth_provider.dart';
import '../../providers/career_provider.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authStateProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Account section
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  CircleAvatar(
                    backgroundColor: theme.colorScheme.primaryContainer,
                    child: Icon(Icons.person,
                        color: theme.colorScheme.onPrimaryContainer),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          authState.valueOrNull?.email ?? 'User',
                          style: theme.textTheme.titleSmall,
                        ),
                        Text(
                          'Logged in',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Data section
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.download_outlined),
                  title: const Text('Export Data as JSON'),
                  onTap: () {
                    // TODO: Phase 3 — export local DB as JSON
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Coming soon')),
                    );
                  },
                ),
                const Divider(height: 1),
                ListTile(
                  leading: Icon(Icons.delete_outline,
                      color: theme.colorScheme.error),
                  title: Text('Clear All Data',
                      style: TextStyle(color: theme.colorScheme.error)),
                  onTap: () => _confirmClearData(context, ref),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // About section
          Card(
            child: Column(
              children: [
                const ListTile(
                  leading: Icon(Icons.info_outline),
                  title: Text('CareerOS'),
                  subtitle: Text('Version 1.0.0'),
                ),
                const Divider(height: 1),
                ListTile(
                  leading:
                      Icon(Icons.logout, color: theme.colorScheme.error),
                  title: Text('Log Out',
                      style: TextStyle(color: theme.colorScheme.error)),
                  onTap: () =>
                      ref.read(authStateProvider.notifier).logout(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _confirmClearData(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear All Data?'),
        content: const Text(
          'This will permanently delete all your imported conversations, '
          'projects, skills, achievements, and roles. This cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
            onPressed: () async {
              // Recreate the database.
              final db = ref.read(databaseProvider);
              // Delete all tables.
              await db.customStatement('DELETE FROM project_achievements');
              await db.customStatement('DELETE FROM project_skills');
              await db.customStatement('DELETE FROM conversation_projects');
              await db.customStatement('DELETE FROM achievements');
              await db.customStatement('DELETE FROM skills');
              await db.customStatement('DELETE FROM projects');
              await db.customStatement('DELETE FROM roles');
              await db.customStatement('DELETE FROM conversations');
              ref.invalidate(statsProvider);
              ref.invalidate(projectsProvider);
              ref.invalidate(skillsProvider);
              ref.invalidate(achievementsProvider);
              ref.invalidate(rolesProvider);
              if (context.mounted) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('All data cleared')),
                );
              }
            },
            child: const Text('Clear Data'),
          ),
        ],
      ),
    );
  }
}

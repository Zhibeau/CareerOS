import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/career_provider.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final stats = ref.watch(statsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'CareerOS',
          style: theme.textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
            color: theme.colorScheme.primary,
          ),
        ),
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(statsProvider);
          ref.invalidate(projectsProvider);
        },
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Stat cards grid
            stats.when(
              data: (data) => _StatsGrid(stats: data),
              loading: () => const _StatsGrid(
                stats: {
                  'projects': 0,
                  'skills': 0,
                  'achievements': 0,
                  'roles': 0,
                },
              ),
              error: (err, _) => Center(child: Text('Error: $err')),
            ),
            const SizedBox(height: 24),

            // Recent projects
            Text(
              'Recent Projects',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            _RecentProjectsList(),
          ],
        ),
      ),
    );
  }
}

class _StatsGrid extends StatelessWidget {
  final Map<String, int> stats;

  const _StatsGrid({required this.stats});

  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.6,
      children: [
        _StatCard(
          label: 'Projects',
          count: stats['projects'] ?? 0,
          icon: Icons.folder_outlined,
          onTap: () => GoRouter.of(context).go('/dashboard/projects'),
        ),
        _StatCard(
          label: 'Skills',
          count: stats['skills'] ?? 0,
          icon: Icons.code,
          onTap: () => GoRouter.of(context).go('/dashboard/skills'),
        ),
        _StatCard(
          label: 'Achievements',
          count: stats['achievements'] ?? 0,
          icon: Icons.emoji_events_outlined,
          onTap: () => GoRouter.of(context).go('/dashboard/achievements'),
        ),
        _StatCard(
          label: 'Roles',
          count: stats['roles'] ?? 0,
          icon: Icons.business_center_outlined,
          onTap: () => GoRouter.of(context).go('/dashboard/roles'),
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final int count;
  final IconData icon;
  final VoidCallback onTap;

  const _StatCard({
    required this.label,
    required this.count,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Icon(icon, color: theme.colorScheme.primary, size: 28),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    label,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                  Text(
                    '$count',
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RecentProjectsList extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final projects = ref.watch(projectsProvider);
    final theme = Theme.of(context);

    return projects.when(
      data: (list) {
        if (list.isEmpty) {
          return Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  Icon(
                    Icons.upload_file_outlined,
                    size: 48,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'No projects yet',
                    style: theme.textTheme.titleSmall,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Import your AI chat history to get started',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        final recent = list.take(5).toList();
        return Column(
          children: recent.map((p) {
            return Card(
              child: ListTile(
                title: Text(p.name),
                subtitle: Text(
                  p.summary ?? '',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => GoRouter.of(context).go('/dashboard/projects'),
              ),
            );
          }).toList(),
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, _) => Text('Error: $err'),
    );
  }
}

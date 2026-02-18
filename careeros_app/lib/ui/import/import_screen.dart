import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/import_provider.dart';

class ImportScreen extends ConsumerWidget {
  const ImportScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final importState = ref.watch(importStateProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Import Chat History')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // File picker card
          Card(
            child: InkWell(
              onTap: importState.isLoading
                  ? null
                  : () =>
                      ref.read(importStateProvider.notifier).pickAndImport(),
              borderRadius: BorderRadius.circular(12),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 24),
                child: Column(
                  children: [
                    Icon(
                      Icons.upload_file_rounded,
                      size: 48,
                      color: theme.colorScheme.primary,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Pick JSON File',
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Select your ChatGPT or Claude export (.json)',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),

          // How to export guide
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'How to export your data',
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _ExportStep(
                    provider: 'ChatGPT',
                    steps: 'Settings > Data Controls > Export Data',
                    icon: Icons.chat_bubble_outline,
                  ),
                  const Divider(height: 24),
                  _ExportStep(
                    provider: 'Claude',
                    steps: 'Settings > Account > Export Data',
                    icon: Icons.auto_awesome_outlined,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Import progress / result
          if (importState.isLoading)
            const Card(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Column(
                  children: [
                    CircularProgressIndicator(),
                    SizedBox(height: 16),
                    Text('Processing conversations...'),
                  ],
                ),
              ),
            ),

          if (importState.hasError)
            Card(
              color: theme.colorScheme.errorContainer,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text(
                  importState.error.toString(),
                  style: TextStyle(color: theme.colorScheme.onErrorContainer),
                ),
              ),
            ),

          if (importState.valueOrNull != null)
            _ImportResultCard(result: importState.valueOrNull!),
        ],
      ),
    );
  }
}

class _ExportStep extends StatelessWidget {
  final String provider;
  final String steps;
  final IconData icon;

  const _ExportStep({
    required this.provider,
    required this.steps,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        Icon(icon, size: 20, color: theme.colorScheme.onSurfaceVariant),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(provider,
                  style: theme.textTheme.bodyMedium
                      ?.copyWith(fontWeight: FontWeight.w600)),
              Text(steps, style: theme.textTheme.bodySmall),
            ],
          ),
        ),
      ],
    );
  }
}

class _ImportResultCard extends StatelessWidget {
  final ImportResult result;

  const _ImportResultCard({required this.result});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      color: theme.colorScheme.primaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.check_circle,
                    color: theme.colorScheme.onPrimaryContainer),
                const SizedBox(width: 8),
                Text(
                  'Import Complete',
                  style: theme.textTheme.titleSmall?.copyWith(
                    color: theme.colorScheme.onPrimaryContainer,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              '${result.source} format detected\n'
              '${result.totalConversations} conversations found\n'
              '${result.newConversations} new (${result.skippedConversations} skipped)\n'
              '${result.workConversations} work-relevant\n'
              '${result.projectsExtracted} projects, '
              '${result.skillsExtracted} skills, '
              '${result.achievementsExtracted} achievements extracted',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onPrimaryContainer,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

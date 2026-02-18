import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/cv_provider.dart';

class CVPreviewScreen extends ConsumerStatefulWidget {
  const CVPreviewScreen({super.key});

  @override
  ConsumerState<CVPreviewScreen> createState() => _CVPreviewScreenState();
}

class _CVPreviewScreenState extends ConsumerState<CVPreviewScreen> {
  String _format = 'pdf';

  @override
  Widget build(BuildContext context) {
    final cvContent = ref.watch(cvContentProvider);
    final exportState = ref.watch(cvExportProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('CV Preview'),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit_outlined),
            tooltip: 'Edit summary',
            onPressed: cvContent.valueOrNull != null
                ? () => _editSummary(context, cvContent.valueOrNull!)
                : null,
          ),
        ],
      ),
      body: cvContent.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text('Error: $err', style: TextStyle(color: theme.colorScheme.error)),
          ),
        ),
        data: (content) {
          if (content == null) {
            return const Center(child: Text('No CV content generated yet.'));
          }
          return _buildPreview(context, content, exportState);
        },
      ),
    );
  }

  Widget _buildPreview(
    BuildContext context,
    Map<String, dynamic> cv,
    AsyncValue<String?> exportState,
  ) {
    final theme = Theme.of(context);

    return Column(
      children: [
        // Scrollable preview
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Name placeholder
              Center(
                child: Text(
                  cv['name_placeholder'] as String? ?? '[Your Name]',
                  style: theme.textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              Center(
                child: Text(
                  cv['contact_placeholder'] as String? ?? '[email] | [phone]',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // Summary
              if (cv['summary'] != null) ...[
                _sectionHeader(theme, 'PROFESSIONAL SUMMARY'),
                Text(cv['summary'] as String),
                const SizedBox(height: 16),
              ],

              // Experience
              if (cv['experience'] != null) ...[
                _sectionHeader(theme, 'EXPERIENCE'),
                ..._buildExperience(theme, cv['experience'] as List),
              ],

              // Skills
              if (cv['skills'] != null) ...[
                _sectionHeader(theme, 'SKILLS'),
                ..._buildSkills(theme, cv['skills'] as Map<String, dynamic>),
              ],
            ],
          ),
        ),

        // Bottom action bar
        Container(
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.1),
                blurRadius: 8,
                offset: const Offset(0, -2),
              ),
            ],
          ),
          padding: const EdgeInsets.all(16),
          child: SafeArea(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Format selector
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'pdf', label: Text('PDF')),
                    ButtonSegment(value: 'docx', label: Text('Word')),
                  ],
                  selected: {_format},
                  onSelectionChanged: (v) =>
                      setState(() => _format = v.first),
                ),
                const SizedBox(height: 12),

                // Download + Share row
                Row(
                  children: [
                    Expanded(
                      child: FilledButton.icon(
                        onPressed: exportState.isLoading
                            ? null
                            : () => _download(context),
                        icon: exportState.isLoading
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2),
                              )
                            : const Icon(Icons.download),
                        label: const Text('Download'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: exportState.valueOrNull != null
                            ? () => ref
                                .read(cvExportProvider.notifier)
                                .share()
                            : null,
                        icon: const Icon(Icons.share),
                        label: const Text('Share'),
                      ),
                    ),
                  ],
                ),

                // Success / error feedback
                if (exportState.hasError) ...[
                  const SizedBox(height: 8),
                  Text(
                    exportState.error.toString(),
                    style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                        fontSize: 12),
                  ),
                ],
                if (exportState.valueOrNull != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Saved to device.',
                    style: TextStyle(
                        color: Theme.of(context).colorScheme.primary,
                        fontSize: 12),
                  ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }

  // ── Section helpers ──

  Widget _sectionHeader(ThemeData theme, String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: theme.textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.bold,
              letterSpacing: 1.2,
            ),
          ),
          const Divider(height: 4),
        ],
      ),
    );
  }

  List<Widget> _buildExperience(ThemeData theme, List<dynamic> experience) {
    return experience.map<Widget>((role) {
      final map = role as Map<String, dynamic>;
      final bullets = (map['bullets'] as List<dynamic>?)
              ?.map((b) => b as String)
              .toList() ??
          [];

      return Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${map['title'] ?? ''} — ${map['company'] ?? ''}',
              style: theme.textTheme.bodyLarge
                  ?.copyWith(fontWeight: FontWeight.w600),
            ),
            if (map['dates'] != null)
              Text(
                map['dates'] as String,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            const SizedBox(height: 4),
            ...bullets.map(
              (b) => Padding(
                padding: const EdgeInsets.only(left: 12, bottom: 2),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('\u2022 '),
                    Expanded(child: Text(b)),
                  ],
                ),
              ),
            ),
          ],
        ),
      );
    }).toList();
  }

  List<Widget> _buildSkills(
      ThemeData theme, Map<String, dynamic> skills) {
    return skills.entries.map<Widget>((entry) {
      final items = entry.value is List
          ? (entry.value as List).join(', ')
          : entry.value.toString();
      return Padding(
        padding: const EdgeInsets.only(bottom: 4),
        child: RichText(
          text: TextSpan(
            style: theme.textTheme.bodyMedium,
            children: [
              TextSpan(
                text: '${entry.key}: ',
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
              TextSpan(text: items),
            ],
          ),
        ),
      );
    }).toList();
  }

  // ── Actions ──

  Future<void> _download(BuildContext context) async {
    try {
      await ref.read(cvExportProvider.notifier).export(format: _format);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Export failed: $e')),
        );
      }
    }
  }

  void _editSummary(BuildContext context, Map<String, dynamic> cv) {
    final controller =
        TextEditingController(text: cv['summary'] as String? ?? '');

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(
          left: 16,
          right: 16,
          top: 16,
          bottom: MediaQuery.of(ctx).viewInsets.bottom + 16,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Edit Summary',
                style: Theme.of(ctx).textTheme.titleMedium),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              maxLines: 5,
              decoration: const InputDecoration(
                hintText: 'Professional summary...',
              ),
            ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: () {
                final updated = Map<String, dynamic>.from(cv);
                updated['summary'] = controller.text;
                ref
                    .read(cvContentProvider.notifier)
                    .updateContent(updated);
                Navigator.pop(ctx);
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );
  }
}

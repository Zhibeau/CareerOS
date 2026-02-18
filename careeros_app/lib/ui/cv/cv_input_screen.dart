import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/career_provider.dart';
import '../../providers/cv_provider.dart';

class CVInputScreen extends ConsumerStatefulWidget {
  const CVInputScreen({super.key});

  @override
  ConsumerState<CVInputScreen> createState() => _CVInputScreenState();
}

class _CVInputScreenState extends ConsumerState<CVInputScreen> {
  final _jdController = TextEditingController();
  final _selectedRoleIds = <String>{};

  @override
  void dispose() {
    _jdController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final roles = ref.watch(rolesProvider);
    final cvContent = ref.watch(cvContentProvider);
    final theme = Theme.of(context);

    // Navigate to preview once content is generated.
    ref.listen(cvContentProvider, (prev, next) {
      if (next.hasValue && next.valueOrNull != null && !next.isLoading) {
        context.push('/cv/preview');
      }
    });

    return Scaffold(
      appBar: AppBar(title: const Text('Generate CV')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Job description input
          Text(
            'Job Description',
            style: theme.textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _jdController,
            maxLines: 8,
            decoration: const InputDecoration(
              hintText: 'Paste the job description here...',
              alignLabelWithHint: true,
            ),
          ),
          const SizedBox(height: 24),

          // Role selection
          Text(
            'Include Roles',
            style: theme.textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          roles.when(
            data: (list) {
              if (list.isEmpty) {
                return Text(
                  'No roles added yet. Add roles in the Roles screen first.',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                );
              }
              return Column(
                children: list.map((role) {
                  final label = role.company != null
                      ? '${role.title} @ ${role.company}'
                      : role.title;
                  return CheckboxListTile(
                    value: _selectedRoleIds.contains(role.id),
                    title: Text(label),
                    subtitle: role.startedAt != null
                        ? Text(
                            '${role.startedAt} — ${role.endedAt ?? "Present"}')
                        : null,
                    onChanged: (checked) {
                      setState(() {
                        if (checked == true) {
                          _selectedRoleIds.add(role.id);
                        } else {
                          _selectedRoleIds.remove(role.id);
                        }
                      });
                    },
                    controlAffinity: ListTileControlAffinity.leading,
                    contentPadding: EdgeInsets.zero,
                  );
                }).toList(),
              );
            },
            loading: () => const CircularProgressIndicator(),
            error: (err, _) => Text('Error: $err'),
          ),
          const SizedBox(height: 32),

          // Generate button
          FilledButton.icon(
            onPressed: cvContent.isLoading ||
                    _jdController.text.trim().isEmpty ||
                    _selectedRoleIds.isEmpty
                ? null
                : () => ref.read(cvContentProvider.notifier).preview(
                      jobDescription: _jdController.text.trim(),
                      roleIds: _selectedRoleIds.toList(),
                    ),
            icon: cvContent.isLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.description_outlined),
            label:
                Text(cvContent.isLoading ? 'Generating...' : 'Generate CV'),
          ),

          if (cvContent.hasError) ...[
            const SizedBox(height: 16),
            Card(
              color: theme.colorScheme.errorContainer,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text(
                  cvContent.error.toString(),
                  style: TextStyle(
                    color: theme.colorScheme.onErrorContainer,
                  ),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

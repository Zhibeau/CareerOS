import 'package:drift/drift.dart' show Value;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../data/local/database.dart';
import '../../../providers/career_provider.dart';

void showProjectEditDialog(
  BuildContext context, {
  required Project project,
  required VoidCallback onSaved,
}) {
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    builder: (context) => _ProjectEditSheet(
      project: project,
      onSaved: onSaved,
    ),
  );
}

class _ProjectEditSheet extends ConsumerStatefulWidget {
  final Project project;
  final VoidCallback onSaved;

  const _ProjectEditSheet({
    required this.project,
    required this.onSaved,
  });

  @override
  ConsumerState<_ProjectEditSheet> createState() => _ProjectEditSheetState();
}

class _ProjectEditSheetState extends ConsumerState<_ProjectEditSheet> {
  late final TextEditingController _nameCtrl;
  late final TextEditingController _summaryCtrl;
  String? _selectedRoleId;

  @override
  void initState() {
    super.initState();
    _nameCtrl = TextEditingController(text: widget.project.name);
    _summaryCtrl = TextEditingController(text: widget.project.summary);
    _selectedRoleId = widget.project.roleId;
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _summaryCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final roles = ref.watch(rolesProvider);
    final theme = Theme.of(context);

    return Padding(
      padding: EdgeInsets.fromLTRB(
        24,
        24,
        24,
        MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('Edit Project', style: theme.textTheme.titleLarge),
          const SizedBox(height: 16),

          TextField(
            controller: _nameCtrl,
            decoration: const InputDecoration(labelText: 'Name'),
            textInputAction: TextInputAction.next,
          ),
          const SizedBox(height: 12),

          TextField(
            controller: _summaryCtrl,
            decoration: const InputDecoration(labelText: 'Summary'),
            maxLines: 3,
          ),
          const SizedBox(height: 12),

          // Role selector
          roles.when(
            data: (roleList) {
              return DropdownButtonFormField<String?>(
                value: _selectedRoleId,
                decoration: const InputDecoration(labelText: 'Linked Role'),
                items: [
                  const DropdownMenuItem(
                    value: null,
                    child: Text('None'),
                  ),
                  ...roleList.map((r) {
                    final label = r.company != null
                        ? '${r.title} @ ${r.company}'
                        : r.title;
                    return DropdownMenuItem(
                      value: r.id,
                      child: Text(label),
                    );
                  }),
                ],
                onChanged: (value) =>
                    setState(() => _selectedRoleId = value),
              );
            },
            loading: () => const LinearProgressIndicator(),
            error: (_, __) => const SizedBox.shrink(),
          ),
          const SizedBox(height: 24),

          Row(
            children: [
              // Delete button
              OutlinedButton(
                onPressed: () async {
                  final db = ref.read(databaseProvider);
                  await db.deleteProject(widget.project.id);
                  ref.invalidate(projectsProvider);
                  ref.invalidate(statsProvider);
                  if (context.mounted) Navigator.pop(context);
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: theme.colorScheme.error,
                  minimumSize: Size.zero,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 14,
                  ),
                ),
                child: const Text('Delete'),
              ),
              const Spacer(),
              // Save button
              FilledButton(
                onPressed: () async {
                  final db = ref.read(databaseProvider);
                  await db.updateProject(ProjectsCompanion(
                    id: Value(widget.project.id),
                    name: Value(_nameCtrl.text.trim()),
                    summary: Value(_summaryCtrl.text.trim()),
                    roleId: Value(_selectedRoleId),
                  ));
                  widget.onSaved();
                  ref.invalidate(statsProvider);
                  if (context.mounted) Navigator.pop(context);
                },
                child: const Text('Save'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

import '../data/remote/extract_api.dart';
import 'auth_provider.dart';
import 'career_provider.dart';

// ── CV preview (structured JSON content from Claude) ──

final cvContentProvider =
    AsyncNotifierProvider<CVContentNotifier, Map<String, dynamic>?>(
  CVContentNotifier.new,
);

class CVContentNotifier extends AsyncNotifier<Map<String, dynamic>?> {
  @override
  Future<Map<String, dynamic>?> build() async => null;

  /// Gather career data for the selected roles and call the backend
  /// to generate structured CV content for in-app preview.
  Future<void> preview({
    required String jobDescription,
    required List<String> roleIds,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final db = ref.read(databaseProvider);

      final allRoles = await db.getAllRoles();
      final selectedRoles =
          allRoles.where((r) => roleIds.contains(r.id)).toList();

      final allProjects = await db.getAllProjects();
      final allSkills = await db.getAllSkills();
      final allAchievements = await db.getAllAchievements();

      final careerData = {
        'roles': selectedRoles
            .map((r) => {
                  'title': r.title,
                  'company': r.company,
                  'started_at': r.startedAt,
                  'ended_at': r.endedAt,
                })
            .toList(),
        'projects': allProjects
            .where(
                (p) => p.roleId != null && roleIds.contains(p.roleId))
            .map((p) => {
                  'name': p.name,
                  'summary': p.summary,
                  'role_id': p.roleId,
                })
            .toList(),
        'skills': allSkills
            .map((s) => {'name': s.name, 'category': s.category})
            .toList(),
        'achievements': allAchievements
            .map((a) => {'summary': a.summary, 'impact': a.impact})
            .toList(),
      };

      final api = ExtractApi(ref.read(apiClientProvider));
      return await api.previewCV(
        careerData: careerData,
        jobDescription: jobDescription,
      );
    });
  }

  /// Update preview content after the user edits it in the preview screen.
  void updateContent(Map<String, dynamic> edited) {
    state = AsyncData(edited);
  }
}

// ── CV export (render preview content to PDF/DOCX) ──

final cvExportProvider =
    AsyncNotifierProvider<CVExportNotifier, String?>(CVExportNotifier.new);

class CVExportNotifier extends AsyncNotifier<String?> {
  @override
  Future<String?> build() async => null;

  /// Render the current preview content to the requested format,
  /// save to the documents directory, and return the file path.
  Future<String> export({required String format}) async {
    final content = ref.read(cvContentProvider).valueOrNull;
    if (content == null) {
      throw StateError('No CV content to export');
    }

    state = const AsyncLoading();

    final result = await AsyncValue.guard(() async {
      final api = ExtractApi(ref.read(apiClientProvider));
      final bytes = await api.renderCV(
        cvContent: content,
        format: format,
      );

      final dir = await getApplicationDocumentsDirectory();
      final ext = format == 'pdf' ? 'pdf' : 'docx';
      final fileName =
          'CareerOS_CV_${DateTime.now().millisecondsSinceEpoch}.$ext';
      final file = File('${dir.path}/$fileName');
      await file.writeAsBytes(bytes);

      return file.path;
    });

    state = result;
    return result.valueOrNull ?? (throw result.error!);
  }

  /// Share the most recently exported file.
  Future<void> share() async {
    final path = state.valueOrNull;
    if (path == null) return;
    await Share.shareXFiles([XFile(path)], text: 'My CareerOS CV');
  }
}

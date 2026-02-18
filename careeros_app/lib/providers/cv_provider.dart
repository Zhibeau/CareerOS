import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

import '../data/remote/extract_api.dart';
import 'auth_provider.dart';
import 'career_provider.dart';

final cvStateProvider =
    AsyncNotifierProvider<CVNotifier, String?>(CVNotifier.new);

class CVNotifier extends AsyncNotifier<String?> {
  @override
  Future<String?> build() async => null;

  Future<void> generate({
    required String jobDescription,
    required List<String> roleIds,
    required String format,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final db = ref.read(databaseProvider);

      // Gather career data for selected roles.
      final allRoles = await db.getAllRoles();
      final selectedRoles =
          allRoles.where((r) => roleIds.contains(r.id)).toList();

      final allProjects = await db.getAllProjects();
      final allSkills = await db.getAllSkills();
      final allAchievements = await db.getAllAchievements();

      // Build career data payload.
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
            .where((p) =>
                p.roleId != null && roleIds.contains(p.roleId))
            .map((p) => {
                  'name': p.name,
                  'summary': p.summary,
                  'role_id': p.roleId,
                })
            .toList(),
        'skills':
            allSkills.map((s) => {'name': s.name, 'category': s.category}).toList(),
        'achievements': allAchievements
            .map((a) => {'summary': a.summary, 'impact': a.impact})
            .toList(),
      };

      // Call backend.
      final api = ExtractApi(ref.read(apiClientProvider));
      final bytes = await api.generateCV(
        careerData: careerData,
        jobDescription: jobDescription,
        format: format,
      );

      // Save to downloads.
      final dir = await getApplicationDocumentsDirectory();
      final ext = format == 'pdf' ? 'pdf' : 'docx';
      final fileName =
          'CareerOS_CV_${DateTime.now().millisecondsSinceEpoch}.$ext';
      final file = File('${dir.path}/$fileName');
      await file.writeAsBytes(bytes);

      // Share.
      await Share.shareXFiles([XFile(file.path)],
          text: 'My CareerOS CV');

      return file.path;
    });
  }
}

import 'dart:convert';
import 'dart:io';

import 'package:drift/drift.dart' show Value;
import 'package:file_picker/file_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/local/database.dart';
import '../data/remote/extract_api.dart';
import '../domain/importers/chatgpt_importer.dart' as chatgpt;
import '../domain/importers/claude_importer.dart' as claude;
import '../domain/models/conversation.dart' as domain;
import 'auth_provider.dart';
import 'career_provider.dart';

class ImportResult {
  final String source;
  final int totalConversations;
  final int newConversations;
  final int skippedConversations;
  final int workConversations;
  final int projectsExtracted;
  final int skillsExtracted;
  final int achievementsExtracted;

  const ImportResult({
    required this.source,
    required this.totalConversations,
    required this.newConversations,
    required this.skippedConversations,
    required this.workConversations,
    required this.projectsExtracted,
    required this.skillsExtracted,
    required this.achievementsExtracted,
  });
}

final importStateProvider =
    AsyncNotifierProvider<ImportNotifier, ImportResult?>(ImportNotifier.new);

class ImportNotifier extends AsyncNotifier<ImportResult?> {
  @override
  Future<ImportResult?> build() async => null;

  Future<void> pickAndImport() async {
    // Pick file.
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['json'],
    );
    if (result == null || result.files.isEmpty) return;

    final filePath = result.files.single.path;
    if (filePath == null) return;

    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _importFile(filePath));

    // Refresh all data providers.
    ref.invalidate(statsProvider);
    ref.invalidate(projectsProvider);
    ref.invalidate(skillsProvider);
    ref.invalidate(achievementsProvider);
  }

  Future<ImportResult> _importFile(String filePath) async {
    final db = ref.read(databaseProvider);

    // 1. Detect format and parse locally.
    final source = _detectFormat(filePath);
    final conversations = source == 'chatgpt'
        ? chatgpt.importChatGPT(filePath)
        : claude.importClaude(filePath);

    // 2. Filter already-imported.
    final newConvs = <domain.Conversation>[];
    var skipped = 0;
    for (final conv in conversations) {
      if (await db.conversationExists(conv.id)) {
        skipped++;
      } else {
        newConvs.add(conv);
      }
    }

    // 3. Store conversations locally.
    final now = DateTime.now().toUtc().toIso8601String();
    for (final conv in newConvs) {
      await db.insertConversation(ConversationsCompanion.insert(
        id: conv.id,
        source: conv.source,
        title: conv.title,
        startedAt: Value(conv.startedAt),
        importedAt: now,
      ));
    }

    // 4. Send to backend for extraction.
    var workCount = 0;
    var projectCount = 0;
    var skillCount = 0;
    var achievementCount = 0;

    if (newConvs.isNotEmpty) {
      final api = ExtractApi(ref.read(apiClientProvider));
      final extractions = await api.extract(newConvs);

      for (final entry in extractions) {
        final convId = entry.key;
        final extraction = entry.value;

        await db.updateIsWork(convId, extraction.isWork);

        if (!extraction.isWork) continue;
        workCount++;

        // Store entities using raw parameters (domain → DB boundary).
        final projectIdByName = <String, String>{};
        final skillIdByName = <String, String>{};

        for (final project in extraction.projects) {
          final pid = await db.upsertProject(
            id: project.id,
            name: project.name,
            summary: project.summary,
            status: project.status,
            startedAt: project.startedAt,
            endedAt: project.endedAt,
            roleId: project.roleId,
          );
          projectIdByName[project.name] = pid;
          await db.linkConversationProject(convId, pid);
          projectCount++;
        }

        for (final skill in extraction.skills) {
          final sid = await db.upsertSkill(
            id: skill.id,
            name: skill.name,
            category: skill.category,
          );
          skillIdByName[skill.name.trim().toLowerCase()] = sid;
          skillCount++;
        }

        for (final achievement in extraction.achievements) {
          await db.insertAchievement(
            id: achievement.id,
            summary: achievement.summary,
            impact: achievement.impact,
            achievedAt: achievement.achievedAt,
          );
          achievementCount++;
        }

        // Wire junction links.
        for (final entry in extraction.projectSkills.entries) {
          final pid = projectIdByName[entry.key];
          if (pid == null) continue;
          for (final skillName in entry.value) {
            final sid = skillIdByName[skillName.trim().toLowerCase()];
            if (sid != null) await db.linkProjectSkill(pid, sid);
          }
        }
      }
    }

    return ImportResult(
      source: source,
      totalConversations: conversations.length,
      newConversations: newConvs.length,
      skippedConversations: skipped,
      workConversations: workCount,
      projectsExtracted: projectCount,
      skillsExtracted: skillCount,
      achievementsExtracted: achievementCount,
    );
  }

  String _detectFormat(String filePath) {
    final content = File(filePath).readAsStringSync();
    final data = jsonDecode(content);
    if (data is! List || data.isEmpty) {
      throw FormatException('Expected non-empty JSON array');
    }
    final first = data[0] as Map<String, dynamic>;
    if (first.containsKey('mapping')) return 'chatgpt';
    if (first.containsKey('chat_messages') || first.containsKey('uuid')) {
      return 'claude';
    }
    throw FormatException('Unrecognized export format');
  }
}

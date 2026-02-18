import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/local/database.dart';

// ── Database singleton ──

final databaseProvider = Provider<AppDatabase>((ref) {
  final db = AppDatabase();
  ref.onDispose(() => db.close());
  return db;
});

// ── Stats ──

final statsProvider = FutureProvider<Map<String, int>>((ref) {
  final db = ref.watch(databaseProvider);
  return db.getStats();
});

// ── Projects ──

final projectsProvider = FutureProvider<List<Project>>((ref) {
  final db = ref.watch(databaseProvider);
  return db.getAllProjects();
});

// ── Skills ──

final skillsProvider = FutureProvider<List<Skill>>((ref) {
  final db = ref.watch(databaseProvider);
  return db.getAllSkills();
});

// ── Achievements ──

final achievementsProvider = FutureProvider<List<Achievement>>((ref) {
  final db = ref.watch(databaseProvider);
  return db.getAllAchievements();
});

// ── Roles ──

final rolesProvider = FutureProvider<List<Role>>((ref) {
  final db = ref.watch(databaseProvider);
  return db.getAllRoles();
});

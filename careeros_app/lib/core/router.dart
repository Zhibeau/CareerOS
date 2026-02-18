import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/auth_provider.dart';
import '../ui/auth/login_screen.dart';
import '../ui/auth/register_screen.dart';
import '../ui/database/achievements_screen.dart';
import '../ui/database/dashboard_screen.dart';
import '../ui/database/projects_screen.dart';
import '../ui/database/roles_screen.dart';
import '../ui/database/skills_screen.dart';
import '../ui/cv/cv_input_screen.dart';
import '../ui/import/import_screen.dart';
import '../ui/settings/settings_screen.dart';
import '../ui/shared/shell_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: '/dashboard',
    redirect: (context, state) {
      final isLoggedIn = authState.valueOrNull?.isLoggedIn ?? false;
      final isAuthRoute = state.matchedLocation == '/login' ||
          state.matchedLocation == '/register';

      if (!isLoggedIn && !isAuthRoute) return '/login';
      if (isLoggedIn && isAuthRoute) return '/dashboard';
      return null;
    },
    routes: [
      // Auth routes (no shell)
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),

      // Main app with bottom navigation shell
      ShellRoute(
        builder: (context, state, child) => ShellScreen(child: child),
        routes: [
          GoRoute(
            path: '/dashboard',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: DashboardScreen(),
            ),
            routes: [
              GoRoute(
                path: 'projects',
                builder: (context, state) => const ProjectsScreen(),
              ),
              GoRoute(
                path: 'skills',
                builder: (context, state) => const SkillsScreen(),
              ),
              GoRoute(
                path: 'achievements',
                builder: (context, state) => const AchievementsScreen(),
              ),
              GoRoute(
                path: 'roles',
                builder: (context, state) => const RolesScreen(),
              ),
            ],
          ),
          GoRoute(
            path: '/import',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: ImportScreen(),
            ),
          ),
          GoRoute(
            path: '/cv',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: CVInputScreen(),
            ),
          ),
          GoRoute(
            path: '/settings',
            pageBuilder: (context, state) => const NoTransitionPage(
              child: SettingsScreen(),
            ),
          ),
        ],
      ),
    ],
  );
});

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../core/constants.dart';
import '../data/remote/api_client.dart';
import '../data/remote/auth_api.dart';

// ── Shared instances ──

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());
final authApiProvider = Provider<AuthApi>(
  (ref) => AuthApi(ref.watch(apiClientProvider)),
);

// ── Auth state ──

class AuthState {
  final bool isLoggedIn;
  final String? email;

  const AuthState({this.isLoggedIn = false, this.email});

  AuthState copyWith({bool? isLoggedIn, String? email}) => AuthState(
        isLoggedIn: isLoggedIn ?? this.isLoggedIn,
        email: email ?? this.email,
      );
}

final authStateProvider =
    AsyncNotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

class AuthNotifier extends AsyncNotifier<AuthState> {
  final _storage = const FlutterSecureStorage();

  @override
  Future<AuthState> build() async {
    // Check if we have a stored token on startup.
    final token = await _storage.read(key: AppConstants.accessTokenKey);
    if (token != null) {
      return const AuthState(isLoggedIn: true);
    }
    return const AuthState();
  }

  Future<void> login({
    required String email,
    required String password,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final api = ref.read(authApiProvider);
      final tokens = await api.login(email: email, password: password);
      await _storeTokens(tokens.accessToken, tokens.refreshToken);
      return AuthState(isLoggedIn: true, email: email);
    });
  }

  Future<void> register({
    required String email,
    required String password,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final api = ref.read(authApiProvider);
      final tokens = await api.register(email: email, password: password);
      await _storeTokens(tokens.accessToken, tokens.refreshToken);
      return AuthState(isLoggedIn: true, email: email);
    });
  }

  Future<void> logout() async {
    await _storage.delete(key: AppConstants.accessTokenKey);
    await _storage.delete(key: AppConstants.refreshTokenKey);
    state = const AsyncData(AuthState());
  }

  Future<void> _storeTokens(String access, String refresh) async {
    await _storage.write(key: AppConstants.accessTokenKey, value: access);
    await _storage.write(key: AppConstants.refreshTokenKey, value: refresh);
  }
}

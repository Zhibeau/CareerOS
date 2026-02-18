class AppConstants {
  AppConstants._();

  /// Base URL for the CareerOS backend API.
  /// Override with --dart-define=API_BASE_URL=... for different environments.
  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000', // Android emulator → host
  );

  /// Token storage keys.
  static const accessTokenKey = 'access_token';
  static const refreshTokenKey = 'refresh_token';

  /// Rate limits shown to user.
  static const maxConversationsPerDay = 50;
}

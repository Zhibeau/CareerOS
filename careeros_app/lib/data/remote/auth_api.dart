import 'package:dio/dio.dart';

import 'api_client.dart';

class AuthTokens {
  final String accessToken;
  final String refreshToken;

  const AuthTokens({
    required this.accessToken,
    required this.refreshToken,
  });

  factory AuthTokens.fromJson(Map<String, dynamic> json) => AuthTokens(
        accessToken: json['access_token'] as String,
        refreshToken: json['refresh_token'] as String,
      );
}

class AuthApi {
  final ApiClient _client;

  AuthApi(this._client);

  Future<AuthTokens> register({
    required String email,
    required String password,
  }) async {
    final response = await _client.dio.post('/auth/register', data: {
      'email': email,
      'password': password,
    });
    return AuthTokens.fromJson(response.data as Map<String, dynamic>);
  }

  Future<AuthTokens> login({
    required String email,
    required String password,
  }) async {
    final response = await _client.dio.post('/auth/login', data: {
      'email': email,
      'password': password,
    });
    return AuthTokens.fromJson(response.data as Map<String, dynamic>);
  }

  Future<Map<String, dynamic>> getProfile() async {
    final response = await _client.dio.get('/auth/me');
    return response.data as Map<String, dynamic>;
  }
}

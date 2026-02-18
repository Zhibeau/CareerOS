import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../core/constants.dart';

class ApiClient {
  late final Dio dio;
  final FlutterSecureStorage _storage;

  ApiClient({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage() {
    dio = Dio(BaseOptions(
      baseUrl: AppConstants.apiBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ));

    dio.interceptors.add(_AuthInterceptor(_storage, dio));
  }
}

class _AuthInterceptor extends Interceptor {
  final FlutterSecureStorage _storage;
  final Dio _dio;

  _AuthInterceptor(this._storage, this._dio);

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // Skip auth header for login/register.
    if (options.path.contains('/auth/login') ||
        options.path.contains('/auth/register')) {
      return handler.next(options);
    }

    final token = await _storage.read(key: AppConstants.accessTokenKey);
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // Try refresh.
      final refreshed = await _tryRefresh();
      if (refreshed) {
        // Retry original request with new token.
        final token =
            await _storage.read(key: AppConstants.accessTokenKey);
        final options = err.requestOptions;
        options.headers['Authorization'] = 'Bearer $token';
        try {
          final response = await _dio.fetch(options);
          return handler.resolve(response);
        } on DioException catch (e) {
          return handler.next(e);
        }
      }
    }
    handler.next(err);
  }

  Future<bool> _tryRefresh() async {
    final refreshToken =
        await _storage.read(key: AppConstants.refreshTokenKey);
    if (refreshToken == null) return false;

    try {
      final response = await Dio(BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
      )).post('/auth/refresh', data: {'refresh_token': refreshToken});

      final newAccess = response.data['access_token'] as String;
      await _storage.write(
          key: AppConstants.accessTokenKey, value: newAccess);
      return true;
    } catch (_) {
      // Refresh failed — clear tokens, force re-login.
      await _storage.delete(key: AppConstants.accessTokenKey);
      await _storage.delete(key: AppConstants.refreshTokenKey);
      return false;
    }
  }
}

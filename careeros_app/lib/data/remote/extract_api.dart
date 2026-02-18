import 'package:dio/dio.dart';

import '../../domain/models/conversation.dart';
import '../../domain/models/extraction_result.dart';
import 'api_client.dart';

class ExtractApi {
  final ApiClient _client;

  ExtractApi(this._client);

  /// Send conversations to the backend for LLM extraction.
  Future<List<MapEntry<String, ExtractionResult>>> extract(
    List<Conversation> conversations,
  ) async {
    final response = await _client.dio.post(
      '/extract',
      data: {
        'conversations': conversations.map((c) => c.toJson()).toList(),
      },
    );

    final results = response.data['results'] as List<dynamic>;
    return results.map((r) {
      final map = r as Map<String, dynamic>;
      return MapEntry(
        map['conversation_id'] as String,
        ExtractionResult.fromJson(map['extraction'] as Map<String, dynamic>),
      );
    }).toList();
  }

  /// Generate structured CV content (JSON) for in-app preview.
  Future<Map<String, dynamic>> previewCV({
    required Map<String, dynamic> careerData,
    required String jobDescription,
  }) async {
    final response = await _client.dio.post(
      '/cv/preview',
      data: {
        'career_data': careerData,
        'job_description': jobDescription,
      },
    );

    return response.data as Map<String, dynamic>;
  }

  /// Render CV content to PDF or DOCX bytes.
  Future<List<int>> renderCV({
    required Map<String, dynamic> cvContent,
    required String format,
  }) async {
    final response = await _client.dio.post(
      '/cv/render',
      data: {
        'cv_content': cvContent,
        'format': format,
      },
      options: Options(responseType: ResponseType.bytes),
    );

    return response.data as List<int>;
  }

  /// Combined: generate and render in one call. Returns raw bytes.
  Future<List<int>> generateCV({
    required Map<String, dynamic> careerData,
    required String jobDescription,
    required String format,
  }) async {
    final response = await _client.dio.post(
      '/cv/generate',
      data: {
        'career_data': careerData,
        'job_description': jobDescription,
        'format': format,
      },
      options: Options(responseType: ResponseType.bytes),
    );

    return response.data as List<int>;
  }
}

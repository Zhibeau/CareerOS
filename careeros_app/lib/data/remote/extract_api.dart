import '../../domain/models/conversation.dart';
import '../../domain/models/extraction_result.dart';
import 'api_client.dart';

class ExtractApi {
  final ApiClient _client;

  ExtractApi(this._client);

  /// Send conversations to the backend for LLM extraction.
  /// Returns a list of (conversationId, ExtractionResult) pairs.
  Future<List<MapEntry<String, ExtractionResult>>> extract(
    List<Conversation> conversations,
  ) async {
    final response = await _client.dio.post(
      '/extract',
      data: {
        'conversations':
            conversations.map((c) => c.toJson()).toList(),
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

  /// Generate a CV document on the server.
  /// Returns raw bytes (PDF or DOCX).
  Future<List<int>> generateCV({
    required Map<String, dynamic> careerData,
    required String jobDescription,
    required String format, // "pdf" or "docx"
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

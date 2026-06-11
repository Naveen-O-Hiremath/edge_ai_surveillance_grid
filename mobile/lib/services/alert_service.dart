import 'dart:convert';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class AlertService {
  static const String wsUrl = 'ws://10.0.2.2:8000/ws/live';
  static WebSocketChannel? _channel;
  static Function(Map<String, dynamic>)? onAlert;

  static Future<void> initialize(FlutterLocalNotificationsPlugin plugin) async {
    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    const ios = DarwinInitializationSettings();
    await plugin.initialize(
      const InitializationSettings(android: android, iOS: ios),
      onDidReceiveNotificationResponse: (details) {},
    );

    const channel = AndroidNotificationChannel(
      'sentinel_alerts',
      'Security Alerts',
      description: 'Critical security notifications from Sentinel AI',
      importance: Importance.max,
      playSound: true,
    );

    await plugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);
  }

  static void connect() {
    _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
    _channel!.stream.listen((message) {
      final data = jsonDecode(message as String) as Map<String, dynamic>;
      if (data['type'] == 'alert' || data['type'] == 'alarm') {
        onAlert?.call(data['data'] as Map<String, dynamic>);
      }
    });
  }

  static Future<void> showAlert(
    FlutterLocalNotificationsPlugin plugin,
    Map<String, dynamic> alert,
  ) async {
    final severity = alert['severity'] ?? 'high';
    final isCritical = severity == 'critical';

    await plugin.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      'Sentinel AI — ${severity.toString().toUpperCase()}',
      alert['title'] ?? 'Security Alert',
      NotificationDetails(
        android: AndroidNotificationDetails(
          'sentinel_alerts',
          'Security Alerts',
          importance: isCritical ? Importance.max : Importance.high,
          priority: isCritical ? Priority.max : Priority.high,
          playSound: alert['sound_enabled'] ?? true,
          enableVibration: true,
        ),
        iOS: const DarwinNotificationDetails(
          presentAlert: true,
          presentSound: true,
          presentBadge: true,
        ),
      ),
    );
  }

  static void disconnect() {
    _channel?.sink.close();
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import '../main.dart';
import '../services/alert_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final List<Map<String, dynamic>> _alerts = [];
  bool _connected = false;

  @override
  void initState() {
    super.initState();
    AlertService.onAlert = (alert) {
      setState(() => _alerts.insert(0, alert));
      AlertService.showAlert(notifications, alert);
    };
    AlertService.connect();
    setState(() => _connected = true);
  }

  @override
  void dispose() {
    AlertService.disconnect();
    super.dispose();
  }

  Color _severityColor(String? severity) {
    switch (severity) {
      case 'critical':
        return const Color(0xFFEF4444);
      case 'high':
        return const Color(0xFFF97316);
      case 'medium':
        return const Color(0xFFEAB308);
      default:
        return const Color(0xFF3B82F6);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Sentinel AI'),
        backgroundColor: const Color(0xFF111827),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Row(
              children: [
                Icon(
                  Icons.circle,
                  size: 10,
                  color: _connected ? Colors.green : Colors.red,
                ),
                const SizedBox(width: 6),
                Text(
                  _connected ? 'Live' : 'Offline',
                  style: const TextStyle(fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
      body: _alerts.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.shield_outlined, size: 64, color: Colors.grey[700]),
                  const SizedBox(height: 16),
                  Text(
                    'All Clear',
                    style: TextStyle(fontSize: 20, color: Colors.grey[400]),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Alerts will appear here in real-time',
                    style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                  ),
                ],
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _alerts.length,
              itemBuilder: (context, index) {
                final alert = _alerts[index];
                final severity = alert['severity'] as String?;
                return Card(
                  color: const Color(0xFF1A2234),
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    leading: Icon(
                      Icons.warning_amber_rounded,
                      color: _severityColor(severity),
                    ),
                    title: Text(
                      alert['title'] ?? 'Alert',
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    subtitle: Text(
                      'Risk: ${alert['risk_score'] ?? 'N/A'} · ${severity ?? 'unknown'}',
                    ),
                    trailing: Text(
                      severity?.toUpperCase() ?? '',
                      style: TextStyle(
                        color: _severityColor(severity),
                        fontWeight: FontWeight.bold,
                        fontSize: 11,
                      ),
                    ),
                  ),
                );
              },
            ),
    );
  }
}

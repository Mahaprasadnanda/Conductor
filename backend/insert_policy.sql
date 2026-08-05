INSERT INTO rate_limit_policies (service_id, "limit", window_seconds, algorithm, enabled, created_at) VALUES (3, 100, 10, 'SLIDING_WINDOW_LOG', true, NOW());

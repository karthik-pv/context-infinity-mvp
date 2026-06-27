INSERT INTO decision_nodes (title, decision, rationale, tradeoffs, confidence, tags)
VALUES
('Use Redis for DB Cache Layer',
 'Redis is the primary caching and ephemeral storage layer.',
 'Fast reads and TTL support.',
 ARRAY['Infra overhead'],
 0.96,
 ARRAY['db','redis']),

('Short JWT TTL',
 'JWT access tokens expire after 30 seconds.',
 'Reduce replay attack risk.',
 ARRAY['More refresh requests'],
 0.98,
 ARRAY['auth','jwt','security']),

('Refresh Rotation',
 'Refresh tokens rotate on every refresh request.',
 'Prevents stolen refresh token reuse.',
 ARRAY['More writes'],
 0.95,
 ARRAY['auth','security']),

('Redis Cache TTL',
 'Cache entries expire after 5 minutes.',
 'Balance freshness and performance.',
 ARRAY['More misses'],
 0.90,
 ARRAY['cache','redis']),

('Soft Delete Users',
 'Users are soft deleted via deleted_at.',
 'Preserve recoverability.',
 ARRAY['Complex queries'],
 0.93,
 ARRAY['postgres','users']),

('Session Persistence',
 'User sessions are stored in Postgres.',
 'Required for audit trail.',
 ARRAY['Extra writes'],
 0.89,
 ARRAY['session','postgres']),

('Auth Before Routes',
 'Authentication middleware runs before all protected routes.',
 'Ensure access control.',
 ARRAY['Latency'],
 0.97,
 ARRAY['auth','middleware']),

('Thin Controllers',
 'Controllers contain no business logic.',
 'Maintain clean architecture.',
 ARRAY['More abstraction'],
 0.95,
 ARRAY['architecture']),

('Service Layer Rule',
 'Business logic lives in service layer.',
 'Improve maintainability.',
 ARRAY['More files'],
 0.94,
 ARRAY['architecture']),

('Idempotent Login',
 'Login requests must be idempotent.',
 'Avoid duplicate session creation.',
 ARRAY['Extra checks'],
 0.91,
 ARRAY['auth']),

('Rate Limit Login',
 'Login attempts capped at 5/min/IP.',
 'Prevent brute force attacks.',
 ARRAY['Potential false positives'],
 0.94,
 ARRAY['security','rate-limit']),

('Audit Login Events',
 'Every login attempt is logged.',
 'Security visibility.',
 ARRAY['Storage cost'],
 0.88,
 ARRAY['audit','security']),

('Refresh Token Blacklist',
 'Invalidated refresh tokens go to Redis blacklist.',
 'Prevent replay.',
 ARRAY['Memory overhead'],
 0.92,
 ARRAY['redis','auth']),

('Cleanup Expired Sessions',
 'Expired sessions cleaned every 10 mins.',
 'Reduce stale session growth.',
 ARRAY['Background jobs'],
 0.87,
 ARRAY['jobs','session']),

('Postgres Index Users Email',
 'Email column must be indexed.',
 'Fast user lookup.',
 ARRAY['Index storage'],
 0.93,
 ARRAY['postgres','performance']),

('API Versioning',
 'All routes are prefixed with /v1.',
 'Future-proof APIs.',
 ARRAY['Longer routes'],
 0.85,
 ARRAY['api']),

('Structured Error Responses',
 'API errors must follow standard JSON schema.',
 'Consistent client handling.',
 ARRAY['Boilerplate'],
 0.90,
 ARRAY['api']),

('Central Exception Handler',
 'Unhandled errors go through global handler.',
 'Prevent leaking internal errors.',
 ARRAY['Less local flexibility'],
 0.94,
 ARRAY['api','errors']),

('Delayed Cleanup Startup',
 'Cleanup job waits 5s after boot.',
 'Avoid DB race during startup.',
 ARRAY['Slight delay'],
 0.82,
 ARRAY['jobs']),

('Connection Pool Limit',
 'Postgres pool limited to 20 connections.',
 'Prevent connection exhaustion.',
 ARRAY['Queueing under load'],
 0.91,
 ARRAY['postgres','performance']);

 -- db-level
INSERT INTO decision_artifacts (decision_id, artifact_type, artifact_ref, is_display_anchor)
SELECT id, 'folder', 'db', TRUE FROM decision_nodes
WHERE title = 'Use Redis for DB Cache Layer';

-- jwt.py
INSERT INTO decision_artifacts (decision_id, artifact_type, artifact_ref, is_display_anchor)
SELECT id, 'file', 'db/redis/jwt.py', TRUE FROM decision_nodes
WHERE title IN (
    'Short JWT TTL',
    'Refresh Rotation',
    'Refresh Token Blacklist'
);

-- cache.py
INSERT INTO decision_artifacts (decision_id, artifact_type, artifact_ref, is_display_anchor)
SELECT id, 'file', 'db/redis/cache.py', TRUE FROM decision_nodes
WHERE title = 'Redis Cache TTL';

-- user.py
INSERT INTO decision_artifacts (decision_id, artifact_type, artifact_ref, is_display_anchor)
SELECT id, 'file', 'db/postgres/user.py', TRUE FROM decision_nodes
WHERE title IN (
    'Soft Delete Users',
    'Postgres Index Users Email',
    'Connection Pool Limit'
);

-- session.py
INSERT INTO decision_artifacts (decision_id, artifact_type, artifact_ref, is_display_anchor)
SELECT id, 'file', 'db/postgres/session.py', TRUE FROM decision_nodes
WHERE title = 'Session Persistence';

-- auth/service.py
INSERT INTO decision_artifacts (decision_id, artifact_type, artifact_ref, is_display_anchor)
SELECT id, 'file', 'auth/service.py', TRUE FROM decision_nodes
WHERE title IN (
    'Service Layer Rule',
    'Idempotent Login'
);

-- auth/middleware.py
INSERT INTO decision_artifacts (decision_id, artifact_type, artifact_ref, is_display_anchor)
SELECT id, 'file', 'auth/middleware.py', TRUE FROM decision_nodes
WHERE title IN (
    'Auth Before Routes',
    'Rate Limit Login'
);

-- auth/refresh.py
INSERT INTO decision_artifacts (decision_id, artifact_type, artifact_ref, is_display_anchor)
SELECT id, 'file', 'auth/refresh.py', TRUE FROM decision_nodes
WHERE title = 'Audit Login Events';

-- api/controllers.py
INSERT INTO decision_artifacts (decision_id, artifact_type, artifact_ref, is_display_anchor)
SELECT id, 'file', 'api/controllers.py', TRUE FROM decision_nodes
WHERE title IN (
    'Thin Controllers',
    'Structured Error Responses'
);

-- api/routes.py
INSERT INTO decision_artifacts (decision_id, artifact_type, artifact_ref, is_display_anchor)
SELECT id, 'file', 'api/routes.py', TRUE FROM decision_nodes
WHERE title IN (
    'API Versioning',
    'Central Exception Handler'
);

-- jobs/cleanup.py
INSERT INTO decision_artifacts (decision_id, artifact_type, artifact_ref, is_display_anchor)
SELECT id, 'file', 'jobs/cleanup.py', TRUE FROM decision_nodes
WHERE title IN (
    'Cleanup Expired Sessions',
    'Delayed Cleanup Startup'
);
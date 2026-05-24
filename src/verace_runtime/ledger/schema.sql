CREATE TABLE IF NOT EXISTS runtime_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS persons (
  id TEXT PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contours (
  id TEXT PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contour_memberships (
  person_id TEXT NOT NULL REFERENCES persons(id),
  contour_id TEXT NOT NULL REFERENCES contours(id),
  role TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (person_id, contour_id)
);

CREATE TABLE IF NOT EXISTS mandates (
  id TEXT PRIMARY KEY,
  public_id TEXT NOT NULL UNIQUE,
  principal_person_id TEXT NOT NULL REFERENCES persons(id),
  contour_id TEXT NOT NULL REFERENCES contours(id),
  title TEXT NOT NULL,
  scope TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY,
  public_id TEXT NOT NULL UNIQUE,
  contour_id TEXT NOT NULL REFERENCES contours(id),
  principal_person_id TEXT NOT NULL REFERENCES persons(id),
  text TEXT NOT NULL,
  kind TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
  id TEXT PRIMARY KEY,
  public_id TEXT NOT NULL UNIQUE,
  contour_id TEXT NOT NULL REFERENCES contours(id),
  mandate_id TEXT NOT NULL REFERENCES mandates(id),
  message_id TEXT REFERENCES messages(id),
  title TEXT NOT NULL,
  decision_text TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  id TEXT NOT NULL UNIQUE,
  public_no TEXT UNIQUE,
  mandate_id TEXT NOT NULL REFERENCES mandates(id),
  contour_id TEXT NOT NULL REFERENCES contours(id),
  message_id TEXT REFERENCES messages(id),
  title TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_events (
  id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(id),
  event_type TEXT NOT NULL,
  summary TEXT NOT NULL,
  receipt_id TEXT NOT NULL REFERENCES receipts(id),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS approvals (
  id TEXT PRIMARY KEY,
  mandate_id TEXT REFERENCES mandates(id),
  task_id TEXT REFERENCES tasks(id),
  approval_type TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS receipts (
  id TEXT PRIMARY KEY,
  public_id TEXT NOT NULL UNIQUE,
  receipt_type TEXT NOT NULL,
  action_class TEXT NOT NULL,
  subject_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  status TEXT NOT NULL,
  policy_result TEXT NOT NULL,
  note TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claims (
  id TEXT PRIMARY KEY,
  claim_type TEXT NOT NULL,
  claim_text TEXT NOT NULL,
  subject_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  receipt_id TEXT NOT NULL REFERENCES receipts(id),
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outbox_items (
  id TEXT PRIMARY KEY,
  action_class TEXT NOT NULL,
  payload TEXT NOT NULL,
  status TEXT NOT NULL,
  receipt_id TEXT NOT NULL REFERENCES receipts(id),
  created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_active_mandate_principal_contour
ON mandates(principal_person_id, contour_id)
WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_tasks_public_no ON tasks(public_no);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at, public_id);
CREATE INDEX IF NOT EXISTS idx_receipts_subject ON receipts(subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_claims_subject ON claims(subject_type, subject_id);

BEGIN;

CREATE UNIQUE INDEX IF NOT EXISTS settlement_owner_movement_id ON settlement(owner,movement,id);

CREATE TABLE IF NOT EXISTS payment_revision (
    owner INTEGER NOT NULL,
    movement INTEGER NOT NULL,
    payment INTEGER NOT NULL,
    version INTEGER NOT NULL CHECK(version > 0),
    key TEXT NOT NULL,
    note TEXT NOT NULL CHECK(length(trim(note)) BETWEEN 1 AND 120),
    amount INTEGER CHECK(amount BETWEEN 1 AND 9999999999999),
    day TEXT,
    created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK((amount IS NULL) = (day IS NULL)),
    PRIMARY KEY(owner,movement,payment,version),
    UNIQUE(owner,key),
    FOREIGN KEY(owner,movement,payment) REFERENCES settlement(owner,movement,id),
    FOREIGN KEY(owner,key) REFERENCES request(owner,key)
);

CREATE VIEW IF NOT EXISTS effective_settlement AS
SELECT s.id,s.owner,s.movement,s.reason,
    CASE WHEN r.version IS NULL THEN s.amount ELSE r.amount END AS amount,
    COALESCE(r.day,s.day) AS day,
    COALESCE(r.version,0) AS version
FROM settlement s
LEFT JOIN payment_revision r ON r.owner=s.owner AND r.movement=s.movement AND r.payment=s.id
    AND r.version=(SELECT MAX(version) FROM payment_revision
        WHERE owner=s.owner AND movement=s.movement AND payment=s.id)
WHERE r.version IS NULL OR r.amount IS NOT NULL;

CREATE TRIGGER IF NOT EXISTS payment_revision_no_update BEFORE UPDATE ON payment_revision
BEGIN SELECT RAISE(ABORT,'Payment revision is immutable'); END;
CREATE TRIGGER IF NOT EXISTS payment_revision_no_delete BEFORE DELETE ON payment_revision
BEGIN SELECT RAISE(ABORT,'Payment revision is immutable'); END;
CREATE TRIGGER IF NOT EXISTS settlement_no_update BEFORE UPDATE ON settlement
BEGIN SELECT RAISE(ABORT,'Settlement is immutable'); END;
CREATE TRIGGER IF NOT EXISTS settlement_no_delete BEFORE DELETE ON settlement
BEGIN SELECT RAISE(ABORT,'Settlement is immutable'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit
BEGIN SELECT RAISE(ABORT,'Audit is immutable'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit
BEGIN SELECT RAISE(ABORT,'Audit is immutable'); END;

COMMIT;

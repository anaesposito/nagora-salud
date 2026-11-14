BEGIN;
CREATE TABLE IF NOT EXISTS liquidation (
 id INTEGER PRIMARY KEY, owner INTEGER NOT NULL, payer INTEGER NOT NULL, reference TEXT NOT NULL,
 UNIQUE(owner,id), UNIQUE(owner,payer,reference),
 FOREIGN KEY(owner,payer) REFERENCES payer(owner,id)
);
CREATE TABLE IF NOT EXISTS liquidation_revision (
 owner INTEGER NOT NULL, liquidation INTEGER NOT NULL, version INTEGER NOT NULL CHECK(version>0),
 key TEXT NOT NULL, fingerprint TEXT NOT NULL, day TEXT NOT NULL,
 received INTEGER NOT NULL CHECK(typeof(received)='integer' AND received BETWEEN 0 AND 9999999999999),
 method TEXT NOT NULL, note TEXT NOT NULL, payload TEXT NOT NULL,
 created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(owner,liquidation,version), UNIQUE(owner,key),
 FOREIGN KEY(owner,liquidation) REFERENCES liquidation(owner,id),
 FOREIGN KEY(owner,key) REFERENCES request(owner,key)
);
CREATE TABLE IF NOT EXISTS liquidation_allocation (
 owner INTEGER NOT NULL, liquidation INTEGER NOT NULL, version INTEGER NOT NULL, movement INTEGER NOT NULL,
 generated INTEGER NOT NULL CHECK(generated>0), allocated INTEGER NOT NULL CHECK(allocated>0),
 cash INTEGER NOT NULL CHECK(cash>=0), discount INTEGER NOT NULL CHECK(discount>=0),
 retained INTEGER NOT NULL CHECK(retained>=0), difference INTEGER NOT NULL CHECK(difference>=0),
 discount_kind TEXT NOT NULL, retention_kind TEXT NOT NULL, note TEXT NOT NULL,
 CHECK(allocated=cash+discount+retained+difference),
 CHECK(typeof(generated)='integer' AND typeof(allocated)='integer' AND typeof(cash)='integer'
       AND typeof(discount)='integer' AND typeof(retained)='integer' AND typeof(difference)='integer'),
 PRIMARY KEY(owner,liquidation,version,movement),
 FOREIGN KEY(owner,liquidation,version) REFERENCES liquidation_revision(owner,liquidation,version),
 FOREIGN KEY(owner,movement) REFERENCES movement(owner,id)
);
CREATE TABLE IF NOT EXISTS liquidation_entry (
 owner INTEGER NOT NULL, liquidation INTEGER NOT NULL, version INTEGER NOT NULL, movement INTEGER NOT NULL,
 settlement INTEGER NOT NULL, component TEXT NOT NULL CHECK(component IN ('cash','discount','retained')),
 PRIMARY KEY(owner,settlement), UNIQUE(owner,liquidation,version,movement,component),
 FOREIGN KEY(owner,liquidation,version,movement) REFERENCES liquidation_allocation(owner,liquidation,version,movement),
 FOREIGN KEY(owner,movement,settlement) REFERENCES settlement(owner,movement,id)
);
DROP VIEW IF EXISTS effective_settlement;
CREATE VIEW effective_settlement AS
SELECT s.id,s.owner,s.movement,s.reason,
 CASE WHEN r.version IS NULL THEN s.amount ELSE r.amount END AS amount,
 COALESCE(r.day,s.day) AS day, COALESCE(r.version,0) AS version
FROM settlement s
LEFT JOIN payment_revision r ON r.owner=s.owner AND r.movement=s.movement AND r.payment=s.id
 AND r.version=(SELECT MAX(version) FROM payment_revision WHERE owner=s.owner AND movement=s.movement AND payment=s.id)
LEFT JOIN liquidation_entry e ON e.owner=s.owner AND e.settlement=s.id
WHERE (r.version IS NULL OR r.amount IS NOT NULL)
 AND (e.settlement IS NULL OR e.version=(SELECT MAX(version) FROM liquidation_revision WHERE owner=e.owner AND liquidation=e.liquidation));
CREATE TRIGGER IF NOT EXISTS liquidation_no_update BEFORE UPDATE ON liquidation BEGIN SELECT RAISE(ABORT,'Liquidation is immutable'); END;
CREATE TRIGGER IF NOT EXISTS liquidation_no_delete BEFORE DELETE ON liquidation BEGIN SELECT RAISE(ABORT,'Liquidation is immutable'); END;
CREATE TRIGGER IF NOT EXISTS liquidation_revision_no_update BEFORE UPDATE ON liquidation_revision BEGIN SELECT RAISE(ABORT,'Liquidation revision is immutable'); END;
CREATE TRIGGER IF NOT EXISTS liquidation_revision_no_delete BEFORE DELETE ON liquidation_revision BEGIN SELECT RAISE(ABORT,'Liquidation revision is immutable'); END;
CREATE TRIGGER IF NOT EXISTS liquidation_allocation_no_update BEFORE UPDATE ON liquidation_allocation BEGIN SELECT RAISE(ABORT,'Allocation is immutable'); END;
CREATE TRIGGER IF NOT EXISTS liquidation_allocation_no_delete BEFORE DELETE ON liquidation_allocation BEGIN SELECT RAISE(ABORT,'Allocation is immutable'); END;
CREATE TRIGGER IF NOT EXISTS liquidation_entry_no_update BEFORE UPDATE ON liquidation_entry BEGIN SELECT RAISE(ABORT,'Allocation entry is immutable'); END;
CREATE TRIGGER IF NOT EXISTS liquidation_entry_no_delete BEFORE DELETE ON liquidation_entry BEGIN SELECT RAISE(ABORT,'Allocation entry is immutable'); END;
COMMIT;

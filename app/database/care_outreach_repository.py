"""Care Outreach Repository - Database Layer

Handles persistence for saboteur conversion through care.
"""

import sqlite3
import json
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.care_outreach import (
    CareVolunteer,
    OutreachAssignment,
    OutreachNote,
    NeedsAssessment,
    ConversionMetrics,
    OutreachStatus,
    DetectionReason,
    AccessLevel,
)


class CareOutreachRepository:
    """Repository for care outreach data"""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._init_tables()

    def _init_tables(self):
        """Initialize database tables for care outreach"""
        self.conn.executescript("""
            -- Care volunteers table
            CREATE TABLE IF NOT EXISTS care_volunteers (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                training TEXT NOT NULL,  -- JSON list
                currently_supporting INTEGER DEFAULT 0,
                max_capacity INTEGER DEFAULT 3,
                supervision_partner_id TEXT,
                joined_at TEXT NOT NULL,
                last_supervision TEXT,
                FOREIGN KEY (supervision_partner_id) REFERENCES care_volunteers(user_id)
            );

            -- Outreach assignments table
            CREATE TABLE IF NOT EXISTS outreach_assignments (
                id TEXT PRIMARY KEY,
                flagged_user_id TEXT NOT NULL,
                outreach_volunteer_id TEXT NOT NULL,
                detection_reason TEXT NOT NULL,
                detection_details TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                started_at TEXT NOT NULL,
                ended_at TEXT,
                needs_assessment TEXT,  -- JSON
                converted_at TEXT,
                conversion_story TEXT,
                FOREIGN KEY (outreach_volunteer_id) REFERENCES care_volunteers(user_id)
            );

            -- Outreach notes table
            CREATE TABLE IF NOT EXISTS outreach_notes (
                id TEXT PRIMARY KEY,
                assignment_id TEXT NOT NULL,
                volunteer_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                note TEXT NOT NULL,
                needs_identified TEXT,  -- JSON list
                resources_connected TEXT,  -- JSON list
                sentiment TEXT,
                FOREIGN KEY (assignment_id) REFERENCES outreach_assignments(id),
                FOREIGN KEY (volunteer_id) REFERENCES care_volunteers(user_id)
            );

            -- Needs assessments table
            CREATE TABLE IF NOT EXISTS needs_assessments (
                user_id TEXT PRIMARY KEY,
                assessed_by TEXT NOT NULL,
                assessed_at TEXT NOT NULL,
                housing_insecure BOOLEAN DEFAULT 0,
                food_insecure BOOLEAN DEFAULT 0,
                employment_unstable BOOLEAN DEFAULT 0,
                healthcare_access BOOLEAN DEFAULT 0,
                isolated BOOLEAN DEFAULT 0,
                past_trauma_with_orgs BOOLEAN DEFAULT 0,
                trust_issues BOOLEAN DEFAULT 0,
                being_paid_to_sabotage TEXT,
                law_enforcement TEXT,
                resources_connected TEXT,  -- JSON list
                FOREIGN KEY (assessed_by) REFERENCES care_volunteers(user_id)
            );

            -- Indexes for common queries
            CREATE INDEX IF NOT EXISTS idx_outreach_flagged_user
                ON outreach_assignments(flagged_user_id);
            CREATE INDEX IF NOT EXISTS idx_outreach_volunteer
                ON outreach_assignments(outreach_volunteer_id);
            CREATE INDEX IF NOT EXISTS idx_outreach_status
                ON outreach_assignments(status);
            CREATE INDEX IF NOT EXISTS idx_notes_assignment
                ON outreach_notes(assignment_id);
        """)
        self.conn.commit()

    # --- Care Volunteer Methods ---

    def add_volunteer(self, volunteer: CareVolunteer) -> CareVolunteer:
        """Add a new care volunteer"""
        self.conn.execute("""
            INSERT INTO care_volunteers (
                user_id, name, training, currently_supporting,
                max_capacity, supervision_partner_id, joined_at, last_supervision
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            volunteer.user_id,
            volunteer.name,
            json.dumps(volunteer.training),
            volunteer.currently_supporting,
            volunteer.max_capacity,
            volunteer.supervision_partner_id,
            volunteer.joined_at.isoformat(),
            volunteer.last_supervision.isoformat() if volunteer.last_supervision else None,
        ))
        self.conn.commit()
        return volunteer

    def get_volunteer(self, user_id: str) -> Optional[CareVolunteer]:
        """Get volunteer by user ID"""
        row = self.conn.execute("""
            SELECT user_id, name, training, currently_supporting,
                   max_capacity, supervision_partner_id, joined_at, last_supervision
            FROM care_volunteers
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        if not row:
            return None

        return CareVolunteer(
            user_id=row[0],
            name=row[1],
            training=json.loads(row[2]),
            currently_supporting=row[3],
            max_capacity=row[4],
            supervision_partner_id=row[5],
            joined_at=datetime.fromisoformat(row[6]),
            last_supervision=datetime.fromisoformat(row[7]) if row[7] else None,
        )

    def get_available_volunteers(self) -> List[CareVolunteer]:
        """Get volunteers who have capacity"""
        rows = self.conn.execute("""
            SELECT user_id, name, training, currently_supporting,
                   max_capacity, supervision_partner_id, joined_at, last_supervision
            FROM care_volunteers
            WHERE currently_supporting < max_capacity
            ORDER BY currently_supporting ASC
        """).fetchall()

        return [
            CareVolunteer(
                user_id=row[0],
                name=row[1],
                training=json.loads(row[2]),
                currently_supporting=row[3],
                max_capacity=row[4],
                supervision_partner_id=row[5],
                joined_at=datetime.fromisoformat(row[6]),
                last_supervision=datetime.fromisoformat(row[7]) if row[7] else None,
            )
            for row in rows
        ]

    def update_volunteer_capacity(self, user_id: str, delta: int):
        """Update volunteer's current capacity"""
        self.conn.execute("""
            UPDATE care_volunteers
            SET currently_supporting = currently_supporting + ?
            WHERE user_id = ?
        """, (delta, user_id))
        self.conn.commit()

    def update_volunteer_supervision(self, user_id: str, timestamp: datetime):
        """Record supervision check-in"""
        self.conn.execute("""
            UPDATE care_volunteers
            SET last_supervision = ?
            WHERE user_id = ?
        """, (timestamp.isoformat(), user_id))
        self.conn.commit()

    # --- Outreach Assignment Methods ---

    def create_assignment(self, assignment: OutreachAssignment) -> OutreachAssignment:
        """Create new outreach assignment"""
        self.conn.execute("""
            INSERT INTO outreach_assignments (
                id, flagged_user_id, outreach_volunteer_id,
                detection_reason, detection_details, status,
                started_at, ended_at, needs_assessment,
                converted_at, conversion_story
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assignment.id,
            assignment.flagged_user_id,
            assignment.outreach_volunteer_id,
            assignment.detection_reason.value,
            assignment.detection_details,
            assignment.status.value,
            assignment.started_at.isoformat(),
            assignment.ended_at.isoformat() if assignment.ended_at else None,
            json.dumps(assignment.needs_assessment) if assignment.needs_assessment else None,
            assignment.converted_at.isoformat() if assignment.converted_at else None,
            assignment.conversion_story,
        ))
        self.conn.commit()

        # Update volunteer capacity
        self.update_volunteer_capacity(assignment.outreach_volunteer_id, 1)

        return assignment

    def get_assignment(self, assignment_id: str) -> Optional[OutreachAssignment]:
        """Get assignment by ID"""
        row = self.conn.execute("""
            SELECT id, flagged_user_id, outreach_volunteer_id,
                   detection_reason, detection_details, status,
                   started_at, ended_at, needs_assessment,
                   converted_at, conversion_story
            FROM outreach_assignments
            WHERE id = ?
        """, (assignment_id,)).fetchone()

        if not row:
            return None

        # Get notes for this assignment
        notes = self.get_assignment_notes(assignment_id)

        return OutreachAssignment(
            id=row[0],
            flagged_user_id=row[1],
            outreach_volunteer_id=row[2],
            detection_reason=DetectionReason(row[3]),
            detection_details=row[4],
            status=OutreachStatus(row[5]),
            started_at=datetime.fromisoformat(row[6]),
            ended_at=datetime.fromisoformat(row[7]) if row[7] else None,
            needs_assessment=json.loads(row[8]) if row[8] else None,
            converted_at=datetime.fromisoformat(row[9]) if row[9] else None,
            conversion_story=row[10],
            notes=notes,
        )

    def get_assignment_for_user(self, user_id: str) -> Optional[OutreachAssignment]:
        """Get active outreach assignment for a user"""
        row = self.conn.execute("""
            SELECT id, flagged_user_id, outreach_volunteer_id,
                   detection_reason, detection_details, status,
                   started_at, ended_at, needs_assessment,
                   converted_at, conversion_story
            FROM outreach_assignments
            WHERE flagged_user_id = ?
            ORDER BY started_at DESC
            LIMIT 1
        """, (user_id,)).fetchone()

        if not row:
            return None

        notes = self.get_assignment_notes(row[0])

        return OutreachAssignment(
            id=row[0],
            flagged_user_id=row[1],
            outreach_volunteer_id=row[2],
            detection_reason=DetectionReason(row[3]),
            detection_details=row[4],
            status=OutreachStatus(row[5]),
            started_at=datetime.fromisoformat(row[6]),
            ended_at=datetime.fromisoformat(row[7]) if row[7] else None,
            needs_assessment=json.loads(row[8]) if row[8] else None,
            converted_at=datetime.fromisoformat(row[9]) if row[9] else None,
            conversion_story=row[10],
            notes=notes,
        )

    def update_assignment_status(
        self,
        assignment_id: str,
        status: OutreachStatus,
        conversion_story: Optional[str] = None
    ):
        """Update assignment status"""
        now = datetime.utcnow()

        if status in [OutreachStatus.CONVERTED, OutreachStatus.CHOSE_TO_LEAVE]:
            # Mark as ended
            self.conn.execute("""
                UPDATE outreach_assignments
                SET status = ?, ended_at = ?, converted_at = ?, conversion_story = ?
                WHERE id = ?
            """, (
                status.value,
                now.isoformat(),
                now.isoformat() if status == OutreachStatus.CONVERTED else None,
                conversion_story,
                assignment_id
            ))

            # Free up volunteer capacity
            assignment = self.get_assignment(assignment_id)
            if assignment:
                self.update_volunteer_capacity(assignment.outreach_volunteer_id, -1)
        else:
            self.conn.execute("""
                UPDATE outreach_assignments
                SET status = ?
                WHERE id = ?
            """, (status.value, assignment_id))

        self.conn.commit()

    def get_active_assignments(self) -> List[OutreachAssignment]:
        """Get all active outreach assignments"""
        rows = self.conn.execute("""
            SELECT id, flagged_user_id, outreach_volunteer_id,
                   detection_reason, detection_details, status,
                   started_at, ended_at, needs_assessment,
                   converted_at, conversion_story
            FROM outreach_assignments
            WHERE status = 'active'
            ORDER BY started_at DESC
        """).fetchall()

        assignments = []
        for row in rows:
            notes = self.get_assignment_notes(row[0])
            assignments.append(OutreachAssignment(
                id=row[0],
                flagged_user_id=row[1],
                outreach_volunteer_id=row[2],
                detection_reason=DetectionReason(row[3]),
                detection_details=row[4],
                status=OutreachStatus(row[5]),
                started_at=datetime.fromisoformat(row[6]),
                ended_at=datetime.fromisoformat(row[7]) if row[7] else None,
                needs_assessment=json.loads(row[8]) if row[8] else None,
                converted_at=datetime.fromisoformat(row[9]) if row[9] else None,
                conversion_story=row[10],
                notes=notes,
            ))

        return assignments

    # --- Outreach Note Methods ---

    def add_note(self, note: OutreachNote) -> OutreachNote:
        """Add note to assignment"""
        self.conn.execute("""
            INSERT INTO outreach_notes (
                id, assignment_id, volunteer_id, timestamp,
                note, needs_identified, resources_connected, sentiment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            note.id,
            note.assignment_id,
            note.volunteer_id,
            note.timestamp.isoformat(),
            note.note,
            json.dumps(note.needs_identified) if note.needs_identified else None,
            json.dumps(note.resources_connected) if note.resources_connected else None,
            note.sentiment,
        ))
        self.conn.commit()
        return note

    def get_assignment_notes(self, assignment_id: str) -> List[OutreachNote]:
        """Get all notes for an assignment"""
        rows = self.conn.execute("""
            SELECT id, assignment_id, volunteer_id, timestamp,
                   note, needs_identified, resources_connected, sentiment
            FROM outreach_notes
            WHERE assignment_id = ?
            ORDER BY timestamp ASC
        """, (assignment_id,)).fetchall()

        return [
            OutreachNote(
                id=row[0],
                assignment_id=row[1],
                volunteer_id=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                note=row[4],
                needs_identified=json.loads(row[5]) if row[5] else None,
                resources_connected=json.loads(row[6]) if row[6] else None,
                sentiment=row[7],
            )
            for row in rows
        ]

    # --- Needs Assessment Methods ---

    def save_needs_assessment(self, assessment: NeedsAssessment) -> NeedsAssessment:
        """Save needs assessment"""
        self.conn.execute("""
            INSERT OR REPLACE INTO needs_assessments (
                user_id, assessed_by, assessed_at,
                housing_insecure, food_insecure, employment_unstable,
                healthcare_access, transportation_needed,
                mental_health_crisis, substance_issues, disability_accommodation,
                childcare_needed, eldercare_needed,
                isolated, past_trauma_with_orgs,
                trust_issues, being_paid_to_sabotage, law_enforcement,
                resources_connected
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assessment.user_id,
            assessment.assessed_by,
            assessment.assessed_at.isoformat(),
            assessment.housing_insecure,
            assessment.food_insecure,
            assessment.employment_unstable,
            assessment.healthcare_access,
            assessment.transportation_needed,
            assessment.mental_health_crisis,
            assessment.substance_issues,
            assessment.disability_accommodation,
            assessment.childcare_needed,
            assessment.eldercare_needed,
            assessment.isolated,
            assessment.past_trauma_with_orgs,
            assessment.trust_issues,
            assessment.being_paid_to_sabotage,
            assessment.law_enforcement,
            json.dumps(assessment.resources_connected),
        ))
        self.conn.commit()
        return assessment

    def get_needs_assessment(self, user_id: str) -> Optional[NeedsAssessment]:
        """Get needs assessment for user"""
        row = self.conn.execute("""
            SELECT user_id, assessed_by, assessed_at,
                   housing_insecure, food_insecure, employment_unstable,
                   healthcare_access, transportation_needed,
                   mental_health_crisis, substance_issues, disability_accommodation,
                   childcare_needed, eldercare_needed,
                   isolated, past_trauma_with_orgs,
                   trust_issues, being_paid_to_sabotage, law_enforcement,
                   resources_connected
            FROM needs_assessments
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        if not row:
            return None

        return NeedsAssessment(
            user_id=row[0],
            assessed_by=row[1],
            assessed_at=datetime.fromisoformat(row[2]),
            housing_insecure=bool(row[3]),
            food_insecure=bool(row[4]),
            employment_unstable=bool(row[5]),
            healthcare_access=bool(row[6]),
            transportation_needed=bool(row[7]),
            mental_health_crisis=bool(row[8]),
            substance_issues=bool(row[9]),
            disability_accommodation=bool(row[10]),
            childcare_needed=bool(row[11]),
            eldercare_needed=bool(row[12]),
            isolated=bool(row[13]),
            past_trauma_with_orgs=bool(row[14]),
            trust_issues=bool(row[15]),
            being_paid_to_sabotage=row[16],
            law_enforcement=row[17],
            resources_connected=json.loads(row[18]) if row[18] else [],
        )

    # --- Metrics Methods ---

    def get_conversion_metrics(self) -> ConversionMetrics:
        """Get current conversion metrics"""
        # Count by status
        status_counts = self.conn.execute("""
            SELECT status, COUNT(*)
            FROM outreach_assignments
            GROUP BY status
        """).fetchall()

        counts = {status: 0 for status in OutreachStatus}
        for status, count in status_counts:
            counts[OutreachStatus(status)] = count

        # Get conversions this month
        one_month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
        converted_this_month = self.conn.execute("""
            SELECT COUNT(*)
            FROM outreach_assignments
            WHERE status = 'converted' AND converted_at >= ?
        """, (one_month_ago,)).fetchone()[0]

        # Average time to first real conversation
        # (First note with sentiment "opening_up" or needs identified)
        avg_time = self.conn.execute("""
            SELECT AVG(
                CAST((julianday(n.timestamp) - julianday(a.started_at)) AS REAL)
            )
            FROM outreach_notes n
            JOIN outreach_assignments a ON n.assignment_id = a.id
            WHERE n.sentiment IN ('opening_up', 'hopeful')
               OR n.needs_identified IS NOT NULL
        """).fetchone()[0]

        # Get conversion stories
        stories = self.conn.execute("""
            SELECT conversion_story
            FROM outreach_assignments
            WHERE status = 'converted' AND conversion_story IS NOT NULL
            LIMIT 10
        """).fetchall()

        return ConversionMetrics(
            outreach_active=counts[OutreachStatus.ACTIVE],
            converted_this_month=converted_this_month,
            chose_to_leave=counts[OutreachStatus.CHOSE_TO_LEAVE],
            still_trying=counts[OutreachStatus.STILL_TRYING],
            average_time_to_first_real_conversation=avg_time,
            conversion_stories=[story[0] for story in stories],
        )

"""Service for Knowledge Osmosis

'Knowledge emerges only through invention and re-invention.' - Paulo Freire
"""
import uuid
from datetime import datetime, UTC
from typing import List

from app.models.knowledge_osmosis import (
    StudyCircle,
    LearningArtifact,
    UnansweredQuestion,
    CircleStatus,
    ArtifactType,
    QuestionStatus,
)
from app.database.knowledge_osmosis_repository import KnowledgeOsmosisRepository


class KnowledgeOsmosisService:
    """Business logic for Knowledge Osmosis."""

    def __init__(self, db_path: str):
        self.repo = KnowledgeOsmosisRepository(db_path)

    def create_study_circle(
        self,
        name: str,
        topic: str,
        description: str,
        created_by: str,
        artifact_commitment: str
    ) -> StudyCircle:
        """Create a new study circle."""
        circle = StudyCircle(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            topic=topic,
            facilitator_user_id=created_by,
            member_count=1,
            status=CircleStatus.FORMING,
            artifact_commitment=artifact_commitment,
            created_at=datetime.now(UTC),
            created_by=created_by
        )
        return self.repo.create_study_circle(circle)

    def publish_artifact(
        self,
        circle_id: str,
        created_by_user_id: str,
        title: str,
        artifact_type: ArtifactType,
        content: str,
        topic: str,
        tags: List[str],
        difficulty: str = 'beginner',
        description: str = None,
        builds_on_artifact_id: str = None
    ) -> LearningArtifact:
        """Publish a learning artifact to the Common Heap."""
        artifact = LearningArtifact(
            id=str(uuid.uuid4()),
            circle_id=circle_id,
            created_by_user_id=created_by_user_id,
            title=title,
            description=description,
            artifact_type=artifact_type,
            content=content,
            topic=topic,
            tags=tags,
            difficulty=difficulty,
            builds_on_artifact_id=builds_on_artifact_id,
            published_at=datetime.now(UTC)
        )
        return self.repo.create_artifact(artifact)

    def discover_artifacts(self, topic: str, limit: int = 20) -> List[LearningArtifact]:
        """Discover artifacts by topic."""
        return self.repo.get_artifacts_by_topic(topic, limit)

    def ask_question(
        self,
        artifact_id: str,
        circle_id: str,
        question: str,
        context: str = None
    ) -> UnansweredQuestion:
        """Post an unanswered question."""
        q = UnansweredQuestion(
            id=str(uuid.uuid4()),
            artifact_id=artifact_id,
            circle_id=circle_id,
            question=question,
            context=context,
            status=QuestionStatus.OPEN,
            asked_at=datetime.now(UTC)
        )
        return self.repo.create_unanswered_question(q)

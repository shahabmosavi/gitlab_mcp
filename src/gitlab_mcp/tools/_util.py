"""Helpers for trimming large GitLab objects down to the fields that matter.

List endpoints can return very large objects; ``pick`` keeps responses compact so
they don't blow the model's context. The ``gitlab_api`` tool is always available
when the full, untrimmed payload is needed.
"""

from __future__ import annotations

from typing import Any


def pick(obj: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    """Return a copy of ``obj`` containing only ``fields`` that are present."""
    return {k: obj[k] for k in fields if k in obj}


def slim_many(objs: list[Any], fields: tuple[str, ...]) -> list[Any]:
    return [pick(o, fields) if isinstance(o, dict) else o for o in objs]


PROJECT_FIELDS = (
    "id",
    "name",
    "path_with_namespace",
    "description",
    "visibility",
    "default_branch",
    "web_url",
    "star_count",
    "forks_count",
    "last_activity_at",
    "archived",
)

ISSUE_FIELDS = (
    "id",
    "iid",
    "project_id",
    "title",
    "state",
    "labels",
    "assignees",
    "author",
    "milestone",
    "web_url",
    "created_at",
    "updated_at",
    "due_date",
    "user_notes_count",
)

MR_FIELDS = (
    "id",
    "iid",
    "project_id",
    "title",
    "state",
    "merge_status",
    "detailed_merge_status",
    "draft",
    "source_branch",
    "target_branch",
    "author",
    "assignees",
    "reviewers",
    "labels",
    "web_url",
    "created_at",
    "updated_at",
    "has_conflicts",
)

PIPELINE_FIELDS = (
    "id",
    "iid",
    "project_id",
    "status",
    "source",
    "ref",
    "sha",
    "web_url",
    "created_at",
    "updated_at",
)

JOB_FIELDS = (
    "id",
    "name",
    "stage",
    "status",
    "ref",
    "allow_failure",
    "started_at",
    "finished_at",
    "duration",
    "web_url",
)

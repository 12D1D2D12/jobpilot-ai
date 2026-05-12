from tools.skill_gap_tool import SkillGapTool


def test_skill_gap_tool_generates_redis_plan() -> None:
    plan = SkillGapTool().generate_learning_plan(["Redis"])

    assert len(plan) == 1
    assert "caching patterns" in plan[0]
    assert "cache penetration" in plan[0]


def test_skill_gap_tool_generates_docker_plan() -> None:
    plan = SkillGapTool().generate_learning_plan(["Docker"])

    assert len(plan) == 1
    assert "Dockerfile" in plan[0]
    assert "docker-compose" in plan[0]


def test_skill_gap_tool_generates_generic_plan_for_unknown_skill() -> None:
    plan = SkillGapTool().generate_learning_plan(["Kafka"])

    assert len(plan) == 1
    assert "Kafka" in plan[0]
    assert "hands-on project" in plan[0]

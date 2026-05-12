class SkillGapTool:
    _SKILL_PLANS = {
        "redis": "Redis: study caching patterns, core data structures, connection pools, cache penetration, cache breakdown, and cache avalanche.",
        "docker": "Docker: study Dockerfile, images, containers, volumes, networks, and docker-compose.",
        "langgraph": "LangGraph: study StateGraph, state design, nodes, edges, conditional routing, memory, and checkpointing.",
        "fastapi": "FastAPI: study routes, dependency injection, middleware, Pydantic schemas, exception handling, and async services.",
    }

    def generate_learning_plan(self, missing_skills: list[str]) -> list[str]:
        if not missing_skills:
            return ["Review the target JD again and turn weak project experience into measurable resume bullets."]

        learning_plan: list[str] = []
        for skill in missing_skills:
            normalized_skill = skill.strip().lower()
            learning_plan.append(
                self._SKILL_PLANS.get(
                    normalized_skill,
                    (
                        f"{skill}: study core concepts, build a small hands-on project, "
                        "document trade-offs, and add measurable outcomes to the resume."
                    ),
                )
            )

        return learning_plan

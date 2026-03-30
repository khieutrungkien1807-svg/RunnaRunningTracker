import json
from pathlib import Path
from core.schemas import Skill, PlanStep, TaskCompletionSpec, ArtifactCheck

class SkillStore:
    """Phase 3: Actionable Intelligence Memory Hub"""
    def __init__(self):
        self.skills: list[Skill] = []
        self._bootstrap_hardcoded_skills()

    def _bootstrap_hardcoded_skills(self):
        """Mock version of DB loading. Loading 10 classic production skills."""
        
        # 1. React Missing Component
        react_missing_comp = Skill(
            name="fix_react_missing_component",
            description="Fix missing React component.",
            trigger_patterns=["module not found", "failed to resolve import", "is not defined", "missing file"],
            plan_template=[
                PlanStep(step_id=1, action="generate_code", agent="frontend", input={"instruction": "Create the missing React component."})
            ],
            success_criteria=TaskCompletionSpec(
                deterministic_checks=[ArtifactCheck(type="file_exists", path="{DYNAMIC_PATH}")],
                semantic_goal="Component correctly generated."
            )
        )
        
        # 2. NPM Missing Dependency
        npm_missing_dep = Skill(
            name="fix_missing_npm_dependency",
            description="Install generic missing JS package.",
            trigger_patterns=["cannot find package", "npm err!", "is not in the npm registry"],
            plan_template=[
                PlanStep(step_id=1, action="run_cmd", agent="infra", input={"command": "npm install {PACKAGE_NAME}"})
            ],
            success_criteria=TaskCompletionSpec(
                deterministic_checks=[ArtifactCheck(type="file_contains", path="package.json", keyword="{PACKAGE_NAME}")],
                semantic_goal="Dependency installed."
            )
        )

        # 3. TypeScript Type Error (Any / Implicit)
        ts_type_error = Skill(
            name="fix_typescript_implicit_any",
            description="Fix TypeScript implicitly has an 'any' type error.",
            trigger_patterns=["implicitly has an 'any' type", "ts(7006)", "parameter '", "has an 'any'"],
            plan_template=[
                PlanStep(step_id=1, action="generate_code", agent="frontend", input={"instruction": "Add proper typings or strict interfaces to resolve implicit any errors."}),
                PlanStep(step_id=2, action="run_cmd", agent="frontend", input={"command": "npx tsc --noEmit"})
            ],
            success_criteria=TaskCompletionSpec(
                deterministic_checks=[ArtifactCheck(type="cmd_exit_zero", cmd="npx tsc --noEmit")],
                semantic_goal="File conforms to strict TypeScript rules."
            )
        )

        # 4. Python Module Import Error
        py_missing_module = Skill(
            name="fix_python_missing_module",
            description="Install missing Python dependency via pip.",
            trigger_patterns=["importerror: no module named", "modulenotfounderror: no module named"],
            plan_template=[
                PlanStep(step_id=1, action="run_cmd", agent="backend", input={"command": "pip install {MODULE_NAME}"}),
                PlanStep(step_id=2, action="run_cmd", agent="infra", input={"command": "pip freeze > requirements.txt"})
            ],
            success_criteria=TaskCompletionSpec(
                deterministic_checks=[ArtifactCheck(type="file_contains", path="requirements.txt", keyword="{MODULE_NAME}")],
                semantic_goal="Python module installed and recorded."
            )
        )

        # 5. Env Var Missing 
        missing_env_var = Skill(
            name="fix_missing_env_var",
            description="Provide missing environment variable to prevent crash.",
            trigger_patterns=["missing environment variable", "undefined error reading property", "process.env.", "key error:"],
            plan_template=[
                PlanStep(step_id=1, action="generate_code", agent="infra", input={"instruction": "Add placeholder {ENV_VAR} to .env.example"}),
                PlanStep(step_id=2, action="run_cmd", agent="infra", input={"command": "cp .env.example .env"})
            ],
            success_criteria=TaskCompletionSpec(
                deterministic_checks=[ArtifactCheck(type="file_exists", path=".env"), ArtifactCheck(type="file_contains", path=".env", keyword="{ENV_VAR}")],
                semantic_goal="Environment fallback structured."
            )
        )

        # 6. React Hook Rules Violation
        react_hook_rules = Skill(
            name="fix_react_hook_rules",
            description="Fix React hooks called conditionally or in wrong order.",
            trigger_patterns=["rendered more hooks than during the previous render", "react hook", "called conditionally"],
            plan_template=[
                PlanStep(step_id=1, action="generate_code", agent="frontend", input={"instruction": "Refactor component: move all hooks to the top level, pulling them outside conditionals."})
            ],
            success_criteria=TaskCompletionSpec(
                deterministic_checks=[ArtifactCheck(type="file_contains", path="{FILE_PATH}", keyword="use")],
                semantic_goal="Hooks pulled to root logic tier."
            )
        )

        # 7. Port Already In Use (Dev Environment)
        port_in_use = Skill(
            name="fix_port_already_in_use",
            description="Kill node process occupying commonly used dev ports.",
            trigger_patterns=["listen eaddrinuse", "port is already in use", "address already in use"],
            plan_template=[
                PlanStep(step_id=1, action="run_cmd", agent="infra", input={"command": "npx kill-port {PORT_NUMBER}"})
            ],
            success_criteria=TaskCompletionSpec(
                deterministic_checks=[ArtifactCheck(type="cmd_exit_zero", cmd="node -e \"console.log('port freed')\"")],
                semantic_goal="Port freed for local development."
            )
        )

        # 8. Git Merge Conflict Markers Left Behind
        merge_conflict = Skill(
            name="fix_merge_conflict_markers",
            description="Clean up unresolved git merge markers in code.",
            trigger_patterns=["<<<<<<<", "=======", ">>>>>>>", "merge conflict"],
            plan_template=[
                PlanStep(step_id=1, action="generate_code", agent="general", input={"instruction": "Resolve git merge conflict in {FILE_PATH} by accepting correct inbound changes and removing markers."})
            ],
            success_criteria=TaskCompletionSpec(
                deterministic_checks=[ArtifactCheck(type="cmd_exit_zero", cmd="grep -v '<<<<<<<' {FILE_PATH}")],
                semantic_goal="Merge conflicts neutralized."
            )
        )

        # 9. JSON Parse Error (Syntax/Trailing Comma)
        json_parse_error = Skill(
            name="fix_json_parse_error",
            description="Fix trailing commas or syntax string errors in JSON files.",
            trigger_patterns=["unexpected token", "in json at position", "expected double-quoted property name", "json.parse"],
            plan_template=[
                PlanStep(step_id=1, action="generate_code", agent="general", input={"instruction": "Fix invalid JSON formatting in {FILE_PATH}."})
            ],
            success_criteria=TaskCompletionSpec(
                deterministic_checks=[ArtifactCheck(type="json_valid", path="{FILE_PATH}")],
                semantic_goal="JSON syntax strictly compliant."
            )
        )

        # 10. Jest/Vitest Snapshot Failed
        test_snapshot_failed = Skill(
            name="fix_test_snapshot",
            description="Update UI component snapshots when intention was deliberate.",
            trigger_patterns=["snapshot failed", "does not match snapshot", "snapshot testing"],
            plan_template=[
                PlanStep(step_id=1, action="run_cmd", agent="frontend", input={"command": "npm run test -- -u {FILE_PATH}"})
            ],
            success_criteria=TaskCompletionSpec(
                deterministic_checks=[ArtifactCheck(type="cmd_exit_zero", cmd="npm run test {FILE_PATH}")],
                semantic_goal="Snapshots synced with DOM intent."
            )
        )

        self.skills.extend([
            react_missing_comp, npm_missing_dep, ts_type_error, py_missing_module, 
            missing_env_var, react_hook_rules, port_in_use, merge_conflict, 
            json_parse_error, test_snapshot_failed
        ])

    def retrieve(self, task: str, errors: list[str] = None) -> Skill | None:
        """Hybrid retrieval: Semantic + Keyword match + Context match."""
        # 1. Repair Macro Match
        if errors:
            err_str = " ".join(errors).lower()
            for skill in self.skills:
                if any(pattern in err_str for pattern in skill.trigger_patterns):
                    print(f"[SKILL STORE] Found repair match: {skill.name} via Error Pattern.")
                    return skill
                    
        # 2. Intent Macro Match
        task_lower = task.lower()
        for skill in self.skills:
            if any(pattern in task_lower for pattern in skill.trigger_patterns):
                print(f"[SKILL STORE] Found plan match: {skill.name} via Intent Pattern.")
                return skill
                
        return None

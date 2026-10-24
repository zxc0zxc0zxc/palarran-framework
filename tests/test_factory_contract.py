"""Independent black-box acceptance for the frozen factory workflow v1 contract."""

import copy
import math
import sys
import unittest

from orchestrator.spec import validate


def workflow():
    return {
        "version": 1,
        "name": "contract-smoke",
        "plan_revision": "v001",
        "limits": {
            "run_seconds": 30,
            "task_seconds": 5,
            "lease_seconds": 3,
            "max_attempts": 2,
            "output_bytes": 1024,
        },
        "policy": {
            "executables": [sys.executable],
            "adapters": ["command"],
            "env": [],
        },
        "tasks": [{
            "id": "build",
            "argv": [sys.executable, "-c", "print('ok')"],
            "verify": [[sys.executable, "-c", "assert 1 + 1 == 2"]],
        }],
    }


class FactoryContractTests(unittest.TestCase):
    def reject(self, value):
        original = copy.deepcopy(value)
        with self.assertRaises(ValueError):
            validate(value)
        self.assertEqual(value, original, "Rejection must not mutate caller data")

    def test_valid_smoke_normalizes_optional_fields(self):
        value = workflow()
        normalized = validate(value)
        self.assertEqual(normalized["tasks"][0]["adapter"], "command")
        self.assertEqual(normalized["tasks"][0]["depends_on"], [])
        self.assertIs(normalized["tasks"][0]["replay_safe"], False)
        self.assertNotIn("adapter", value["tasks"][0])

    def test_valid_explicit_values_and_dag(self):
        value = workflow()
        task = value["tasks"][0]
        task.update(adapter="command", depends_on=[], replay_safe=True)
        next_task = copy.deepcopy(task)
        next_task.update(id="test", depends_on=["build"])
        value["tasks"].append(next_task)
        result = validate(value)
        self.assertEqual(result, value)

    def test_returns_deep_copy(self):
        value = workflow()
        original = copy.deepcopy(value)
        result = validate(value)
        result["limits"]["task_seconds"] = 1
        result["tasks"][0]["argv"].append("changed")
        result["policy"]["env"].append("PATH")
        self.assertEqual(value, original)

    def test_unknown_fields_at_every_object_level(self):
        for location in ("root", "limits", "policy", "task"):
            with self.subTest(location=location):
                value = workflow()
                objects = {"root": value, "limits": value["limits"],
                           "policy": value["policy"], "task": value["tasks"][0]}
                objects[location]["unsupported"] = True
                self.reject(value)

    def test_missing_required_root_fields(self):
        for key in workflow():
            with self.subTest(key=key):
                value = workflow()
                del value[key]
                self.reject(value)

    def test_root_requires_object(self):
        for value in (None, [], "workflow", 1):
            with self.subTest(value=value):
                self.reject(value)

    def test_nested_container_types(self):
        for key in ("limits", "policy", "tasks"):
            for malformed in (None, "invalid", 7):
                value = workflow()
                value[key] = malformed
                with self.subTest(key=key, malformed=malformed):
                    self.reject(value)
        for malformed_task in (None, [], "task", 1):
            value = workflow()
            value["tasks"] = [malformed_task]
            with self.subTest(malformed_task=malformed_task):
                self.reject(value)

    def test_task_required_fields(self):
        for key in ("id", "argv", "verify"):
            value = workflow()
            del value["tasks"][0][key]
            with self.subTest(key=key):
                self.reject(value)

    def test_version_requires_integer_one(self):
        for version in (True, False, 0, 2, "1", None):
            with self.subTest(version=version):
                value = workflow()
                value["version"] = version
                self.reject(value)

    def test_identifiers_format_and_reserved_task(self):
        for key in ("name", "plan_revision", "id"):
            for identifier in ("", "has space", "../escape", "a" * 65, 123, None):
                with self.subTest(key=key, identifier=identifier):
                    value = workflow()
                    container = value["tasks"][0] if key == "id" else value
                    container[key] = identifier
                    self.reject(value)
        value = workflow()
        value["tasks"][0]["id"] = "__final__"
        self.reject(value)

    def test_task_count_bounds(self):
        for count in (0, 101):
            value = workflow()
            template = value["tasks"][0]
            value["tasks"] = [dict(copy.deepcopy(template), id="task_%s" % n)
                              for n in range(count)]
            with self.subTest(count=count):
                self.reject(value)

    def test_one_hundred_tasks_are_allowed(self):
        value = workflow()
        template = value["tasks"][0]
        value["tasks"] = [dict(copy.deepcopy(template), id="task_%s" % n)
                          for n in range(100)]
        self.assertEqual(len(validate(value)["tasks"]), 100)

    def test_duplicate_task_ids(self):
        value = workflow()
        value["tasks"].append(copy.deepcopy(value["tasks"][0]))
        self.reject(value)

    def test_missing_duplicate_and_self_dependencies(self):
        for dependencies in (["missing"], ["build"], ["missing", "missing"]):
            value = workflow()
            value["tasks"][0]["depends_on"] = dependencies
            with self.subTest(dependencies=dependencies):
                self.reject(value)
        value = workflow()
        value["tasks"].append(dict(copy.deepcopy(value["tasks"][0]),
                                   id="second", depends_on=["build", "build"]))
        self.reject(value)

    def test_dependency_cycle(self):
        value = workflow()
        task = value["tasks"][0]
        task["depends_on"] = ["second"]
        value["tasks"].append(dict(copy.deepcopy(task), id="second", depends_on=["build"]))
        self.reject(value)

    def test_dependency_list_types(self):
        for dependencies in ("build", None, [1], [None], [[]]):
            value = workflow()
            value["tasks"][0]["depends_on"] = dependencies
            with self.subTest(dependencies=dependencies):
                self.reject(value)

    def test_limits_reject_non_numbers_bool_and_nonfinite(self):
        for key in workflow()["limits"]:
            for limit in (True, False, None, "10", [], math.nan, math.inf, -math.inf):
                value = workflow()
                value["limits"][key] = limit
                with self.subTest(key=key, limit=limit):
                    self.reject(value)

    def test_limits_bounds(self):
        invalid = {
            "run_seconds": [0, -1, 86401],
            "task_seconds": [0, -1, 3601],
            "lease_seconds": [0, 2.99, 301],
            "max_attempts": [0, -1, 11, 1.5],
            "output_bytes": [0, 1023, 10485761, 1024.5],
        }
        for key, limits in invalid.items():
            for limit in limits:
                value = workflow()
                value["limits"][key] = limit
                with self.subTest(key=key, limit=limit):
                    self.reject(value)

    def test_limits_inclusive_upper_bounds(self):
        value = workflow()
        value["limits"].update(run_seconds=86400, task_seconds=3600,
                               lease_seconds=300, max_attempts=10,
                               output_bytes=10485760)
        self.assertEqual(validate(value)["limits"], value["limits"])

    def test_all_limits_are_required(self):
        for key in workflow()["limits"]:
            value = workflow()
            del value["limits"][key]
            with self.subTest(key=key):
                self.reject(value)

    def test_policy_list_types_empty_and_duplicates(self):
        for key in ("executables", "adapters", "env"):
            for item in (None, "command", [1], [[]]):
                value = workflow()
                value["policy"][key] = item
                with self.subTest(key=key, item=item):
                    self.reject(value)
            value = workflow()
            entry = {"executables": sys.executable, "adapters": "command", "env": "HOME"}[key]
            value["policy"][key] = [entry, entry]
            self.reject(value)
        for key in ("executables", "adapters"):
            value = workflow()
            value["policy"][key] = []
            self.reject(value)

    def test_policy_requires_all_fields(self):
        for key in workflow()["policy"]:
            value = workflow()
            del value["policy"][key]
            self.reject(value)

    def test_invalid_environment_variable_names(self):
        for name in ("", "A=B", "HAS SPACE", "1START", "A\x00B", "../HOME"):
            value = workflow()
            value["policy"]["env"] = [name]
            with self.subTest(name=name):
                self.reject(value)

    def test_valid_environment_variable_names(self):
        value = workflow()
        value["policy"]["env"] = ["PATH", "HOME", "_CONFIG", "a_1"]
        self.assertEqual(validate(value)["policy"]["env"], value["policy"]["env"])

    def test_absolute_executable_and_no_nul(self):
        for executable in ("python3", "./python3", "", "/bin/py\x00thon"):
            value = workflow()
            value["policy"]["executables"] = [executable]
            value["tasks"][0]["argv"][0] = executable
            value["tasks"][0]["verify"][0][0] = executable
            with self.subTest(executable=executable):
                self.reject(value)

    def test_executable_existence_is_not_admission_requirement(self):
        value = workflow()
        future_executable = "/opt/factory-contract-test/nonexistent-runner"
        value["policy"]["executables"].append(future_executable)
        value["tasks"][0]["argv"][0] = future_executable
        self.assertEqual(validate(value)["tasks"][0]["argv"][0], future_executable)

    def test_unallowlisted_execution_and_verification(self):
        for field in ("argv", "verify"):
            value = workflow()
            command = value["tasks"][0][field]
            if field == "verify":
                command = command[0]
            command[0] = "/opt/not-allowed"
            with self.subTest(field=field):
                self.reject(value)

    def test_empty_and_invalid_argv(self):
        for argv in ([], None, "echo ok", [1], [sys.executable, 1], [sys.executable, "bad\x00arg"]):
            value = workflow()
            value["tasks"][0]["argv"] = argv
            with self.subTest(argv=argv):
                self.reject(value)

    def test_empty_and_invalid_verify(self):
        for verify in ([], None, "test", [[]], [[sys.executable, 1]], [["relative"]]):
            value = workflow()
            value["tasks"][0]["verify"] = verify
            with self.subTest(verify=verify):
                self.reject(value)

    def test_command_rejects_ai_fields(self):
        for field, content in (("prompt", "Implement feature"), ("executable", sys.executable)):
            value = workflow()
            value["tasks"][0][field] = content
            with self.subTest(field=field):
                self.reject(value)

    def test_replay_safe_requires_boolean(self):
        for replay_safe in (0, 1, None, "true", []):
            value = workflow()
            value["tasks"][0]["replay_safe"] = replay_safe
            with self.subTest(replay_safe=replay_safe):
                self.reject(value)

    def test_adapters_must_be_known_and_allowlisted(self):
        for adapter in ("unknown", "claude", True, None):
            value = workflow()
            value["tasks"][0]["adapter"] = adapter
            with self.subTest(adapter=adapter):
                self.reject(value)
        value = workflow()
        value["policy"]["adapters"].append("unknown")
        self.reject(value)

    def ai_workflow(self, adapter):
        value = workflow()
        value["policy"]["adapters"].append(adapter)
        task = value["tasks"][0]
        del task["argv"]
        task.update(adapter=adapter, executable=sys.executable,
                    prompt="Read /skills/palarran-backend-build/SKILL.md and mandatory docs; "
                    "implement target plan revision v001 and DoD; "
                    "read target .palarran/ decision memory; "
                    "exit failure on any unresolved question.")
        return value

    def test_supported_ai_adapters(self):
        for adapter in ("codex", "claude"):
            with self.subTest(adapter=adapter):
                value = self.ai_workflow(adapter)
                self.assertEqual(validate(value)["tasks"][0]["adapter"], adapter)

    def test_ai_requires_prompt_and_executable_and_no_command_argv(self):
        for adapter in ("codex", "claude"):
            for missing in ("prompt", "executable"):
                value = self.ai_workflow(adapter)
                del value["tasks"][0][missing]
                with self.subTest(adapter=adapter, missing=missing):
                    self.reject(value)
            value = self.ai_workflow(adapter)
            value["tasks"][0]["argv"] = [sys.executable]
            self.reject(value)

    def test_ai_rejects_invalid_prompt_and_executable(self):
        for field, bad_values in (("prompt", ["", None, 1, "bad\x00prompt"]),
                                  ("executable", ["codex", "/opt/not-allowed", None])):
            for bad_value in bad_values:
                value = self.ai_workflow("codex")
                value["tasks"][0][field] = bad_value
                with self.subTest(field=field, bad_value=bad_value):
                    self.reject(value)


if __name__ == "__main__":
    unittest.main()

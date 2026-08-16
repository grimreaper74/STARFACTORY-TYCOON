"""Pure-Python contract tests for the unexecuted One Factory shell tooling."""

from __future__ import annotations

import sys
from pathlib import Path
import types
import unittest


PROJECT = Path(__file__).resolve().parents[2]
SCRIPTS = PROJECT / "Scripts"


def load_static_module(filename: str, name: str):
    fake_unreal = types.ModuleType("unreal")

    class Paths:
        @staticmethod
        def project_dir() -> str:
            return str(PROJECT) + "\\"

    fake_unreal.Paths = Paths
    previous = sys.modules.get("unreal")
    sys.modules["unreal"] = fake_unreal
    try:
        namespace = {
            "__name__": name,
            "__file__": str(SCRIPTS / filename),
            "__package__": None,
        }
        source = (SCRIPTS / filename).read_text(encoding="utf-8")
        exec(compile(source, str(SCRIPTS / filename), "exec"), namespace)
        return types.SimpleNamespace(**namespace)
    finally:
        if previous is None:
            sys.modules.pop("unreal", None)
        else:
            sys.modules["unreal"] = previous


class OneFactoryShellContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_static_module(
            "create_one_factory_shell_v001.py", "one_factory_builder_static"
        )
        cls.validator = load_static_module(
            "validate_one_factory_shell_v001.py", "one_factory_validator_static"
        )

    def test_exact_destination_and_native_class_paths(self):
        expected_map = (
            "/Game/LineBoss/Factory/OneFactory/v001/Maps/"
            "LB_MoorcrossWorks_OneFactory_v001"
        )
        self.assertEqual(self.builder.MAP, expected_map)
        self.assertEqual(self.validator.MAP, expected_map)
        self.assertEqual(
            self.builder.GAME_MODE_CLASS_PATH,
            "/Script/LineBossCarFactory.LBOneFactoryGameMode",
        )
        self.assertEqual(
            self.builder.BOOTSTRAP_CLASS_PATH,
            "/Script/LineBossCarFactory.LBOneFactoryBootstrap",
        )
        self.assertEqual(
            self.builder.PRESS_AUTHORITY_CLASS_PATH,
            "/Script/LineBossCarFactory.LBPressShopBuildAuthority",
        )

    def test_exact_factory_envelope_and_grid(self):
        for module in (self.builder, self.validator):
            self.assertEqual(module.FACTORY_CENTRE_CM, (0.0, 0.0, 1500.0))
            self.assertEqual(module.FACTORY_SIZE_CM, (62000.0, 31000.0, 3000.0))
            self.assertEqual(module.GRID_SIZE_CM, 100.0)

    def test_authority_arrays_are_exact_and_ordered(self):
        self.assertEqual(self.builder.BUILD_BAYS, self.validator.BUILD_BAYS)
        self.assertEqual(self.builder.PROTECTED_AREAS, self.validator.PROTECTED_AREAS)
        self.assertEqual(self.builder.UTILITY_SPINES, self.validator.UTILITY_SPINES)
        self.assertEqual(self.builder.LOGISTICS_SPINES, self.validator.LOGISTICS_SPINES)
        self.assertEqual(
            [row["id"] for row in self.builder.BUILD_BAYS],
            [
                "OF_BAY_PRESS_01",
                "OF_BAY_BODY_01",
                "OF_BAY_PAINT_01",
                "OF_BAY_ASSEMBLY_01",
            ],
        )
        self.assertEqual(
            [row["id"] for row in self.builder.PROTECTED_AREAS],
            ["OF_SPINE_LOGISTICS_EW_01", "OF_SPINE_SERVICE_EW_01"],
        )
        self.assertEqual(len(self.builder.UTILITY_SPINES), 1)
        self.assertEqual(len(self.builder.LOGISTICS_SPINES), 1)
        self.assertEqual(
            self.builder.UTILITY_SPINES[0]["maximum_connection_distance_cm"],
            30000.0,
        )

    def test_hism_instance_layout_is_independently_duplicated(self):
        builder_rows = self.builder.expected_hism_instances()
        validator_rows = self.validator.expected_hism_instances()
        self.assertEqual(builder_rows, validator_rows)
        counts = {label: len(rows) for label, rows in builder_rows.items()}
        self.assertEqual(
            counts,
            {
                "LB_OF_ENV_HISM_FloorSlabs_v001": 200,
                "LB_OF_ENV_HISM_CutawayWalls_v001": 3,
                "LB_OF_ENV_HISM_Columns_v001": 22,
                "LB_OF_ENV_HISM_OpenRoofFrame_v001": 13,
                "LB_OF_ENV_HISM_Grid100cm_v001": 932,
                "LB_OF_ENV_HISM_SafetyLines_v001": 20,
                "LB_OF_ENV_HISM_DepartmentFloor_Press_v001": 1,
                "LB_OF_ENV_HISM_DepartmentFloor_Body_v001": 1,
                "LB_OF_ENV_HISM_DepartmentFloor_Paint_v001": 1,
                "LB_OF_ENV_HISM_DepartmentFloor_Assembly_v001": 1,
            },
        )
        self.assertEqual(sum(counts.values()), 1194)
        self.assertEqual(len(counts), 10)

    def test_validator_freezes_exact_actor_cardinality(self):
        self.assertEqual(self.validator.EXPECTED_NONFOUNDATION_ACTOR_COUNT, 26)
        self.assertEqual(self.validator.EXPECTED_MAP_AUTHORED_ACTOR_COUNT, 25)
        self.assertEqual(len(self.validator.EXPECTED_ACTORS), 26)
        self.assertEqual(
            self.validator.EXPECTED_ACTORS["RecastNavMesh-Default"],
            {
                "class": "/Script/NavigationSystem.RecastNavMesh",
                "location": (0.0, 0.0, 0.0),
                "rotation": (0.0, 0.0, 0.0),
                "scale": (1.0, 1.0, 1.0),
                "tags": (),
            },
        )
        self.assertEqual(
            self.validator.EXPECTED_ACTORS["LB_OneFactoryBootstrap_v001"]["tags"],
            tuple(sorted(("LB.OneFactory.Bootstrap.v001", "LB.Provenance.NativeOnly"))),
        )
        self.assertEqual(
            self.validator.EXPECTED_ACTORS[
                "LB_OneFactory_PressBuildAuthority_v001"
            ]["class"],
            "/Script/LineBossCarFactory.LBPressShopBuildAuthority",
        )
        self.assertEqual(
            self.validator.EXPECTED_ACTORS[
                "LB_OneFactory_PressBuildAuthority_v001"
            ]["tags"],
            tuple(sorted((
                "LB.OneFactory.MapAuthored.PressBuildAuthority.v001",
                "LB.Provenance.NativeOnly",
            ))),
        )

    def test_shell_has_no_production_actor_spec(self):
        allowed_project_classes = {
            "/Script/LineBossCarFactory.LBOneFactoryBootstrap",
            "/Script/LineBossCarFactory.LBPressShopBuildAuthority",
        }
        project_classes = {
            row["class"]
            for row in self.validator.EXPECTED_ACTORS.values()
            if row["class"].startswith("/Script/LineBossCarFactory.")
        }
        self.assertEqual(project_classes, allowed_project_classes)
        forbidden = ("wip", "machine", "station", "robot", "cellactor")
        for label, row in self.validator.EXPECTED_ACTORS.items():
            identity = " ".join((label, *row["tags"])).lower()
            self.assertFalse(any(term in identity for term in forbidden), identity)

    def test_single_lighting_and_fixed_exposure_authorities(self):
        specs = self.validator.EXPECTED_ACTORS
        lighting = [
            label for label, row in specs.items()
            if "LB.OneFactory.Lighting.Authority.5000K.v001" in row["tags"]
        ]
        exposure = [
            label for label, row in specs.items()
            if "LB.OneFactory.Lighting.FixedExposure.v001" in row["tags"]
        ]
        self.assertEqual(lighting, ["LB_OF_ENV_LightingAuthority_5000K_v001"])
        self.assertEqual(exposure, ["LB_OF_ENV_FixedExposureAuthority_v001"])


if __name__ == "__main__":
    unittest.main()

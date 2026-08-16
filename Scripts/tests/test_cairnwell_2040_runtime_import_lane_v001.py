from __future__ import annotations

import ast
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = ROOT / "Scripts"
DOC = ROOT / "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_UNREAL_IMPORT_LANE.md"
CONTRACT_PREPARER = SCRIPTS / "prepare_cairnwell_2040_runtime_v001_contract.py"
BASELINE_PREPARER = SCRIPTS / "prepare_cairnwell_2040_runtime_v001_baseline.py"
RUNTIME = SCRIPTS / "cairnwell_2040_runtime_v001.py"
IMPORTER = SCRIPTS / "import_cairnwell_2040_runtime_v001.py"
VALIDATOR = SCRIPTS / "validate_cairnwell_2040_runtime_fresh_process_v001.py"
RUNNER = SCRIPTS / "run_cairnwell_2040_runtime_import_lane_v001.ps1"
V002_RECOVERY_PREPARER = SCRIPTS / "prepare_cairnwell_2040_runtime_v001_recovery_v002.py"
V002_RECOVERY_DOC = ROOT / "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V002.md"
V002_RECOVERY_CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v002_contract.json"
V002_RECOVERY_CONTRACT_SHA = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v002_contract.sha256"
RECOVERY_PREPARER = SCRIPTS / "prepare_cairnwell_2040_runtime_v001_recovery_v003.py"
RECOVERY_DOC = ROOT / "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V003.md"
RECOVERY_CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v003_contract.json"
RECOVERY_CONTRACT_SHA = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v003_contract.sha256"
LOG_RETRY_HELPER = SCRIPTS / "cairnwell_2040_runtime_log_retry_v003.ps1"
V004_RECOVERY_PREPARER = SCRIPTS / "prepare_cairnwell_2040_runtime_v001_recovery_v004.py"
V004_RECOVERY_DOC = ROOT / "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V004.md"
V004_RECOVERY_CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v004_contract.json"
V004_RECOVERY_CONTRACT_SHA = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v004_contract.sha256"
V005_RECOVERY_PREPARER = SCRIPTS / "prepare_cairnwell_2040_runtime_v001_recovery_v005.py"
V005_RECOVERY_DOC = ROOT / "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V005.md"
V005_RECOVERY_CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v005_contract.json"
V005_RECOVERY_CONTRACT_SHA = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v005_contract.sha256"
V006_RECOVERY_PREPARER = SCRIPTS / "prepare_cairnwell_2040_runtime_v001_recovery_v006.py"
V006_RECOVERY_DOC = ROOT / "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V006.md"
V006_RECOVERY_CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v006_contract.json"
V006_RECOVERY_CONTRACT_SHA = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v006_contract.sha256"
V007_RECOVERY_PREPARER = SCRIPTS / "prepare_cairnwell_2040_runtime_v001_recovery_v007.py"
V007_RECOVERY_DOC = ROOT / "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V007.md"
V007_RECOVERY_CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v007_contract.json"
V007_RECOVERY_CONTRACT_SHA = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v007_contract.sha256"
V008_RECOVERY_PREPARER = SCRIPTS / "prepare_cairnwell_2040_runtime_v001_recovery_v008.py"
V008_RECOVERY_DOC = ROOT / "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V008.md"
V008_RECOVERY_CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v008_contract.json"
V008_RECOVERY_CONTRACT_SHA = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v008_contract.sha256"
V009_RECOVERY_PREPARER = SCRIPTS / "prepare_cairnwell_2040_runtime_v001_recovery_v009.py"
V009_RECOVERY_DOC = ROOT / "Docs/OneFactory/CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009.md"
V009_RECOVERY_CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v009_contract.json"
V009_RECOVERY_CONTRACT_SHA = SCRIPTS / "cairnwell_2040_runtime_v001_recovery_v009_contract.sha256"
CONTRACT = SCRIPTS / "cairnwell_2040_runtime_v001_import_contract.json"
CONTRACT_SHA = SCRIPTS / "cairnwell_2040_runtime_v001_import_contract.sha256"
BASELINE = SCRIPTS / "cairnwell_2040_runtime_v001_import_baseline.json"
BASELINE_SHA = SCRIPTS / "cairnwell_2040_runtime_v001_import_baseline.sha256"
DEST = ROOT / "Content/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001"
AUDIT_ROOT = ROOT / "Saved/Audits/OneFactory/Vehicles/Cairnwell2040Runtime_v001/UnrealImportLane_v001"
FAILED_RUN = AUDIT_ROOT / "20260815T094919Z-7dfb3c0a"
V002_FAILED_RUN = AUDIT_ROOT / "Recovery_v002/20260815T103132Z-3fc39714"
V003_FAILED_RUN = AUDIT_ROOT / "Recovery_v003/20260815T105958Z-79a98abc"
RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v003"
V004_RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v004"
V004_FAILED_RUN = V004_RECOVERY_AUDIT_ROOT / "20260815T112446Z-4e34bb5c"
V005_RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v005"
V005_FAILED_RUN = V005_RECOVERY_AUDIT_ROOT / "20260815T115847Z-92ea69dd"
V006_RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v006"
V006_FAILED_RUN = V006_RECOVERY_AUDIT_ROOT / "20260815T124823Z-67c989ee"
V007_RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v007"
V008_RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v008"
V009_RECOVERY_AUDIT_ROOT = AUDIT_ROOT / "Recovery_v009"
V001_QUARANTINE = ROOT / (
    "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T094919Z-7dfb3c0a_v001"
)
QUARANTINE = ROOT / (
    "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T103132Z-3fc39714_v002"
)
V003_QUARANTINE = ROOT / (
    "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T105958Z-79a98abc_v003"
)
V004_QUARANTINE = ROOT / (
    "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T112446Z-4e34bb5c_v004"
)
V005_QUARANTINE = ROOT / (
    "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T115847Z-92ea69dd_v005"
)
V006_QUARANTINE = ROOT / (
    "Saved/Quarantine/OneFactory/Vehicles/Cairnwell2040Runtime_v001/"
    "Incident_20260815T124823Z-67c989ee_v006"
)

EXPECTED_NAMESPACE = "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001"
EXPECTED_ROLES = {
    "BIW_AutomotiveSkeleton",
    "BIW_UnderbodySubset",
    "EmeraldBodyVisualAuthority",
    "EmeraldRollingGearVisualAuthority",
}
EXPECTED_TEXTURE_SEMANTICS = {"base_color", "metallic_roughness", "normal"}


def literal_assignment(source: str, name: str):
    """Read a top-level literal without importing an Unreal-aware module."""
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return ast.literal_eval(node.value)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == name:
                return ast.literal_eval(node.value)
    raise AssertionError(f"top-level literal assignment not found: {name}")


def write_text_receivers(source: str) -> list[str]:
    receivers = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "write_text":
            continue
        value = node.func.value
        receivers.append(value.id if isinstance(value, ast.Name) else ast.unparse(value))
    return receivers


class Cairnwell2040RuntimeImportLaneV001StaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = DOC.read_text(encoding="utf-8")
        cls.contract_preparer = CONTRACT_PREPARER.read_text(encoding="utf-8")
        cls.baseline_preparer = BASELINE_PREPARER.read_text(encoding="utf-8")
        cls.recovery_preparer = RECOVERY_PREPARER.read_text(encoding="utf-8")
        cls.recovery_doc = RECOVERY_DOC.read_text(encoding="utf-8")
        cls.log_retry_helper = LOG_RETRY_HELPER.read_text(encoding="utf-8")
        cls.v004_recovery_preparer = V004_RECOVERY_PREPARER.read_text(encoding="utf-8")
        cls.v004_recovery_doc = V004_RECOVERY_DOC.read_text(encoding="utf-8")
        cls.v005_recovery_preparer = V005_RECOVERY_PREPARER.read_text(encoding="utf-8")
        cls.v005_recovery_doc = V005_RECOVERY_DOC.read_text(encoding="utf-8")
        cls.v006_recovery_preparer = V006_RECOVERY_PREPARER.read_text(encoding="utf-8")
        cls.v006_recovery_doc = V006_RECOVERY_DOC.read_text(encoding="utf-8")
        cls.v007_recovery_preparer = V007_RECOVERY_PREPARER.read_text(encoding="utf-8")
        cls.v007_recovery_doc = V007_RECOVERY_DOC.read_text(encoding="utf-8")
        cls.v008_recovery_preparer = V008_RECOVERY_PREPARER.read_text(encoding="utf-8")
        cls.v008_recovery_doc = V008_RECOVERY_DOC.read_text(encoding="utf-8")
        cls.v009_recovery_preparer = V009_RECOVERY_PREPARER.read_text(encoding="utf-8")
        cls.v009_recovery_doc = V009_RECOVERY_DOC.read_text(encoding="utf-8")
        cls.runtime = RUNTIME.read_text(encoding="utf-8")

    def test_chained_v001_through_v006_failure_state_and_v007_stale_pair_are_coherent(self) -> None:
        authority_exists = [
            path.exists() for path in (CONTRACT, CONTRACT_SHA, BASELINE, BASELINE_SHA)
        ]
        self.assertEqual(sum(authority_exists), 4, "original contract/baseline must remain frozen")
        self.assertEqual(
            hashlib.sha256(V002_RECOVERY_CONTRACT.read_bytes()).hexdigest().upper(),
            "0D0E0ADE47D80F487A8E94547133323EF1C7622C9260177A948049BC09AA85E2",
        )
        self.assertEqual(
            hashlib.sha256(RECOVERY_CONTRACT.read_bytes()).hexdigest().upper(),
            "A5ED1D53A35A7D2D58BD533691C4207AF9BF820EBC4D0E0DD0D734254D34FF22",
        )
        self.assertEqual(
            hashlib.sha256(V004_RECOVERY_CONTRACT.read_bytes()).hexdigest().upper(),
            "C52DE8F74018D03458A94946A0B1208322881F4C52E765B474B3DE56CF8052DA",
        )
        self.assertEqual(
            hashlib.sha256(V005_RECOVERY_CONTRACT.read_bytes()).hexdigest().upper(),
            "E5E9F4CF0E003C0B5936E0EED581D6E697E1C20AD0BC1B390E6FA7D3ADD2E239",
        )
        self.assertEqual(
            hashlib.sha256(V006_RECOVERY_CONTRACT.read_bytes()).hexdigest().upper(),
            "7DDEF098FF1C2D0E53756E89CC57B1A00A89C32A4A7E623686454D619F3214AD",
        )
        self.assertEqual(
            hashlib.sha256(V007_RECOVERY_CONTRACT.read_bytes()).hexdigest().upper(),
            "7271F549ADF301C078636C408B49C5998CE8882A07FB999EF730CB0B97F7698F",
        )
        self.assertEqual(V007_RECOVERY_CONTRACT.stat().st_size, 98751)
        self.assertEqual(
            hashlib.sha256(V007_RECOVERY_CONTRACT_SHA.read_bytes()).hexdigest().upper(),
            "ECC793B9319E935EC29762420421292828B7ADF7C0DBBC93022C3154298F8508",
        )
        self.assertEqual(V007_RECOVERY_CONTRACT_SHA.stat().st_size, 123)
        self.assertEqual(V008_RECOVERY_CONTRACT.stat().st_size, 133651)
        self.assertEqual(
            hashlib.sha256(V008_RECOVERY_CONTRACT.read_bytes()).hexdigest().upper(),
            "6E8E2D0E6D40A16CFF1AF5BEF31A00498C51DEADADF6CE0901D537285E5E49BD",
        )
        self.assertEqual(V008_RECOVERY_CONTRACT_SHA.stat().st_size, 123)
        self.assertEqual(
            hashlib.sha256(V008_RECOVERY_CONTRACT_SHA.read_bytes()).hexdigest().upper(),
            "D082F35B000CEC489991F8F481AACA78580CCB1326356F468612C4C99CBA054F",
        )
        v009_exists = [V009_RECOVERY_CONTRACT.exists(), V009_RECOVERY_CONTRACT_SHA.exists()]
        self.assertIn(sum(v009_exists), (0, 2), "v009 recovery contract/sidecar must be paired")
        self.assertTrue(DEST.is_dir(), "the completed v009 eleven-package namespace must remain preserved")
        partials = {
            path.relative_to(DEST).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest().upper()
            for path in DEST.rglob("*") if path.is_file()
        }
        self.assertEqual(partials, {
            "Materials/M_LB_C2040_BIWGalvanized_v001.uasset":
                "44F209BACFBED75E0C3C3652E3F339078AE54B6970D688ABD8A543DA50BDCC83",
            "Materials/M_LB_C2040_BodyPaintTintPBR_v001.uasset":
                "D029C4BA43E7608194B93B1E007664691329E9F82B51B6DE60436F334F75857B",
            "Materials/M_LB_C2040_EDCoat_v001.uasset":
                "84B78F938E698D3EE125037DC721DABC018CF73F58ADFD747C55FBCA63E98627",
            "Materials/M_LB_C2040_RollingGearPBR_v001.uasset":
                "44E75F415F57361C1478DF62249FC6FBFDBF62BC3D6EAC24C1E66CA6788782D9",
            "Meshes/SM_LB_C2040_BIW_AutomotiveSkeleton_v001.uasset":
                "C6AA022949255E303D4E94D8E7D5BD33B670CC9C21200B29B9570A026DF9719F",
            "Meshes/SM_LB_C2040_BIW_UnderbodySubset_v001.uasset":
                "0EB3CD02327F362BDC68E9C99CFA48ACF73A98C66311BAE098F01BE28EC4066E",
            "Meshes/SM_LB_C2040_EmeraldBodyVisualAuthority_v001.uasset":
                "2C10916D3B730E48E0F44E09C55AAE7E9A338982661973C6A2420EB4273139AB",
            "Meshes/SM_LB_C2040_EmeraldRollingGearVisualAuthority_v001.uasset":
                "976D4BA7DC88F6DDBBEC7785C03E27F475628CAABC1BA31303C09D791F1EF536",
            "Textures/T_LB_C2040_Emerald_BaseColor_v001.uasset":
                "4EA089DB4D393A87F81E5AFE7D58295B8C11EB9B3E11A7200FE72DF1A1449B34",
            "Textures/T_LB_C2040_Emerald_MRBodyMask_v001.uasset":
                "7A4B85525A43F021FC5CE4E45939C5A554DDA41B17934BB83B0089DB931AB07A",
            "Textures/T_LB_C2040_Emerald_Normal_v001.uasset":
                "86A280DFF0B95EF85EDA7DC39224808C8B3FDBDB84292D415D7F126915EFBC0B",
        })
        self.assertEqual(
            hashlib.sha256((FAILED_RUN / "import_failure_v001.json").read_bytes()).hexdigest().upper(),
            "05F204CDE09BD22BED823101525C82F64E18F8EE56BC6004C9E0979AA73CFC2D",
        )
        self.assertEqual(
            hashlib.sha256((V002_FAILED_RUN / "import_failure_recovery_v002.json").read_bytes()).hexdigest().upper(),
            "86AB67E0AD2C501EE8E49CFAF6061694DD78DFD616B81F22B53B80896E127EE1",
        )
        self.assertEqual(
            hashlib.sha256((V003_FAILED_RUN / "import_failure_recovery_v003.json").read_bytes()).hexdigest().upper(),
            "3FB3E1A8F27F1E4EF477C6F1E3E3AF41E53F2C8618CAC9A4E0A047F91BD60E7C",
        )
        self.assertEqual(
            hashlib.sha256((V004_FAILED_RUN / "import_failure_recovery_v004.json").read_bytes()).hexdigest().upper(),
            "D5BFCA5C8C2380587ECADDE9C64455FFD60A282D54A6FF8E27CD2E7144B494DF",
        )
        self.assertEqual(
            hashlib.sha256((V005_FAILED_RUN / "import_failure_recovery_v005.json").read_bytes()).hexdigest().upper(),
            "435D82778C83CDACAA2E59F91E04273181BA710F5D0BAFFA719A15E04A9F48BB",
        )
        self.assertEqual(
            hashlib.sha256((V006_FAILED_RUN / "import_failure_recovery_v006.json").read_bytes()).hexdigest().upper(),
            "A484FAAB8F612A0EE9FA915436B3389016D7137CB954580C499BDBBFE2A15F06",
        )
        self.assertTrue(V001_QUARANTINE.is_dir(), "v001 four-package quarantine must remain")
        self.assertTrue(QUARANTINE.is_dir(), "v002 seven-package quarantine must remain")
        self.assertTrue(RECOVERY_AUDIT_ROOT.is_dir(), "v003 failed run must remain")
        self.assertTrue(V004_RECOVERY_AUDIT_ROOT.is_dir(), "v004 failed run must remain")
        self.assertTrue(V003_QUARANTINE.is_dir(), "v003 eleven-package quarantine must remain")
        self.assertTrue(V005_RECOVERY_AUDIT_ROOT.is_dir(), "v005 failed run must remain")
        self.assertTrue(V004_QUARANTINE.is_dir(), "v004 eleven-package quarantine must remain")
        self.assertTrue(V006_RECOVERY_AUDIT_ROOT.is_dir(), "v006 failed run must remain")
        self.assertTrue(V005_QUARANTINE.is_dir(), "v005 eleven-package quarantine must remain")
        self.assertFalse(V007_RECOVERY_AUDIT_ROOT.exists(), "recovery v007 must remain unexecuted")
        self.assertFalse(V008_RECOVERY_AUDIT_ROOT.exists(), "recovery v008 must remain unexecuted")
        self.assertTrue(V009_RECOVERY_AUDIT_ROOT.is_dir(), "executed v009 evidence must remain")
        self.assertTrue(V006_QUARANTINE.is_dir(), "completed v009 q6 move must remain")

    def test_document_is_truthful_about_meshy_provenance_identity_and_counts(self) -> None:
        self.assertIn("APPROVED_V005__OFFLINE_FREEZE_AUTHORIZED__UNREAL_NOT_AUTHORIZED", self.doc)
        self.assertIn("ProductionCandidate_v005", self.doc)
        self.assertIn("ProductionCandidate_v006` was rejected", self.doc)
        self.assertIn("MANIFEST_v005.json", self.doc)
        self.assertIn("No v006 FBX, texture, mask, or manifest", self.doc)
        self.assertIn("manual paint-mask", self.doc)
        self.assertIn("false_positive_fragment_count=0", self.doc)
        self.assertIn(EXPECTED_NAMESPACE, self.doc)
        self.assertIn("Meshy-derived", self.doc)
        self.assertIn("must never describe the vehicle", self.doc)
        self.assertIn("as `Native`, clean-room, or provenance-free", self.doc)
        self.assertNotIn("/Game/LineBoss/Native/", self.doc)
        for role in EXPECTED_ROLES:
            self.assertIn(f"`{role}`", self.doc)
        for asset_name in (
            "SM_LB_C2040_BIW_AutomotiveSkeleton_v001",
            "SM_LB_C2040_BIW_UnderbodySubset_v001",
            "SM_LB_C2040_EmeraldBodyVisualAuthority_v001",
            "SM_LB_C2040_EmeraldRollingGearVisualAuthority_v001",
        ):
            self.assertIn(f"`{asset_name}`", self.doc)
        self.assertIn("frozen lane identities", self.doc)
        self.assertIn("match every name exactly or contract generation fails", self.doc)
        for semantic in EXPECTED_TEXTURE_SEMANTICS:
            self.assertIn(f"`{semantic}`", self.doc)
        self.assertIn("4 meshes + 3 textures + 4 materials = 11 packages", self.doc)
        self.assertIn("disjoint from the separate panel-module lane", self.doc)
        self.assertIn("No stamped/body panel module package", self.doc)
        for token in (
            "`textured_tint_pbr`",
            "`textured_pbr`",
            "`solid_pbr`",
            "`VehiclePaintColour`",
            "`BodyPaintMask`",
            "Lerp Alpha",
            "body-versus-rolling role separation",
            "Cairnwell2040_v005_FinalApprovalSupersession.json",
            "Cairnwell2040_v005_AdditiveFreezeReceipt_v002.json",
            "PASS__V005_ADDITIVE_FREEZE_RECEIPT_V002__CURRENT_CONTRACT_AUTHORITY__SOLE_SCHEMA_KEY_CORRECTION",
            "F7C761D794F44E7EEEBB2958A7947F63D59D0EE828510E1803D7B69EA62642F0",
            "738E19C3D1D07028C0F2C107AD023F14DBC94FD44DAE2107411D6C8A317A348C",
            "historical_marker_preserved_byte_exact=true",
            "supersedes_historical_marker_without_deletion=true",
        ):
            self.assertIn(token, self.doc)
        self.assertIn("Unreal process A", self.doc)
        self.assertIn("Unreal process B", self.doc)
        self.assertIn("This two-process boundary is mandatory", self.doc)
        self.assertIn("/Engine/Maps/Entry.Entry", self.doc)
        self.assertIn("LoadLevelAtStartup=None", self.doc)
        self.assertIn("independently re-hash all 11 packages", self.doc)

    def test_contract_preparer_pins_exact_identity_roles_lods_and_closure(self) -> None:
        self.assertEqual(literal_assignment(self.contract_preparer, "DEST"), EXPECTED_NAMESPACE)
        self.assertEqual(literal_assignment(self.contract_preparer, "EXPECTED_ROLES"), EXPECTED_ROLES)
        self.assertEqual(
            literal_assignment(self.contract_preparer, "EXPECTED_MESH_ASSET_NAMES"),
            {
                "BIW_AutomotiveSkeleton": "SM_LB_C2040_BIW_AutomotiveSkeleton_v001",
                "BIW_UnderbodySubset": "SM_LB_C2040_BIW_UnderbodySubset_v001",
                "EmeraldBodyVisualAuthority": "SM_LB_C2040_EmeraldBodyVisualAuthority_v001",
                "EmeraldRollingGearVisualAuthority":
                    "SM_LB_C2040_EmeraldRollingGearVisualAuthority_v001",
            },
        )
        self.assertEqual(
            literal_assignment(self.contract_preparer, "EXPECTED_TEXTURE_SEMANTICS"),
            EXPECTED_TEXTURE_SEMANTICS,
        )
        self.assertEqual(
            literal_assignment(self.contract_preparer, "ACK_TOKEN"),
            "FREEZE_APPROVED_CAIRNWELL_V005_UNREAL_INPUT_CONTRACT_V001",
        )
        self.assertEqual(literal_assignment(self.contract_preparer, "WINNER_VERSION"), "v005")
        self.assertEqual(
            literal_assignment(self.contract_preparer, "WINNER_CANDIDATE"),
            "ProductionCandidate_v005",
        )
        for token in (
            '[row.get("lod") for row in lods] != [0, 1, 2]',
            'set(modules_raw) != EXPECTED_ROLES',
            'set(textures_raw) != EXPECTED_TEXTURE_SEMANTICS',
            'set(materials_raw) != set(EXPECTED_MATERIALS)',
            'len(expected_packages) != 11',
            '"expected_mesh_count": 4',
            '"expected_texture_count": 3',
            '"expected_material_count": 4',
            '"expected_package_count": 11',
            'authority.get("approval_status") != "APPROVED_FOR_GUARDED_UNREAL_IMPORT"',
            'authority.get("selected_candidate", "")',
            'authority.get("selected_version", "")',
            'selected_version != WINNER_VERSION or selected_candidate != WINNER_CANDIDATE',
            'manifest_path.resolve() != EXPECTED_MANIFEST.resolve()',
            '"native" in (selected_candidate + " " + selected_version).casefold()',
            '"FROZEN__APPROVED_CAIRNWELL_V005_WINNER__READY_FOR_BASELINE"',
            '--manifest must be the exact approved v005 MANIFEST_v005.json',
            '"editor_bootstrap_world": "/Engine/Maps/Entry.Entry"',
            'LoadLevelAtStartup=None',
            '"replace_existing": False',
            '"nanite_enabled": False',
            '"has_navigation_data": False',
            '"collision_trace_flag": "CTF_USE_SIMPLE_AS_COMPLEX"',
        ):
            self.assertIn(token, self.contract_preparer)
        self.assertNotIn("DEFAULT_MANIFEST", self.contract_preparer)
        self.assertNotIn("/Game/LineBoss/Native/", self.contract_preparer)

    def test_contract_source_gates_geometry_uv_material_texture_and_hashes(self) -> None:
        for token in (
            'source.suffix.casefold() != ".fbx"',
            'max(abs(value) for value in pivot) > 0.01',
            'uv_channels not in (0, 1)',
            'degenerates != 0',
            'chain[0] > chain[1] > chain[2] > 0',
            'material-slot order differs across authored LODs',
            'does not bind every exact semantic slot once',
            'width != 2048 or height != 2048',
            'source.suffix.casefold() not in LOSSLESS_TEXTURE_SUFFIXES',
            'source_colorspace != "sRGB"',
            'source_colorspace != "Non-Color"',
            'semantic == "metallic_roughness" and channels != 4',
            'normal_convention not in {"OpenGL", "DirectX"}',
            'normal convention/Unreal green-channel conversion mismatch',
            'base_color must be sRGB',
            'must be non-colour data',
            'does not close all three Emerald maps',
            'uses the textured PBR recipe without exactly one UV channel',
            'approved source hash drift',
            'approved source size drift',
            'EmeraldBodyVisualAuthority must be the approved closed body shell',
            'EmeraldRollingGearVisualAuthority must close four tyres plus four rims',
            'runtime authority must provide 12 distinct role/LOD FBX sources',
            'runtime authority must provide three distinct texture source files',
            'every imported runtime source must reside in the exact v005 winner root',
            'approved v005 runtime inputs may not reuse v006 candidate assets',
            'require_expected=True',
            'PENDING_ROOT_VISUAL_APPROVAL_DO_NOT_PROMOTE.md',
            'Cairnwell2040_v005_FinalApprovalSupersession.json',
            'Cairnwell2040_v005_AdditiveFreezeReceipt_v002.json',
            'historical v005 do-not-promote marker must remain preserved byte-exact',
            'final v005 approval-supersession record is absent',
            'final v005 additive-freeze v002 amendment is absent',
            'payload.get("$schema") != FREEZE_AMENDMENT_SCHEMA',
            'post_v1_changed_files_except_declared_schema_key',
            'final v005 additive-freeze v002 amendment no-other-drift proof drift',
        ):
            self.assertIn(token, self.contract_preparer)

    def test_contract_rejects_non_finite_vector_authority_values(self) -> None:
        namespace = {"__name__": "cairnwell_contract_static_regression"}
        exec(compile(self.contract_preparer, str(CONTRACT_PREPARER), "exec"), namespace)
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                        namespace["ContractError"], "must contain only finite coordinates"):
                    namespace["as_vector"]([value, 0.0, 0.0], "finite_regression")

    def test_approval_supersession_fails_when_absent_or_evidence_hash_drifts(self) -> None:
        namespace = {"__name__": "cairnwell_supersession_static_regression"}
        exec(compile(self.contract_preparer, str(CONTRACT_PREPARER), "exec"), namespace)
        with tempfile.TemporaryDirectory(prefix="lb_c2040_supersession_") as temporary:
            project = Path(temporary).resolve()
            winner = project / "ProductionCandidate_v005"
            marker = winner / "PENDING_ROOT_VISUAL_APPROVAL_DO_NOT_PROMOTE.md"
            manifest = winner / "MANIFEST_v005.json"
            record = winner / "Audit/Cairnwell2040_v005_FinalApprovalSupersession.json"
            evidence_paths = {
                "historical_do_not_promote_marker": marker,
                "approved_manifest": manifest,
                "manual_paint_mask_audit": winner / "Audit/ManualMask.json",
                "manual_paint_mask_texture": winner / "Textures/ManualMask.png",
            }
            render_paths = {
                name: winner / f"Renders/ManualPaintMask_{name}.png"
                for name in ("front", "hero", "rear", "side")
            }
            for index, path in enumerate([*evidence_paths.values(), *render_paths.values()]):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(f"authority-{index}".encode("ascii"))

            namespace.update({
                "PROJECT": project,
                "WINNER_ROOT": winner,
                "EXPECTED_MANIFEST": manifest,
                "PENDING_MARKER": marker,
                "SUPERSESSION_RECORD": record,
                "EXPECTED_SUPERSESSION_EVIDENCE": evidence_paths,
                "EXPECTED_SUPERSESSION_RENDERS": render_paths,
                "validate_freeze_amendment": lambda: {"status": "TEST_ONLY"},
            })
            with self.assertRaisesRegex(
                    namespace["ContractError"], "approval-supersession record is absent"):
                namespace["validate_approval_supersession"](manifest)

            def row(path: Path) -> dict:
                data = path.read_bytes()
                return {
                    "path": path.relative_to(project).as_posix(),
                    "sha256": hashlib.sha256(data).hexdigest().upper(),
                    "bytes": len(data),
                }

            payload = {
                "$schema": namespace["SUPERSESSION_SCHEMA"],
                "status": namespace["SUPERSESSION_STATUS"],
                "selected_candidate": namespace["WINNER_CANDIDATE"],
                "selected_version": namespace["WINNER_VERSION"],
                "historical_marker_preserved_byte_exact": True,
                "supersedes_historical_marker_without_deletion": True,
                "unreal_import_or_promotion_performed": False,
                "root_visual_approval": {
                    "status": "PASS",
                    "visible_isolated_false_positive_regions": 0,
                    "painted_roof_and_body_included": True,
                    "glazing_lamps_trim_diffuser_and_wheels_excluded": True,
                },
                "evidence": {key: row(path) for key, path in evidence_paths.items()},
                "manual_paint_mask_renders": {
                    key: row(path) for key, path in render_paths.items()
                },
            }
            payload["evidence"]["historical_do_not_promote_marker"]["sha256"] = "0" * 64
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(namespace["ContractError"], "approved source hash drift"):
                namespace["validate_approval_supersession"](manifest)

            payload["evidence"]["historical_do_not_promote_marker"] = row(marker)
            record.write_text(json.dumps(payload), encoding="utf-8")
            validated = namespace["validate_approval_supersession"](manifest)
            self.assertTrue(validated["historical_marker_preserved_byte_exact"])
            self.assertEqual(set(validated["manual_paint_mask_renders"]), set(render_paths))

    def test_freeze_amendment_fails_when_missing_stale_or_hash_drifted(self) -> None:
        namespace = {"__name__": "cairnwell_amendment_static_regression"}
        exec(compile(self.contract_preparer, str(CONTRACT_PREPARER), "exec"), namespace)
        with tempfile.TemporaryDirectory(prefix="lb_c2040_amendment_") as temporary:
            project = Path(temporary).resolve()
            winner = project / "ProductionCandidate_v005"
            audit_root = winner / "Audit"
            stale = audit_root / "Cairnwell2040_v005_AdditiveFreezeReceipt.json"
            supersession = audit_root / "Cairnwell2040_v005_FinalApprovalSupersession.json"
            amendment = audit_root / "Cairnwell2040_v005_AdditiveFreezeReceipt_v002.json"
            manifest = winner / "MANIFEST_v005.json"
            mask_audit = audit_root / "ManualMask.json"
            mask_texture = winner / "Textures/ManualMask.png"
            renders = {
                name: winner / f"Renders/ManualPaintMask_{name}.png"
                for name in ("front", "hero", "rear", "side")
            }
            preexisting = winner / "preexisting.bin"
            sources = [stale, supersession, manifest, mask_audit, mask_texture,
                       *renders.values(), preexisting]
            for index, path in enumerate(sources):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(f"amendment-authority-{index}".encode("ascii"))

            def digest(path: Path) -> str:
                return hashlib.sha256(path.read_bytes()).hexdigest().upper()

            def inventory_row(path: Path) -> dict:
                return {"bytes": path.stat().st_size, "sha256": digest(path)}

            stale_relative = stale.relative_to(winner).as_posix()
            supersession_relative = supersession.relative_to(winner).as_posix()
            amendment_relative = amendment.relative_to(winner).as_posix()
            namespace.update({
                "PROJECT": project,
                "WINNER_ROOT": winner,
                "EXPECTED_MANIFEST": manifest,
                "STALE_FREEZE_RECEIPT": stale,
                "SUPERSESSION_RECORD": supersession,
                "FREEZE_AMENDMENT_RECORD": amendment,
                "STALE_FREEZE_RECEIPT_SHA256": digest(stale),
                "STALE_FREEZE_RECEIPT_BYTES": stale.stat().st_size,
                "CURRENT_SUPERSESSION_SHA256": digest(supersession),
                "CURRENT_SUPERSESSION_BYTES": supersession.stat().st_size,
                "STALE_V1_SUPERSESSION_SHA256": "1" * 64,
                "FREEZE_AMENDMENT_PREEXISTING_COUNT": 1,
                "EXPECTED_SUPERSESSION_EVIDENCE": {
                    "historical_do_not_promote_marker": preexisting,
                    "approved_manifest": manifest,
                    "manual_paint_mask_audit": mask_audit,
                    "manual_paint_mask_texture": mask_texture,
                },
                "EXPECTED_SUPERSESSION_RENDERS": renders,
            })
            with self.assertRaisesRegex(
                    namespace["ContractError"], "v002 amendment is absent"):
                namespace["validate_freeze_amendment"]()

            final_inventory = {
                path.relative_to(winner).as_posix(): inventory_row(path)
                for path in sources if path != preexisting
            }
            payload = {
                "$schema": namespace["FREEZE_AMENDMENT_SCHEMA"],
                "status": namespace["FREEZE_AMENDMENT_STATUS"],
                "selected_candidate": namespace["WINNER_CANDIDATE"],
                "selected_version": namespace["WINNER_VERSION"],
                "current_contract_authority": True,
                "supersedes_stale_v1_receipt_without_modifying_it": True,
                "unreal_import_or_promotion_performed": False,
                "self_excluded_from_inventory": amendment_relative,
                "self_exclusion_reason": (
                    "A content-addressed receipt cannot include its own final hash without circularity."
                ),
                "stale_v1_receipt_expected_sha256": digest(stale),
                "stale_v1_receipt": {
                    "path": stale_relative, **inventory_row(stale),
                },
                "current_supersession": {
                    "path": supersession_relative, **inventory_row(supersession),
                },
                "declared_post_v1_incident": {
                    "changed_path": supersession_relative,
                    "current_expected_bytes": supersession.stat().st_size,
                    "current_expected_sha256": digest(supersession),
                    "current_state": inventory_row(supersession),
                    "v1_pinned_state": {
                        "bytes": supersession.stat().st_size,
                        "sha256": "1" * 64,
                    },
                    "sole_change": namespace["FREEZE_AMENDMENT_SOLE_CHANGE"],
                },
                "post_v1_changed_files": {
                    supersession_relative: {
                        "current": inventory_row(supersession),
                        "v1": {
                            "bytes": supersession.stat().st_size,
                            "sha256": "1" * 64,
                        },
                    }
                },
                "post_v1_changed_files_except_declared_schema_key": [],
                "post_v1_missing_files": [],
                "post_v1_unexpected_additions": [],
                "changed_preexisting_files": [],
                "preexisting_file_count": 1,
                "preexisting_inventory_before": {
                    preexisting.relative_to(winner).as_posix(): inventory_row(preexisting),
                },
                "preexisting_inventory_after": {
                    preexisting.relative_to(winner).as_posix(): inventory_row(preexisting),
                },
                "final_authority_and_additive_inventory": final_inventory,
            }

            def write_amendment() -> None:
                amendment.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
                namespace["FREEZE_AMENDMENT_SHA256"] = digest(amendment)
                namespace["FREEZE_AMENDMENT_BYTES"] = amendment.stat().st_size

            payload["stale_v1_receipt"]["sha256"] = "0" * 64
            write_amendment()
            with self.assertRaisesRegex(
                    namespace["ContractError"], "identity/chain drift"):
                namespace["validate_freeze_amendment"]()

            payload["stale_v1_receipt"]["sha256"] = digest(stale)
            write_amendment()
            validated = namespace["validate_freeze_amendment"]()
            self.assertTrue(validated["current_contract_authority"])
            self.assertTrue(validated["no_other_changed_files"])

            amendment.write_bytes(amendment.read_bytes() + b"\n")
            with self.assertRaisesRegex(namespace["ContractError"], "approved source hash drift"):
                namespace["validate_freeze_amendment"]()

    def test_player_selectable_paint_contract_graph_and_role_bindings_are_exact(self) -> None:
        self.assertEqual(
            literal_assignment(self.contract_preparer, "EXPECTED_MATERIALS"),
            {
                "body": ("M_LB_C2040_BodyPaintTintPBR_v001", "textured_tint_pbr"),
                "rolling_gear": ("M_LB_C2040_RollingGearPBR_v001", "textured_pbr"),
                "biw_galvanised": ("M_LB_C2040_BIWGalvanized_v001", "solid_pbr"),
                "ed_coat": ("M_LB_C2040_EDCoat_v001", "solid_pbr"),
            },
        )
        self.assertEqual(
            literal_assignment(self.contract_preparer, "EXPECTED_ROLE_MATERIAL"),
            {
                "BIW_AutomotiveSkeleton": "biw_galvanised",
                "BIW_UnderbodySubset": "ed_coat",
                "EmeraldBodyVisualAuthority": "body",
                "EmeraldRollingGearVisualAuthority": "rolling_gear",
            },
        )
        for token in (
            '"textured_tint_pbr"',
            '"VehiclePaintColour"',
            '"paint_mask_texture_semantic"',
            '"metallic_roughness"',
            '"paint_mask_channel"',
            '"BodyPaintMask"',
            'set(module["material_bindings"].values()) != {EXPECTED_ROLE_MATERIAL[role]}',
            '"detail_luminance_weights"',
            '"detail_normalization"',
            '"detail_clamp_min"',
            '"detail_clamp_max"',
            '"paint_mask_authority"',
            '"APPROVED__MANUALLY_AUTHORED_V005_BODY_PAINT_MASK__VISUALLY_VALIDATED"',
            'paint_mask_raw.get("manual_authored") is not True',
            'paint_mask_raw.get("v006_mask_reused") is not False',
            'paint_mask_raw.get("false_positive_fragment_count", -1)',
        ):
            self.assertIn(token, self.contract_preparer)

        importer = IMPORTER.read_text(encoding="utf-8")
        runtime = self.runtime
        for token in (
            "textured_tint_pbr",
            "VehiclePaintColour",
            "paint_mask_texture_semantic",
            "paint_mask_channel",
            "MaterialExpressionVectorParameter",
            "MaterialExpressionMultiply",
            "MaterialExpressionDotProduct",
            "MaterialExpressionClamp",
            "MaterialExpressionConstant3Vector",
            "MaterialExpressionLinearInterpolate",
            "Alpha",
        ):
            self.assertIn(token, importer)
            self.assertIn(token, runtime)
        for token in (
            "body:base_to_luminance",
            "body:luminance_weights",
            "body:luminance_to_normalize",
            "body:detail_normalization",
            "body:normalized_detail_to_clamp",
            "body:paint_parameter_to_absolute_hue",
            "body:clamped_luminance_to_paint_detail",
            "body:untinted_base_to_lerp",
            "body:tinted_base_to_lerp",
            "body:paint_mask_to_lerp",
        ):
            self.assertIn(token, importer)
        for token in (
            'expression_classes != expected_classes',
            'list(lerp_raw) != ["A", "B", "Alpha"]',
            'list(tint_raw) != ["A", "B"]',
            'list(normalized_raw) != ["A", "B"]',
            'list(luminance_raw) != ["A", "B"]',
            'key + ":lerp_A_unmodified_base"',
            'key + ":lerp_Alpha_mask"',
            'lerp_raw["A"] is not luminance_raw["A"]',
            '"absolute_hue_tonal_detail_reaches_base_color_only_through_masked_lerp": True',
        ):
            self.assertIn(token, runtime)
        self.assertIn("EmeraldBodyVisualAuthority", runtime)
        self.assertIn("EmeraldRollingGearVisualAuthority", runtime)

    def test_offline_preparers_are_syntax_valid_and_write_only_their_authorities(self) -> None:
        for path, source in (
            (CONTRACT_PREPARER, self.contract_preparer),
            (BASELINE_PREPARER, self.baseline_preparer),
            (RECOVERY_PREPARER, self.recovery_preparer),
            (V004_RECOVERY_PREPARER, self.v004_recovery_preparer),
            (V005_RECOVERY_PREPARER, self.v005_recovery_preparer),
            (V006_RECOVERY_PREPARER, self.v006_recovery_preparer),
            (V007_RECOVERY_PREPARER, self.v007_recovery_preparer),
            (V008_RECOVERY_PREPARER, self.v008_recovery_preparer),
            (V009_RECOVERY_PREPARER, self.v009_recovery_preparer),
        ):
            compile(source, str(path), "exec")
            self.assertNotIn("import unreal", source)
            self.assertNotIn("subprocess", source)
            for forbidden in (".unlink(", ".rmdir(", "shutil.rmtree", "os.remove(", "delete_asset("):
                self.assertNotIn(forbidden, source)
        self.assertEqual(write_text_receivers(self.contract_preparer), ["OUTPUT", "OUTPUT_SHA"])
        self.assertEqual(write_text_receivers(self.baseline_preparer), ["BASELINE", "BASELINE_SHA"])
        self.assertEqual(write_text_receivers(self.recovery_preparer), ["OUTPUT", "OUTPUT_SHA"])
        self.assertEqual(
            write_text_receivers(self.v004_recovery_preparer), ["OUTPUT", "OUTPUT_SHA"])
        self.assertEqual(
            write_text_receivers(self.v005_recovery_preparer), ["OUTPUT", "OUTPUT_SHA"])
        self.assertEqual(
            write_text_receivers(self.v006_recovery_preparer), ["OUTPUT", "OUTPUT_SHA"])
        self.assertEqual(
            write_text_receivers(self.v007_recovery_preparer), ["OUTPUT", "OUTPUT_SHA"])
        self.assertEqual(
            write_text_receivers(self.v008_recovery_preparer), ["OUTPUT", "OUTPUT_SHA"])
        self.assertEqual(
            write_text_receivers(self.v009_recovery_preparer), ["OUTPUT", "OUTPUT_SHA"])
        for token in (
            "refusing to overwrite an existing contract or sidecar",
            "manifest is not present",
            '"overwrite_reimport_delete_authorized": False',
            '"map_load_save_authorized": False',
            '"runtime_binding_or_map_promotion_authorized": False',
            '"panel_module_namespace_or_packages_authorized": False',
            '"source_config_maps_saves_writes_authorized": False',
        ):
            self.assertIn(token, self.contract_preparer)
        for token in (
            "complete_source_tree",
            "complete_config_tree",
            "all_existing_content_outside_destination_including_maps",
            "campaign_save_games",
            "refusing to overwrite an existing Cairnwell baseline",
            '"paint_mask_authority": contract["paint_mask_authority"]',
            '"approval_supersession": contract["approval_supersession"]',
            'payload.get("paint_mask_authority") != contract.get("paint_mask_authority")',
            'payload.get("approval_supersession") != contract.get("approval_supersession")',
            "--verify-post-import-immutable",
            "PASS__CAIRNWELL_2040_RUNTIME_V001_POST_IMPORT_SOURCE_PROTECTED_LANE_REVERIFIED",
        ):
            self.assertIn(token, self.baseline_preparer)

    def test_recovery_v002_pins_incident_partials_and_ue58_api_fix(self) -> None:
        importer = IMPORTER.read_text(encoding="utf-8")
        validator = VALIDATOR.read_text(encoding="utf-8")
        v002_preparer = V002_RECOVERY_PREPARER.read_text(encoding="utf-8")
        v002_doc = V002_RECOVERY_DOC.read_text(encoding="utf-8")
        compile(v002_preparer, str(V002_RECOVERY_PREPARER), "exec")
        self.assertIn(
            'connect_nodes(normalized_luminance, "", detail_clamp, "",', importer)
        self.assertNotIn(
            'connect_nodes(normalized_luminance, "", detail_clamp, "Input",', importer)
        self.assertIn(
            '"MaterialExpressionClamp": ["None", "Min", "Max"]', self.runtime)
        self.assertIn('list(clamp_raw) != ["", "Min", "Max"]', self.runtime)
        self.assertIn('clamp_raw[""]', self.runtime)
        self.assertIn('clamp_links[""]', self.runtime)
        self.assertNotIn("unreal.SystemLibrary.quit_editor()", importer)
        self.assertNotIn("unreal.SystemLibrary.quit_editor()", validator)
        for token in (
            "MaterialPinNames::Input",
            "NAME_None",
            "empty `ToInputName`",
            "defers `QUIT_EDITOR` itself",
            "026D9A5C896AF1E590E4BD8E42F1EC4788C8210198007D79C5051F8792716DD9",
            "AB9EB8F439AAD66A18C632E8CDA227A2252F737A9E4BE8150407F9C6BEFCA8B2",
        ):
            self.assertIn(token, v002_doc)
        for token in (
            'FAILED_RUN_ID = "20260815T094919Z-7dfb3c0a"',
            '"05F204CDE09BD22BED823101525C82F64E18F8EE56BC6004C9E0979AA73CFC2D"',
            '"MOVE_DIRECTORY_ONLY__NO_DELETE"',
            '"unreal_launch_authorized_by_freeze": False',
            '"strict_editor_exit_code_zero_required": True',
            '"post_receipt_fatal_or_crash_accepted": False',
            'verify_snapshot(baseline["source"]',
            'verify_snapshot(baseline["protected"]',
            'verify_original_lane_drift(baseline)',
            'verify_partial_contract(payload, "source destination")',
            'verify_partial_contract(payload, "quarantine")',
        ):
            self.assertIn(token, v002_preparer)
        for forbidden in (
            ".unlink(", ".rmdir(", "shutil.rmtree", "os.remove(",
            "subprocess", "import unreal", "Move-Item", "Start-Process",
        ):
            self.assertNotIn(forbidden, v002_preparer)

    def test_recovery_v003_slot_identity_is_exact_and_never_fuzzy(self) -> None:
        importer = IMPORTER.read_text(encoding="utf-8")
        self.assertIn("normalize_gameplay_material_slot", importer)
        for token in (
            'actual_slots != expected_imported',
            'imported_slots != expected_imported',
            '"material_slot_name", rule["canonical_material_slot_name"]',
            'final_slots != expected_canonical',
            'final_imported != expected_imported',
            '"normalization_applied": changed',
        ):
            self.assertIn(token, importer)
        for forbidden in ("endswith('_001')", 'removesuffix("_001")', "fuzzy", "casefold() =="):
            self.assertNotIn(forbidden, importer)
        for token in (
            'FBX_NAME_PATTERN = re.compile(rb"MI_LB_C2040_[A-Za-z0-9_.]+")',
            'len(matches) != 1 or len(unique) != 1',
            'MI_LB_C2040_BIW_GalvanisedSteel_v005.001',
            'MI_LB_C2040_BIW_GalvanisedSteel_v005_001',
            'unexpected material-slot rewrite would be required',
            'source_occurrence_count_by_lod',
            '506DE36CC110B754D70800E964A6BCF8D38D304B94C8D8AE3E947B0351B99EF8',
        ):
            self.assertIn(token, self.recovery_preparer)
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        rules = {}
        namespace = {"__name__": "cairnwell_v003_slot_static"}
        exec(compile(self.recovery_preparer, str(RECOVERY_PREPARER), "exec"), namespace)
        rules = namespace["slot_normalization"](contract)
        self.assertEqual(set(rules), EXPECTED_ROLES)
        special = rules["BIW_AutomotiveSkeleton"]
        self.assertEqual(special["source_occurrence_count_by_lod"], [1, 1, 1])
        self.assertTrue(special["normalize_gameplay_material_slot_name"])
        self.assertEqual(
            [role for role, rule in rules.items() if rule["normalize_gameplay_material_slot_name"]],
            ["BIW_AutomotiveSkeleton"],
        )
        self.assertIn("FbxMainImport.cpp:1870-1888", self.recovery_doc)

    def test_recovery_v003_log_retry_waits_for_a_real_read_open_and_times_out(self) -> None:
        for token in (
            "Get-LBFileEvidenceWithBoundedReadRetry",
            "[IO.File]::Open(",
            "[IO.FileShare]::Read",
            "catch [IO.IOException]",
            "catch [UnauthorizedAccessException]",
            "Start-Sleep -Milliseconds",
            "remained unreadable after",
        ):
            self.assertIn(token, self.log_retry_helper)
        self.assertNotIn("Get-FileHash", self.log_retry_helper)

        shell = shutil.which("pwsh") or shutil.which("powershell")
        self.assertIsNotNone(shell, "PowerShell is required for the Windows lock regression")
        with tempfile.TemporaryDirectory() as temp_root:
            locked_path = Path(temp_root) / "redirected stdout.log"
            content = "final redirected stdout bytes\n"
            locked_path.write_text(content, encoding="utf-8")
            expected_hash = hashlib.sha256(locked_path.read_bytes()).hexdigest().upper()
            escaped_path = str(locked_path).replace("'", "''")
            escaped_helper = str(LOG_RETRY_HELPER).replace("'", "''")

            def start_locker(hold_milliseconds: int) -> subprocess.Popen[str]:
                script = (
                    f"$s=[IO.File]::Open('{escaped_path}',[IO.FileMode]::Open,"
                    "[IO.FileAccess]::ReadWrite,[IO.FileShare]::None);"
                    "[Console]::Out.WriteLine('LOCKED');[Console]::Out.Flush();"
                    f"Start-Sleep -Milliseconds {hold_milliseconds};$s.Dispose()"
                )
                process = subprocess.Popen(
                    [shell, "-NoProfile", "-Command", script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                self.assertEqual(process.stdout.readline().strip(), "LOCKED")
                return process

            locker = start_locker(650)
            success_script = (
                f". '{escaped_helper}';"
                f"$e=Get-LBFileEvidenceWithBoundedReadRetry -Path '{escaped_path}' "
                "-Label 'locked regression' -TimeoutMilliseconds 5000;"
                "[Console]::Out.WriteLine(($e.sha256+'|'+$e.read_open_attempts+'|'+"
                "$e.waited_milliseconds))"
            )
            success = subprocess.run(
                [shell, "-NoProfile", "-Command", success_script],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            locker_stdout, locker_stderr = locker.communicate(timeout=5)
            self.assertEqual(locker.returncode, 0, locker_stdout + locker_stderr)
            self.assertEqual(success.returncode, 0, success.stdout + success.stderr)
            digest, attempts, waited = success.stdout.strip().split("|")[-3:]
            self.assertEqual(digest, expected_hash)
            self.assertGreater(int(attempts), 1)
            self.assertGreater(int(waited), 0)

            locker = start_locker(1000)
            timeout_script = (
                f". '{escaped_helper}';"
                f"Get-LBFileEvidenceWithBoundedReadRetry -Path '{escaped_path}' "
                "-Label 'locked timeout regression' -TimeoutMilliseconds 250"
            )
            timed_out = subprocess.run(
                [shell, "-NoProfile", "-Command", timeout_script],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            locker_stdout, locker_stderr = locker.communicate(timeout=5)
            self.assertEqual(locker.returncode, 0, locker_stdout + locker_stderr)
            self.assertNotEqual(timed_out.returncode, 0)
            self.assertIn(
                "locked timeout regression remained unreadable",
                timed_out.stdout + timed_out.stderr,
            )

    def test_recovery_v004_pins_exact_ue58_runtime_uv_sanitation(self) -> None:
        compile(self.v004_recovery_preparer, str(V004_RECOVERY_PREPARER), "exec")
        for token in (
            'V003_RUN_ID = "20260815T105958Z-79a98abc"',
            "3FB3E1A8F27F1E4EF477C6F1E3E3AF41E53F2C8618CAC9A4E0A047F91BD60E7C",
            "D6E42F80894F87E580DD72FC2EE7F9A46E312DDE1AB006F18F01A068408523C6",
            '"lines": "709-718"',
            "NumUVs = FMath::Max(1, NumUVs)",
            "expected_unreal_uv_channels_by_lod",
            "ue_forced_minimum_one_by_lod",
            "actual_triangles\": 59998",
            "actual_render_vertices\": 29109",
            "actual_unreal_uv_channels\": 1",
            "triangle_or_degenerate_removal_drift\": False",
            "MOVE_DIRECTORY_ONLY__NO_DELETE",
        ):
            self.assertIn(token, self.v004_recovery_preparer)
        for forbidden in (
            ".unlink(", ".rmdir(", "shutil.rmtree", "os.remove(",
            "import unreal", "subprocess", "endswith('_001')",
        ):
            self.assertNotIn(forbidden, self.v004_recovery_preparer)

        namespace = {
            "__name__": "cairnwell_v004_uv_static",
            "__file__": str(V004_RECOVERY_PREPARER),
        }
        exec(
            compile(self.v004_recovery_preparer, str(V004_RECOVERY_PREPARER), "exec"),
            namespace,
        )
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        authority = namespace["runtime_uv_sanitization"](contract)
        self.assertEqual(set(authority["roles"]), EXPECTED_ROLES)
        for role in ("BIW_AutomotiveSkeleton", "BIW_UnderbodySubset"):
            rule = authority["roles"][role]
            self.assertEqual(rule["source_uv_channels_by_lod"], [0, 0, 0])
            self.assertEqual(rule["expected_unreal_uv_channels_by_lod"], [1, 1, 1])
            self.assertEqual(rule["ue_forced_minimum_one_by_lod"], [True, True, True])
        for role in ("EmeraldBodyVisualAuthority", "EmeraldRollingGearVisualAuthority"):
            rule = authority["roles"][role]
            self.assertEqual(rule["source_uv_channels_by_lod"], [1, 1, 1])
            self.assertEqual(rule["expected_unreal_uv_channels_by_lod"], [1, 1, 1])
            self.assertEqual(rule["ue_forced_minimum_one_by_lod"], [False, False, False])
        observed = authority["v003_observed_biw_automotive_skeleton_lod0"]
        self.assertEqual(
            (observed["actual_triangles"], observed["actual_render_vertices"],
             observed["actual_unreal_uv_channels"]),
            (59998, 29109, 1),
        )
        self.assertFalse(observed["triangle_or_degenerate_removal_drift"])

        self.assertIn("expected_unreal_uv_channels_by_lod", self.runtime)
        self.assertIn('"unreal_uv_channels": uv_channels', self.runtime)
        self.assertIn('uv_channels == expected_unreal_uv_channels', self.runtime)
        self.assertIn('source UV authority drift', self.runtime)
        self.assertNotIn('or uv_channels != int(expected["uv_channels"])', self.runtime)
        for token in (
            "triangles: expected `59998`, actual `59998`",
            "actual render vertices: `29109`",
            "source UV channels: expected `0`, actual Unreal render UV channels: `1`",
            "triangulation and degenerate-face removal were not the failure",
            "separate exact `expected_unreal_uv_channels_by_lod` contract",
        ):
            self.assertIn(token, self.v004_recovery_doc)

    def test_recovery_v005_converts_all_source_bounds_to_exact_ue_handedness(self) -> None:
        compile(self.v005_recovery_preparer, str(V005_RECOVERY_PREPARER), "exec")
        for token in (
            'V004_RUN_ID = "20260815T112446Z-4e34bb5c"',
            "D5BFCA5C8C2380587ECADDE9C64455FFD60A282D54A6FF8E27CD2E7144B494DF",
            "E96AF266A819FD61B94F637253C409B98312B13B24E32B1E873CB4AB45481FB2",
            "690FB6D64A5375CAF53635FC1EFE210FED8C9D2679C5A2F864D08F742085198B",
            '"lines": "63-71"',
            '"lines": "406-410"',
            "converted_minimum = [minimum[0], -maximum[1], minimum[2]]",
            "converted_maximum = [maximum[0], -minimum[1], maximum[2]]",
            '"comparison_tolerance_cm": 0.25',
            '"tolerance_relaxed": False',
            '"source_or_fbx_modified": False',
            'OBSERVED_ORIGIN_OFFSET = 15767',
            'OBSERVED_EXTENT_OFFSET = 15840',
            'current_source = V004_QUARANTINE / underbody_relative',
            'current_source = DEST / underbody_relative',
            'current["package"]["path"] = prior.prior.relative(DEST / underbody_relative)',
            'MOVE_DIRECTORY_ONLY__NO_DELETE',
        ):
            self.assertIn(token, self.v005_recovery_preparer)
        for forbidden in (
            ".unlink(", ".rmdir(", "shutil.rmtree", "os.remove(",
            "import unreal", "subprocess", "copy2(", "replace_existing",
        ):
            self.assertNotIn(forbidden, self.v005_recovery_preparer)

        namespace = {
            "__name__": "cairnwell_v005_bounds_static",
            "__file__": str(V005_RECOVERY_PREPARER),
        }
        exec(
            compile(self.v005_recovery_preparer, str(V005_RECOVERY_PREPARER), "exec"),
            namespace,
        )
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        authority = namespace["runtime_bounds_conversion"](contract)
        self.assertEqual(set(authority["roles"]), EXPECTED_ROLES)
        self.assertEqual(authority["comparison_tolerance_cm"], 0.25)
        self.assertFalse(authority["tolerance_relaxed"])
        for role, role_rule in authority["roles"].items():
            self.assertEqual([row["lod"] for row in role_rule["lods"]], [0, 1, 2])
            for index, row in enumerate(role_rule["lods"]):
                source = contract["modules"][role]["lods"][index]["expected_unreal_bounds"]
                expected = row["expected_unreal_bounds_cm"]
                self.assertEqual(row["frozen_source_bounds_cm"], source)
                self.assertEqual(
                    expected["minimum_cm"],
                    [source["minimum_cm"][0], -source["maximum_cm"][1], source["minimum_cm"][2]],
                )
                self.assertEqual(
                    expected["maximum_cm"],
                    [source["maximum_cm"][0], -source["minimum_cm"][1], source["maximum_cm"][2]],
                )
                self.assertEqual(expected["dimensions_cm"], source["dimensions_cm"])
                self.assertEqual(expected["pivot_cm"], [0.0, 0.0, 0.0])
        forensic = authority["v004_underbody_lod0_failure_forensics"]
        self.assertEqual(
            forensic["v004_preserved_package"]["minimum_cm"],
            [-225.9876251220703, -79.09723663330078, 8.614322662353516],
        )
        self.assertEqual(
            forensic["v004_preserved_package"]["maximum_cm"],
            [226.0123748779297, 80.06865692138672, 74.74723052978516],
        )
        self.assertGreater(forensic["source_space_y_endpoint_mismatch_cm"], 0.97)
        self.assertLess(forensic["maximum_expected_vs_observed_delta_cm"], 0.00003)

        for token in (
            'runtime_bounds_coordinate_conversion',
            'runtime_bounds_rule["frozen_source_bounds_cm"]',
            'runtime_bounds_rule["expected_unreal_bounds_cm"]',
            'runtime_bounds_tolerance_must_remain_0_25_cm',
        ):
            self.assertIn(token, self.runtime)
        self.assertNotIn(
            'bounds,\n            expected["expected_unreal_bounds"],', self.runtime)
        for token in (
            "`(X, -Y, Z)`",
            "`min=(minX,-maxY,minZ)`",
            "`max=(maxX,-minY,maxZ)`",
            "0.9714353667 cm",
            "0.297791 cm",
            "all four modules and all three authored LODs",
            "unchanged at `0.25 cm`",
            "MOVE-only",
        ):
            self.assertIn(token, self.v005_recovery_doc)

    def test_recovery_v006_pins_texture_forensics_and_exact_ue_enum_identity(self) -> None:
        compile(self.v006_recovery_preparer, str(V006_RECOVERY_PREPARER), "exec")
        importer = IMPORTER.read_text(encoding="utf-8")
        validator = VALIDATOR.read_text(encoding="utf-8")
        runner = RUNNER.read_text(encoding="utf-8")
        for token in (
            'V005_RUN_ID = "20260815T115847Z-92ea69dd"',
            "435D82778C83CDACAA2E59F91E04273181BA710F5D0BAFFA719A15E04A9F48BB",
            "E5E9F4CF0E003C0B5936E0EED581D6E697E1C20AD0BC1B390E6FA7D3ADD2E239",
            "8476C9EF8CFE8A3E58C383FEC80085370F2554F91618569598FDE5D975E79A4A",
            "54488C18B0C2916E89BF416EAC8F008E79AF430AC2F4EA8299A603D5809693AA",
            '"repr_lines": "378-385"',
            '"exact_comparison_lines": "388-410"',
            '"string_suffix_comparison_forbidden": True',
            '"semantic_gates_relaxed": False',
            '"operation": "MOVE_DIRECTORY_ONLY__NO_DELETE"',
            "Incident_20260815T115847Z-92ea69dd_v005",
            'snapshot["file_count"] != 29',
            'actual_disk != expected_disk',
            'len(actual_disk) != 11',
            'declared_chain_hash != object_hash(bound_chain)',
        ):
            self.assertIn(token, self.v006_recovery_preparer)
        for forbidden in (
            ".unlink(", ".rmdir(", "shutil.rmtree", "os.remove(",
            "import unreal", "subprocess", "copy2(", "replace_existing",
        ):
            self.assertNotIn(forbidden, self.v006_recovery_preparer)

        for token in (
            "TEXTURE_COMPRESSION_BY_NAME",
            "MATERIAL_SAMPLER_BY_NAME",
            "CLAMP_MODE_BY_NAME",
            "COLLISION_TRACE_BY_NAME",
            "BLEND_MODE_BY_NAME",
            "MATERIAL_DOMAIN_BY_NAME",
            "def enum_is_exact",
            "type(actual) is type(expected) and actual == expected",
            "def canonical_enum_name",
            "compression_runtime_repr",
            "fail_expected_actual",
            'material.get_editor_property("material_domain")',
            'material.get_editor_property("two_sided")',
            'except RuntimeError:',
            'declared_chain_hash != object_hash(bound_chain)',
            'payload.get("policy", {}).get("exact_ue_enum_identity_required") is not True',
            '"enum_string_suffix_comparisons_forbidden") is not True',
        ):
            self.assertIn(token, self.runtime)
        self.assertNotIn(".endswith(", self.runtime)
        self.assertNotIn('"SIMPLE_AS_COMPLEX" not in trace.upper()', self.runtime)
        self.assertIn('"material_domain": unreal.MaterialDomain.MD_SURFACE', importer)
        self.assertIn('"blend_mode": unreal.BlendMode.BLEND_OPAQUE', importer)
        self.assertNotIn("unreal.SystemLibrary.quit_editor()", importer)
        self.assertNotIn("unreal.SystemLibrary.quit_editor()", validator)

        for token in (
            "all three textures are correct",
            "2048×2048",
            "`TC_DEFAULT`",
            "`TC_MASKS`",
            "`TC_NORMALMAP`",
            "<Type.NAME: numeric_value>",
            "exact type/value identity",
            "Compound failures name every mismatched field",
            "Recovery_v006",
            "MOVE-only",
        ):
            self.assertIn(token, self.v006_recovery_doc)
        for token in (
            "$ActualDiskPaths.Count -ne 11",
            "$ExpectedDiskPaths -join",
            "$ActualDiskPaths -join",
            "Post-exit namespace all-file closure is not the exact eleven uassets",
        ):
            self.assertIn(token, runner)

        paired = [V006_RECOVERY_CONTRACT.exists(), V006_RECOVERY_CONTRACT_SHA.exists()]
        self.assertIn(sum(paired), (0, 2))
        if all(paired):
            digest = hashlib.sha256(V006_RECOVERY_CONTRACT.read_bytes()).hexdigest().upper()
            self.assertEqual(
                V006_RECOVERY_CONTRACT_SHA.read_text(encoding="ascii").split()[0].upper(),
                digest,
            )
            payload = json.loads(V006_RECOVERY_CONTRACT.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["$schema"],
                "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v6",
            )
            self.assertEqual(payload["status"], (
                "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V006__"
                "READY_FOR_ONE_SHOT_QUARANTINE_AND_TWO_PROCESS_IMPORT"))
            chain = dict(payload["incident_chain"])
            declared = chain.pop("binding_sha256")
            recomputed = hashlib.sha256(
                json.dumps(chain, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest().upper()
            self.assertEqual(declared, recomputed)
            self.assertEqual(payload["lane"]["file_count"], 29)
            self.assertEqual(len(payload["partial_packages"]), 11)
            self.assertEqual(payload["prior_quarantines"]["v004_partial_packages"]["file_count"], 11)
            self.assertTrue(payload["policy"]["exact_ue_enum_identity_required"])
            self.assertTrue(payload["policy"]["enum_string_suffix_comparisons_forbidden"])
            enum_authority = payload["exact_ue_enum_validation"]
            self.assertFalse(enum_authority["semantic_gates_relaxed"])
            self.assertEqual(len(enum_authority["read_only_diagnostic"]["files"]), 8)

    def test_stale_recovery_v007_pair_pins_exact_none_fix_and_v1_v6_chain(self) -> None:
        compile(self.v007_recovery_preparer, str(V007_RECOVERY_PREPARER), "exec")
        importer = IMPORTER.read_text(encoding="utf-8")
        validator = VALIDATOR.read_text(encoding="utf-8")
        runner = RUNNER.read_text(encoding="utf-8")
        for token in (
            'V006_RUN_ID = "20260815T124823Z-67c989ee"',
            "A484FAAB8F612A0EE9FA915436B3389016D7137CB954580C499BDBBFE2A15F06",
            "A301E0F229D172C66351017D5281778A3916232D12F4455C328F45F6C5FE1502",
            "ADA88E957267A48B548E1524B3EED9890AB99DD1839D5A35952F05B55078511A",
            "7DDEF098FF1C2D0E53756E89CC57B1A00A89C32A4A7E623686454D619F3214AD",
            "96051980458DAD86719F195072DA4BD34EEBD07A80D647EBB50BBBB0626E5565",
            "026D9A5C896AF1E590E4BD8E42F1EC4788C8210198007D79C5051F8792716DD9",
            "20B3FB6654B4422E7F7327EBC79BA29AC1F4E5366A12A962992E94E516070901",
            "1A4F7F23564AFEBC8C18D080A4757B16958C15FCAB513C9E3A1F0A67E565F67C",
            "164DEA3A175E742D2622C8CCA81B6808B07FF7D70F4119D23B389DBFF498D977",
            "B99BD633B8AAB91211162B3EEBF5021BB8C182CEC8FCD9AC051371F8CECB6DEA",
            "0BD39BC602A1F3889793636425A88249C4BA8F3463D91F4BDC64687FAC68A591",
            "B6650CFBBBBD753031277695F633D4271DD5CEEA4C948C73950E3A41168A7CB5",
            "3179C578A54C54FAA7F6A9D283C321574DAC50DD2C071405AF5F3363EAAA063E",
            "66909943C30BDCEA8F8BC47BD3B719093EEED4D11715B94CB120FB4F4330D815",
            "Incident_20260815T124823Z-67c989ee_v006",
            'snapshot["file_count"] != 33',
            '"operation": "MOVE_DIRECTORY_ONLY__NO_DELETE"',
            '"v006": {',
            'declared != object_hash(bound)',
            'actual_disk != expected_disk',
        ):
            self.assertIn(token, self.v007_recovery_preparer)
        for forbidden in (
            ".unlink(", ".rmdir(", "shutil.rmtree", "os.remove(",
            "import unreal", "subprocess", "copy2(", "replace_existing",
        ):
            self.assertNotIn(forbidden, self.v007_recovery_preparer)

        for token in (
            'REFLECTED_MATERIAL_INPUT_NAMES_BY_CLASS',
            '"MaterialExpressionLinearInterpolate": ["A", "B", "Alpha"]',
            '"MaterialExpressionMultiply": ["A", "B"]',
            '"MaterialExpressionClamp": ["None", "Min", "Max"]',
            '"MaterialExpressionDotProduct": ["A", "B"]',
            'if type(value) is not str:',
            'if value == "":',
            'return "" if value == "None" else value',
            'reflected_names != expected_reflected_names',
            'if len(set(names)) != len(names):',
            'list(clamp_raw) != ["", "Min", "Max"]',
            'normalized_luminance = clamp_raw[""]',
            'clamp_links[""]',
            'unnamed_material_input_canonicalization_required") is not True',
            'raw_none_input_names_forbidden_in_graph_evidence") is not True',
            'EXPECTED_V006_FAILED_RUN_ID = "20260815T124823Z-67c989ee"',
        ):
            self.assertIn(token, self.runtime)
        self.assertEqual(
            self.runtime.count("get_material_expression_input_names(expression)"), 1)
        self.assertNotIn(
            "[str(value) for value in\n             unreal.MaterialEditingLibrary.get_material_expression_input_names",
            self.runtime,
        )
        self.assertIn(
            'connect_nodes(normalized_luminance, "", detail_clamp, "",', importer)
        self.assertNotIn(
            'connect_nodes(normalized_luminance, "", detail_clamp, "None",', importer)
        self.assertNotIn(
            'connect_nodes(normalized_luminance, "", detail_clamp, "Input",', importer)
        self.assertNotIn("unreal.SystemLibrary.quit_editor()", importer)
        self.assertNotIn("unreal.SystemLibrary.quit_editor()", validator)

        for token in (
            "literal Python string `\"None\"`",
            "exact class-specific reflected order",
            "duplicate canonical names are rejected",
            "Raw empty strings are rejected",
            "all five existing quarantines",
            "Recovery_v007",
            "MOVE-only",
            "post-exit all-file namespace closure",
        ):
            self.assertIn(token, self.v007_recovery_doc)
        for token in (
            "RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V009_ONCE",
            "cairnwell_2040_runtime_v001_recovery_v009_contract.json",
            "prepare_cairnwell_2040_runtime_v001_recovery_v009.py",
            "Incident_20260815T124823Z-67c989ee_v006",
            "Recovery_v009",
            "quarantine_receipt_v009.json",
            "v006_import_failure_sha256",
            "unnamed_material_input_canonicalization_required",
            "raw_none_input_names_forbidden_in_graph_evidence",
            "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_UNREAL_IMPORT_LANE",
            "$ActualDiskPaths.Count -ne 11",
        ):
            self.assertIn(token, runner)

        self.assertEqual(V007_RECOVERY_CONTRACT.stat().st_size, 98751)
        self.assertEqual(V007_RECOVERY_CONTRACT_SHA.stat().st_size, 123)
        digest = hashlib.sha256(V007_RECOVERY_CONTRACT.read_bytes()).hexdigest().upper()
        self.assertEqual(
            digest, "7271F549ADF301C078636C408B49C5998CE8882A07FB999EF730CB0B97F7698F")
        self.assertEqual(
            hashlib.sha256(V007_RECOVERY_CONTRACT_SHA.read_bytes()).hexdigest().upper(),
            "ECC793B9319E935EC29762420421292828B7ADF7C0DBBC93022C3154298F8508")
        self.assertEqual(
            V007_RECOVERY_CONTRACT_SHA.read_text(encoding="ascii").split()[0].upper(),
            digest,
        )
        payload = json.loads(V007_RECOVERY_CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["$schema"],
            "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v7",
        )
        self.assertEqual(payload["status"], (
            "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V007__"
            "READY_FOR_ONE_SHOT_QUARANTINE_AND_TWO_PROCESS_IMPORT"))
        chain = dict(payload["incident_chain"])
        declared = chain.pop("binding_sha256")
        recomputed = hashlib.sha256(
            json.dumps(chain, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest().upper()
        self.assertEqual(declared, recomputed)
        self.assertEqual(payload["lane"]["file_count"], 33)
        self.assertEqual(len(payload["partial_packages"]), 11)
        self.assertEqual(payload["prior_quarantines"]["v005_partial_packages"]["file_count"], 11)
        authority = payload["material_input_name_canonicalization"]
        self.assertEqual(authority["reflected_raw_name"], "None")
        self.assertEqual(authority["canonical_graph_name"], "")
        self.assertEqual(len(authority["engine_sources"]), 10)
        self.assertFalse(authority["semantic_gates_relaxed"])
        self.assertFalse(V007_RECOVERY_AUDIT_ROOT.exists())
        self.assertTrue(V006_QUARANTINE.is_dir())

    def test_stale_recovery_v008_preserves_v007_and_exact_prior_all_file_closures(self) -> None:
        compile(self.v008_recovery_preparer, str(V008_RECOVERY_PREPARER), "exec")
        runner = RUNNER.read_text(encoding="utf-8")
        for token in (
            'V007_CONTRACT_BYTES = 98751',
            '7271F549ADF301C078636C408B49C5998CE8882A07FB999EF730CB0B97F7698F',
            'V007_SIDECAR_BYTES = 123',
            'ECC793B9319E935EC29762420421292828B7ADF7C0DBBC93022C3154298F8508',
            'STALE__UNEXECUTED_V007_PRELIMINARY__SUPERSEDED_BY_V008_EXACT_CLOSURE',
            'recovery_v007_result_root_absent_at_freeze',
            'v006_quarantine_absent_at_freeze',
            'exact_prior_all_file_closures',
            'expected_paths != actual_paths',
            'INCIDENT_FILE_COUNTS =',
            '"v001": 5, "v002": 6, "v003": 6, "v004": 6, "v005": 6, "v006": 6',
            'QUARANTINE_FILE_COUNTS =',
            '"v001": 4, "v002": 7, "v003": 11, "v004": 11, "v005": 11',
            'snapshot["file_count"] != 37',
            'payload.get("lane") != expected_lane',
            'payload.get("incident_chain") != v007["incident_chain"]',
            'payload.get("partial_packages") != v007["partial_packages"]',
            'payload.get("result_topology") != result_topology()',
            'payload.get("policy") != expected_policy',
            '"operation": "MOVE_DIRECTORY_ONLY__NO_DELETE"',
            'actual_disk != expected_disk',
            'Recovery_v008',
        ):
            self.assertIn(token, self.v008_recovery_preparer)
        for forbidden in (
            ".unlink(", ".rmdir(", "shutil.rmtree", "os.remove(",
            "import unreal", "subprocess", "copy2(", "replace_existing",
        ):
            self.assertNotIn(forbidden, self.v008_recovery_preparer)

        for token in (
            'EXPECTED_V007_PRELIMINARY_RESULT_ROOT',
            'EXPECTED_V006_QUARANTINE_ROOT',
            'EXPECTED_PRIOR_INCIDENT_ROOTS',
            'EXPECTED_PRIOR_INCIDENT_FILE_COUNTS',
            'EXPECTED_PRIOR_QUARANTINE_ROOTS',
            'EXPECTED_PRIOR_QUARANTINE_FILE_COUNTS',
            'preliminary.get("recovery_v007_result_root")',
            'preliminary.get("v006_quarantine_root")',
            'verify_exact_directory_snapshot',
            'snapshot.get("root") != EXPECTED_PRIOR_INCIDENT_ROOTS[version]',
            'snapshot.get("root") != EXPECTED_PRIOR_QUARANTINE_ROOTS[version]',
            '"MaterialExpressionClamp": ["None", "Min", "Max"]',
            'return "" if value == "None" else value',
            'if len(set(names)) != len(names):',
            'list(clamp_raw) != ["", "Min", "Max"]',
        ):
            self.assertIn(token, self.runtime)

        for token in (
            'RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V009_ONCE',
            'cairnwell_2040_runtime_v001_recovery_v009_contract.json',
            'prepare_cairnwell_2040_runtime_v001_recovery_v009.py',
            'Recovery_v009',
            'quarantine_receipt_v009.json',
            'exact_prior_all_file_closures_required',
            'stale_preliminary_v007',
            'stale_preliminary_v008',
            'Move-Item -LiteralPath $Destination -Destination $Quarantine',
            'FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_UNREAL_IMPORT_LANE',
            '$ActualDiskPaths.Count -ne 11',
        ):
            self.assertIn(token, runner)

        incident_roots = {
            FAILED_RUN: 5, V002_FAILED_RUN: 6, V003_FAILED_RUN: 6,
            V004_FAILED_RUN: 6, V005_FAILED_RUN: 6, V006_FAILED_RUN: 6,
        }
        quarantine_roots = {
            V001_QUARANTINE: 4, QUARANTINE: 7, V003_QUARANTINE: 11,
            V004_QUARANTINE: 11, V005_QUARANTINE: 11,
        }
        for root, expected_count in {**incident_roots, **quarantine_roots}.items():
            self.assertTrue(root.is_dir(), str(root))
            self.assertEqual(
                len([path for path in root.rglob("*") if path.is_file()]),
                expected_count,
                str(root),
            )
        self.assertFalse(V007_RECOVERY_AUDIT_ROOT.exists())
        self.assertFalse(V008_RECOVERY_AUDIT_ROOT.exists())
        self.assertTrue(V006_QUARANTINE.is_dir())

        for token in (
            "provisional v007 contract",
            "preserved byte-exact as stale, unexecuted chronology evidence",
            "literal Python string `None`",
            "Only after that exact raw gate",
            "incident roots v001–v006",
            "quarantine roots q1–q5",
            "MOVE_DIRECTORY_ONLY__NO_DELETE",
            "natural `-ExecutePythonScript` exit only",
            "RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V008_ONCE",
        ):
            self.assertIn(token, self.v008_recovery_doc)

        self.assertEqual(V008_RECOVERY_CONTRACT.stat().st_size, 133651)
        self.assertEqual(V008_RECOVERY_CONTRACT_SHA.stat().st_size, 123)
        digest = hashlib.sha256(V008_RECOVERY_CONTRACT.read_bytes()).hexdigest().upper()
        self.assertEqual(
            digest, "6E8E2D0E6D40A16CFF1AF5BEF31A00498C51DEADADF6CE0901D537285E5E49BD")
        self.assertEqual(
            hashlib.sha256(V008_RECOVERY_CONTRACT_SHA.read_bytes()).hexdigest().upper(),
            "D082F35B000CEC489991F8F481AACA78580CCB1326356F468612C4C99CBA054F")
        payload = json.loads(V008_RECOVERY_CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["$schema"],
            "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v8",
        )
        self.assertEqual(payload["status"], (
            "FROZEN__CAIRNWELL_2040_RUNTIME_V001_INCIDENT_CHAINED_RECOVERY_V008__"
            "READY_FOR_ONE_SHOT_QUARANTINE_AND_TWO_PROCESS_IMPORT"))
        self.assertEqual(payload["lane"]["file_count"], 37)
        self.assertEqual(len(payload["partial_packages"]), 11)
        self.assertEqual(
            payload["stale_preliminary_v007"]["contract"]["sha256"],
            "7271F549ADF301C078636C408B49C5998CE8882A07FB999EF730CB0B97F7698F",
        )
        self.assertEqual(
            payload["stale_preliminary_v007"]["sidecar"]["sha256"],
            "ECC793B9319E935EC29762420421292828B7ADF7C0DBBC93022C3154298F8508",
        )
        closures = payload["exact_prior_all_file_closures"]
        self.assertEqual(
            {key: row["file_count"] for key, row in closures["incident_roots"].items()},
            {"v001": 5, "v002": 6, "v003": 6, "v004": 6, "v005": 6, "v006": 6},
        )
        self.assertEqual(
            {key: row["file_count"] for key, row in closures["quarantine_roots"].items()},
            {"v001": 4, "v002": 7, "v003": 11, "v004": 11, "v005": 11},
        )
        chain = dict(payload["incident_chain"])
        declared = chain.pop("binding_sha256")
        self.assertEqual(
            declared,
            hashlib.sha256(json.dumps(
                chain, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest().upper(),
        )

    def test_recovery_v009_requires_one_shared_no_write_full_payload_preflight(self) -> None:
        compile(self.v009_recovery_preparer, str(V009_RECOVERY_PREPARER), "exec")
        importer = IMPORTER.read_text(encoding="utf-8")
        validator = VALIDATOR.read_text(encoding="utf-8")
        runner = RUNNER.read_text(encoding="utf-8")
        for token in (
            'V008_CONTRACT_BYTES = 133651',
            '6E8E2D0E6D40A16CFF1AF5BEF31A00498C51DEADADF6CE0901D537285E5E49BD',
            'V008_SIDECAR_BYTES = 123',
            'D082F35B000CEC489991F8F481AACA78580CCB1326356F468612C4C99CBA054F',
            'EXPECTED_IMPORT_FAILURES =',
            'STALE__UNEXECUTED_V008_PRELIMINARY__SUPERSEDED_BY_V009_',
            'POST_FREEZE_PRE_QUARANTINE_CONSTANT_LOOKUP_FAILED_BEFORE_ANY_MOVE_OR_UE',
            '"Scripts/prepare_cairnwell_2040_runtime_v001_recovery_v008.py"',
            'snapshot["file_count"] != 41',
            'def build_candidate_payload(',
            'def validate_candidate_payload(',
            'def dry_build_payload(',
            'def candidate_generated_utc(',
            'generated != candidate_generated_utc(state)',
            'validate_candidate_payload(payload, state)',
            'validate_candidate_payload(round_trip, state)',
            'validate_candidate_payload(json.loads(serialized), state)',
            'validate_candidate_payload(payload, state)',
            'group.add_argument("--dry-build", action="store_true")',
            'PASS__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_NO_WRITE_FULL_PAYLOAD_PREFLIGHT',
            'authority_state(require_unmoved_v006_destination=True)',
            'def authority_state(require_unmoved_v006_destination: bool = False)',
            'prior.verify_all_inherited_engine_sources(v007)',
            'payload != expected',
            '"operation": "MOVE_DIRECTORY_ONLY__NO_DELETE"',
            'actual_disk != expected_disk',
        ):
            self.assertIn(token, self.v009_recovery_preparer)
        self.assertEqual(self.v009_recovery_preparer.count('newline="\\n"'), 2)
        for forbidden in (
            ".unlink(", ".rmdir(", "shutil.rmtree", "os.remove(",
            "import unreal", "subprocess", "copy2(", "replace_existing",
        ):
            self.assertNotIn(forbidden, self.v009_recovery_preparer)
        self.assertEqual(
            write_text_receivers(self.v009_recovery_preparer), ["OUTPUT", "OUTPUT_SHA"])

        for token in (
            'cairnwell_2040_runtime_v001_recovery_v009_contract.json',
            'RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V009_ONCE',
            'EXPECTED_V008_PRELIMINARY_CONTRACT_SHA256',
            'EXPECTED_V008_PRELIMINARY_SIDECAR_SHA256',
            'EXPECTED_V008_PRELIMINARY_RESULT_ROOT',
            'stale_preliminary_v008',
            'no_write_full_candidate_payload_preflight_required',
            'lineboss/cairnwell-2040-runtime-v001/recovery-contract/v9',
            'recovery v009 prepared lane',
            'lineboss/audit/cairnwell-2040-runtime-v001/recovery-v009/quarantine/v9',
        ):
            self.assertIn(token, self.runtime)
        for source in (importer, validator, runner):
            self.assertIn("V009", source.upper())
            self.assertNotIn("recovery-v008/", source)
        self.assertIn("Destination topology is process-specific", self.runtime)
        self.assertNotIn(
            'if DEST_DISK.exists():\n        fail("recovery v009 destination was not moved',
            self.runtime,
        )
        self.assertNotIn('if (PROJECT / source_path).exists():', self.runtime)
        self.assertIn(
            "if lane.DEST_DISK.exists() or lane.library.does_directory_exist(lane.DEST):",
            importer,
        )
        self.assertIn('lane.fail("fresh destination already exists; overwrite/reimport forbidden")',
                      importer)
        self.assertIn('for package in baseline["destination"]["expected_package_paths"]:',
                      importer)
        self.assertIn('if lane.library.does_asset_exist(package):', importer)
        self.assertIn("baseline = lane.load_baseline()", validator)
        for token in (
            'RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V009_ONCE',
            'cairnwell_2040_runtime_v001_recovery_v009_contract.json',
            'prepare_cairnwell_2040_runtime_v001_recovery_v009.py',
            'Recovery_v009',
            'quarantine_receipt_v009.json',
            'stale_v008_pair_must_remain_byte_exact',
            'no_write_full_candidate_payload_preflight_required',
            'FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_UNREAL_IMPORT_LANE',
        ):
            self.assertIn(token, runner)

        for token in (
            "Both v007 and v008 contract/sidecar pairs remain byte-exact",
            "Required no-write preflight",
            "constructs the entire candidate payload in memory",
            "--dry-build",
            "same full-payload validator",
            "byte-identical payloads",
            "fourteen distinct installed UE 5.8 source authorities",
            "Recovery_v009",
            "RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V009_ONCE",
        ):
            self.assertIn(token, self.v009_recovery_doc)
        self.assertFalse(V007_RECOVERY_AUDIT_ROOT.exists())
        self.assertFalse(V008_RECOVERY_AUDIT_ROOT.exists())
        self.assertTrue(V009_RECOVERY_AUDIT_ROOT.is_dir())
        self.assertTrue(V006_QUARANTINE.is_dir())
        paired = [V009_RECOVERY_CONTRACT.exists(), V009_RECOVERY_CONTRACT_SHA.exists()]
        self.assertIn(sum(paired), (0, 2))
        if all(paired):
            digest = hashlib.sha256(V009_RECOVERY_CONTRACT.read_bytes()).hexdigest().upper()
            self.assertEqual(
                V009_RECOVERY_CONTRACT_SHA.read_text(encoding="ascii").split()[0].upper(),
                digest,
            )
            payload = json.loads(V009_RECOVERY_CONTRACT.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["$schema"],
                "lineboss/cairnwell-2040-runtime-v001/recovery-contract/v9",
            )
            self.assertEqual(payload["lane"]["file_count"], 41)
            self.assertEqual(len(payload["partial_packages"]), 11)
            self.assertEqual(
                payload["stale_preliminary_v008"]["contract"]["sha256"],
                "6E8E2D0E6D40A16CFF1AF5BEF31A00498C51DEADADF6CE0901D537285E5E49BD",
            )
            self.assertTrue(payload["policy"][
                "no_write_full_candidate_payload_preflight_required"])

    def test_runtime_helper_rejects_identity_provenance_and_package_drift(self) -> None:
        compile(self.runtime, str(RUNTIME), "exec")
        self.assertEqual(literal_assignment(self.runtime, "DEST"), EXPECTED_NAMESPACE)
        self.assertEqual(
            literal_assignment(self.runtime, "EXPECTED_BASELINE_STATUS"),
            "FROZEN__CAIRNWELL_2040_RUNTIME_V001_PROJECT_BASELINE",
        )
        for token in (
            'destination.get("expected_mesh_count") != 4',
            'destination.get("expected_texture_count") != 3',
            'destination.get("expected_material_count") != 4',
            'destination.get("expected_package_count") != 11',
            'selected_version != "v005"',
            'selected_candidate != "ProductionCandidate_v005"',
            'manifest_relative != EXPECTED_MANIFEST_RELATIVE',
            'paint_mask.get("status") != EXPECTED_PAINT_MASK_STATUS',
            'paint_mask.get("v006_mask_reused") is not False',
            'int(paint_mask.get("false_positive_fragment_count", -1)) != 0',
            'supersession.get("status") != EXPECTED_SUPERSESSION_STATUS',
            'supersession.get("historical_marker_preserved_byte_exact") is not True',
            'supersession.get("supersedes_historical_marker_without_deletion") is not True',
            'amendment.get("status") != EXPECTED_FREEZE_AMENDMENT_STATUS',
            'amendment_record.get("sha256") != EXPECTED_FREEZE_AMENDMENT_SHA256',
            'stale_receipt.get("sha256") != EXPECTED_STALE_FREEZE_RECEIPT_SHA256',
            'current_supersession.get("sha256") != EXPECTED_CURRENT_SUPERSESSION_SHA256',
            'amendment.get("no_other_changed_files") is not True',
            'any("ProductionCandidate_v006" in path for path in imported_source_paths)',
            "require_engine_entry_bootstrap_world",
            'path != "/Engine/Maps/Entry.Entry"',
            "LoadLevelAtStartup=None",
            '"meshy-derived" not in provenance_description.casefold()',
            '"native" in provenance_description.casefold()',
            'payload.get("policy", {}).get("overwrite_reimport_delete_authorized") is not False',
            "destination package count is not exact",
            "destination package path closure is not exact",
            "runtime mesh/material/texture dependency closure is not exact",
            "persisted_asset_registry_dependency_closure_verified",
        ):
            self.assertIn(token, self.runtime)
        for forbidden in ("delete_asset(", "delete_directory(", "load_level(", "save_current_level("):
            self.assertNotIn(forbidden, self.runtime)

    def test_contract_consumers_require_exact_v005_winner_and_manual_mask(self) -> None:
        exact_status = "FROZEN__APPROVED_CAIRNWELL_V005_WINNER__READY_FOR_BASELINE"
        rejected_neutral_status = "FROZEN__APPROVED_CAIRNWELL_FINAL_AUTHORITY__READY_FOR_BASELINE"
        for source in (self.contract_preparer, self.baseline_preparer, self.runtime):
            self.assertIn(exact_status, source)
            self.assertNotIn(rejected_neutral_status, source)
        self.assertIn("ProductionCandidate_v005", self.runtime)
        self.assertIn("MANIFEST_v005.json", self.runtime)
        self.assertIn("APPROVED__MANUALLY_AUTHORED_V005_BODY_PAINT_MASK", self.runtime)
        self.assertIn("APPROVED__V005_MANUAL_MASK_SUPERSEDES_HISTORICAL", self.runtime)

    def test_optional_importer_is_guarded_if_present(self) -> None:
        if not IMPORTER.is_file():
            return
        source = IMPORTER.read_text(encoding="utf-8")
        compile(source, str(IMPORTER), "exec")
        for forbidden in (
            "delete_asset(",
            "delete_directory(",
            "load_level(",
            "save_current_level(",
            '"replace_existing": True',
            '"replace_existing_settings": True',
        ):
            self.assertNotIn(forbidden, source)
        for token in (
            "replace_existing",
            "False",
            "import_materials",
            "import_textures",
            "auto_generate_collision",
            "build_nanite",
            "import_lod",
            "imported_lod_index != lod_index",
            "finally:",
            "PARTIAL_ARTIFACTS_PRESERVED_FOR_EXPLICIT_REVIEW",
        ):
            self.assertIn(token, source)

    def test_optional_validator_is_fresh_process_read_only_if_present(self) -> None:
        if not VALIDATOR.is_file():
            return
        source = VALIDATOR.read_text(encoding="utf-8")
        compile(source, str(VALIDATOR), "exec")
        for forbidden in (
            "save_loaded_asset(",
            "save_asset(",
            "delete_asset(",
            "delete_directory(",
            "AssetImportTask(",
            "import_lod(",
            "load_level(",
            "save_current_level(",
        ):
            self.assertNotIn(forbidden, source)
        for token in (
            "import_pid",
            "os.getpid()",
            "namespace_before",
            "namespace_after",
            "registry_before",
            "registry_after",
            "package_hashes",
            "validate_all_assets",
            "require_persisted_dependencies=True",
        ):
            self.assertIn(token, source)

    def test_optional_runner_uses_two_fresh_no_compile_processes_if_present(self) -> None:
        if not RUNNER.is_file():
            return
        source = RUNNER.read_text(encoding="utf-8")
        calls = re.findall(
            r"(?m)^\s*\$Summary\.(?:import|validation)_process\s*=\s*Invoke-GuardedEditor\s+\$",
            source,
        )
        self.assertEqual(len(calls), 2)
        for token in (
            "function Invoke-GuardedEditor",
            "Start-Process -FilePath $Editor",
            "-NoCompile",
            "-NullRHI",
            "Assert-NoProcesses",
            "RECOVER_QUARANTINED_CAIRNWELL_2040_RUNTIME_V001_V009_ONCE",
            "Incident-bound recovery contract identity/safety drift",
            "persisted_asset_registry_dependency_closure_verified",
            "$EngineEntry = '/Engine/Maps/Entry'",
            "LoadLevelAtStartup=None",
            "-NoAutoSave",
            "-NoSaveOnExit",
            "Get-PostExitPackageHashes",
            "--verify-pre-quarantine",
            "--verify-post-quarantine",
            "--verify-post-import",
            "Move-Item -LiteralPath $Destination -Destination $Quarantine",
            "quarantine_receipt_v009.json",
            "MOVE_DIRECTORY_ONLY__NO_DELETE",
            "Get-LBFileEvidenceWithBoundedReadRetry",
            "TimeoutMilliseconds 15000",
            "redirected_log_read_open_retry",
            "strict exit/log gate",
            "Fatal error:",
            "Assertion failed:",
            "Unhandled Exception:",
            "Ensure condition failed",
            "ModeManager",
            "ModeManagerInteractiveToolsContext",
            "Object is not packaged: ModeManagerInteractiveToolsContext None",
            "post_exit_package_sha256",
            "v001_import_failure_sha256",
            "v002_import_failure_sha256",
            "v003_import_failure_sha256",
            "v004_import_failure_sha256",
            "v005_import_failure_sha256",
            "v006_import_failure_sha256",
            "incident_chain_sha256",
            "recovery_contract_sha256",
            "FAIL_CLOSED__CAIRNWELL_2040_RUNTIME_V001_RECOVERY_V009_UNREAL_IMPORT_LANE",
            "$ActualDiskPaths.Count -ne 11",
            "Post-exit namespace all-file closure is not the exact eleven uassets",
        ):
            self.assertIn(token, source)
        self.assertEqual(
            source.count("Move-Item -LiteralPath $Destination -Destination $Quarantine"), 1)
        for forbidden in (
            "Remove-Item", "del ", "rmdir ", "rd /s", "erase ",
            "AcceptKnownCrash", "ignore exit", "whitelist fatal",
        ):
            self.assertNotIn(forbidden, source)
        for redirected_path in ("$LogPath", "$StdoutPath", "$StderrPath"):
            self.assertNotRegex(
                source,
                rf"Get-(?:FileHash|Content)[^\n]*{re.escape(redirected_path)}",
            )
        self.assertNotIn("Build.bat", source)


if __name__ == "__main__":
    unittest.main()

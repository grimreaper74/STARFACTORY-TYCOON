"""Offline contract for articulated IN-01 controller/save integration."""

import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
HEADER = PROJECT / "Source" / "LineBossCarFactory" / "LBInboundDeliveryController.h"
SOURCE = PROJECT / "Source" / "LineBossCarFactory" / "LBInboundDeliveryController.cpp"
CAMPAIGN = PROJECT / "Source" / "LineBossCarFactory" / "LBPressShopCampaignController.cpp"


class InboundArticulatedControllerIntegrationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.campaign = CAMPAIGN.read_text(encoding="utf-8")

    def test_save_schema_v7_persists_independent_hitch_yaw(self):
        self.assertIn("int32 SaveVersion = 7;", self.header)
        self.assertIn("float TrailerRelativeYawDegrees = 0.0f;", self.header)
        self.assertIn(
            "State.TrailerRelativeYawDegrees = Carrier->GetTrailerRelativeYawDegrees();",
            self.source,
        )
        self.assertIn("State.SaveVersion > 7", self.source)
        self.assertIn("InboundDelivery.SaveVersion > 7", self.campaign)

    def test_route_planner_uses_full_parked_articulated_envelope(self):
        self.assertIn('#include "LBMobileRoutePlanner.h"', self.source)
        self.assertIn(
            "Settings.VehicleHalfExtentCm = FVector2D(825.0f, 127.5f);",
            self.source,
        )
        self.assertIn("Settings.CornerRadiusCm = 650.0f;", self.source)
        self.assertIn("Settings.MaximumCurveStepDegrees = 6.0f;", self.source)
        self.assertIn("BuildClearanceAwarePath", self.source)
        self.assertIn("ARTICULATED INBOUND ROUTE REJECTED AN UNROUNDED CORNER", self.source)
        self.assertIn("AdvanceTractorPoseAndSolveTrailer(NextPose", self.source)

    def test_attached_cargo_follows_trailer_without_double_translation(self):
        self.assertIn("GetTrailerCargoRoot()", self.source)
        self.assertIn("FAttachmentTransformRules::KeepWorldTransform", self.source)
        self.assertIn(
            "TrailerCoilActors[Index]->GetAttachParentActor() != LorryActor",
            self.source,
        )
        hook = self.source.index(
            "if (Phase == ELBInboundDeliveryPhase::HookEngage)"
        )
        detach = self.source.index(
            "DetachActiveCoilFromArticulatedTrailer();", hook
        )
        carry = self.source.index(
            "ApplyCarriedCoilPose(HookActor->GetActorLocation());", hook
        )
        self.assertLess(detach, carry)

    def test_ordinary_lorry_interpolation_is_still_the_fallback(self):
        self.assertIn("if (GetArticulatedLorry())", self.source)
        self.assertIn(
            "bDocked = MoveActorTo(LorryActor, LorryDockPoint,",
            self.source,
        )


if __name__ == "__main__":
    unittest.main()

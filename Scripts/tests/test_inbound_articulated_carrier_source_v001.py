"""Offline source contract for the IN-01A/IN-01B native carrier authority."""

import re
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
HEADER = PROJECT / "Source" / "LineBossCarFactory" / "LBInboundArticulatedCarrierActor.h"
SOURCE = PROJECT / "Source" / "LineBossCarFactory" / "LBInboundArticulatedCarrierActor.cpp"


class InboundArticulatedCarrierSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.source = SOURCE.read_text(encoding="utf-8")

    def constant(self, name):
        match = re.search(
            r"static constexpr float\s+{}\s*=\s*(-?[0-9.]+)f;".format(re.escape(name)),
            self.header,
        )
        self.assertIsNotNone(match, "missing contract constant {}".format(name))
        return float(match.group(1))

    def test_exact_registered_dimensions_are_encoded_in_centimetres(self):
        self.assertEqual(self.constant("TractorLengthCm"), 480.0)
        self.assertEqual(self.constant("TractorWidthCm"), 255.0)
        self.assertEqual(self.constant("TractorHitchLocalXCm"), 215.0)
        self.assertEqual(self.constant("TrailerLengthCm"), 1220.0)
        self.assertEqual(self.constant("TrailerWidthCm"), 255.0)
        self.assertEqual(self.constant("TrailerHitchLocalXCm"), -585.0)
        self.assertEqual(self.constant("ParkedEnvelopeLengthCm"), 1650.0)
        self.assertEqual(self.constant("ParkedCentreSeparationCm"), 800.0)
        self.assertEqual(self.constant("HitchOverlapCm"), 50.0)

    def test_two_hidden_proxies_retain_collision_authority(self):
        self.assertIn('CreateDefaultSubobject<UBoxComponent>(TEXT("IN01A_TractorAuthorityProxy"))', self.source)
        self.assertIn('CreateDefaultSubobject<UBoxComponent>(TEXT("IN01B_TrailerAuthorityProxy"))', self.source)
        self.assertIn('SetCollisionProfileName(TEXT("BlockAllDynamic"))', self.source)
        self.assertIn('SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics)', self.source)
        self.assertIn('SetCanEverAffectNavigation(false)', self.source)
        self.assertIn('SetHiddenInGame(true, true)', self.source)

    def test_native_yaw_hitch_and_independent_visual_anchors_are_present(self):
        self.assertIn('CreateDefaultSubobject<USceneComponent>(TEXT("PVT_IN01_TractorHitchYaw"))', self.source)
        self.assertIn('CreateDefaultSubobject<USceneComponent>(TEXT("PVT_IN01_TrailerYaw"))', self.source)
        self.assertIn('TrailerYawPivot->SetupAttachment(TractorHitch)', self.source)
        self.assertIn('TrailerBodyCentre->SetupAttachment(TrailerYawPivot)', self.source)
        self.assertIn('IN01A_TractorPresentationAnchor', self.source)
        self.assertIn('IN01B_TrailerPresentationAnchor', self.source)
        self.assertIn('IN01B_SeparateCargoRoot', self.source)

    def test_solver_fails_closed_before_mutation(self):
        large_step = self.source.index("SOLVER STEP EXCEEDS TUNNEL-SAFE LIMIT")
        jackknife = self.source.index("STEP WOULD JACK-KNIFE THE TRAILER")
        mutation = self.source.index(
            "SetActorTransform(NewTractorWorldTransform", jackknife
        )
        self.assertLess(large_step, mutation)
        self.assertLess(jackknife, mutation)
        self.assertIn("PreviousTrailerCentre - NewHitch", self.source)
        self.assertIn("FMath::FindDeltaAngleDegrees", self.source)

    def test_save_validation_can_check_yaw_without_mutating(self):
        self.assertIn("IsTrailerRelativeYawWithinLimits", self.header)
        self.assertIn(
            "return FMath::IsFinite(CandidateRelativeYawDegrees)", self.source
        )

    def test_actor_does_not_claim_inventory_or_delivery_authority(self):
        combined = self.header + self.source
        for forbidden in (
            "ReleaseOutputUnit",
            "AcceptInputUnit",
            "StartDelivery",
            "ActiveCoilId",
            "CompletedDeliveries",
        ):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()

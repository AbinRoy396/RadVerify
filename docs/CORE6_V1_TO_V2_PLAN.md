# Core6 v1 to v2 Plan

## Locked v1 scope (current)
- brain_skull
- brain_ventricles
- brain_cerebellum
- biometry_abdomen
- biometry_femur
- heart_four_chamber_view

## v2 expansion classes
- face_profile
- face_nasal_bone
- face_lips
- organs_stomach
- limbs_arms
- limbs_legs
- optional later: organs_kidneys, organs_bladder, limbs_hands, limbs_feet

## v2 data gates (must pass before training)
- No cross-split duplicate hashes.
- No cross-class duplicate hashes inside the same split.
- Minimum 300 clean images/class in train split (target 600+).
- Label audit sample: 50 random images/class with >=95% reviewer agreement.

## v2 model gates (must pass before promotion)
- Validation accuracy >= v1 + 5 points.
- Validation macro F1 >= v1 + 5 points.
- No class with F1 < 0.30 in validation.
- Same metrics hold on test split (no regression vs v1).

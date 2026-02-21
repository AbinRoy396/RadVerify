# Labeling Checklist (Priority Order)

This checklist prioritizes labeling for maximum clinical value and model impact.

## Priority 1 - Core Planes (most available, highest impact)
- brain_skull
- brain_ventricles
- brain_cerebellum
- biometry_abdomen
- biometry_femur
- heart_four_chamber_view

## Priority 2 - High-Value Anatomy
- face_profile
- face_nasal_bone
- face_lips
- spine_vertebrae
- spine_skin_coverage

## Priority 3 - Organs
- organs_stomach
- organs_kidneys
- organs_bladder

## Priority 4 - Limbs
- limbs_arms
- limbs_legs
- limbs_hands
- limbs_feet

## Priority 5 - Maternal/Placental
- maternal_placenta
- maternal_amniotic_fluid
- maternal_umbilical_cord

## Suggested Minimum Counts (starting point)
- Priority 1: 300-500 images each
- Priority 2: 200-300 images each
- Priority 3: 150-250 images each
- Priority 4: 150-250 images each
- Priority 5: 150-250 images each

## Notes
- Keep labels consistent with `data/structure_dataset/labels.json`.
- If a class is hard to source, start with 50-100 images and grow later.
- Always keep a balanced train/validation split (80/20 recommended).

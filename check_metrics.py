import json

with open('models/validation_metrics.json') as f:
    d = json.load(f)

v = d['validation']
print(f"=== VALIDATION RESULTS ===")
print(f"Accuracy:  {v['accuracy']*100:.1f}%")
print(f"Macro F1:  {v['macro_f1']:.4f}")
print(f"Samples:   {v['samples']}")
print()
print("Per-class breakdown:")
for k, m in v['per_class'].items():
    print(f"  {k:25s}: P={m['precision']:.2f}  R={m['recall']:.2f}  F1={m['f1']:.2f}  n={m['support']}")

if d.get('test'):
    t = d['test']
    print(f"\n=== TEST RESULTS ===")
    print(f"Accuracy:  {t['accuracy']*100:.1f}%")
    print(f"Macro F1:  {t['macro_f1']:.4f}")

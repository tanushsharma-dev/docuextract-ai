import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path
from evaluation.metrics import compute_field_metrics, compute_line_item_f1, compute_arithmetic_accuracy
from app.extraction.pipeline import run_extraction_pipeline

def run_full_evaluation(golden_dir="data/golden", output_report="evaluation/reports/report.json"):
    golden_files = list(Path(golden_dir).glob("*.json"))
    predictions, ground_truths = [], []

    for gf in golden_files:
        with open(gf) as f:
            gt = json.load(f)
        image_path = gt.get("image_path")
        if not image_path or not os.path.exists(image_path):
            continue
        output_dir = f"./storage/eval/{gf.stem}"
        print(f"🔍 Evaluating: {gf.name}")
        result = run_extraction_pipeline(image_path, output_dir)
        pred = {k: v["value"] for k, v in result.get("fields", {}).items()}
        pred["subtotal"] = pred.get("subtotal")
        pred["tax"] = pred.get("tax")
        pred["line_items"] = result.get("line_items", [])
        predictions.append(pred)
        ground_truths.append(gt)

    field_metrics = compute_field_metrics(predictions, ground_truths)
    arithmetic_acc = compute_arithmetic_accuracy(predictions)
    f1s = [compute_line_item_f1(p.get("line_items", []), g.get("line_items", []))["f1"]
           for p, g in zip(predictions, ground_truths)]
    avg_f1 = sum(f1s) / len(f1s) if f1s else 0

    report = {
        "total_documents": len(predictions),
        "field_metrics": field_metrics,
        "avg_line_item_f1": round(avg_f1, 3),
        "arithmetic_accuracy": round(arithmetic_acc, 3)
    }

    Path(output_report).parent.mkdir(parents=True, exist_ok=True)
    with open(output_report, "w") as f:
        json.dump(report, f, indent=2)

    print("\n=== EVALUATION REPORT ===")
    print(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    run_full_evaluation()
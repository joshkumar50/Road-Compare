import csv
import json
import argparse


def load_labels(path):
    gt = []
    with open(path, newline='') as f:
        r = csv.DictReader(f)
        for row in r:
            gt.append({
                'element': row['element'],
                'issue_type': row['issue_type']
            })
    return gt


def load_pred(path):
    data = json.load(open(path))
    preds = [
        {'element': i['element'], 'issue_type': i['issue_type']}
        for i in data['issues']
    ]
    return preds


def precision_recall(gt, preds):
    gt_set = {(g['element'], g['issue_type']) for g in gt}
    pred_set = {(p['element'], p['issue_type']) for p in preds}
    tp = len(gt_set & pred_set)
    fp = len(pred_set - gt_set)
    fn = len(gt_set - pred_set)
    prec = tp / (tp + fp) if tp + fp > 0 else 0.0
    rec = tp / (tp + fn) if tp + fn > 0 else 0.0
    return prec, rec, tp, fp, fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--labels', default='sample_data/labels.csv')
    ap.add_argument('--results', default='artifacts_results.json')
    ap.add_argument('--out', default='artifacts_metrics.json')
    args = ap.parse_args()
    gt = load_labels(args.labels)
    preds = load_pred(args.results)
    prec, rec, tp, fp, fn = precision_recall(gt, preds)
    metrics = {
        'precision': round(prec, 3),
        'recall': round(rec, 3),
        'tp': tp,
        'fp': fp,
        'fn': fn,
    }
    print(metrics)
    json.dump(metrics, open(args.out, 'w'))


if __name__ == '__main__':
    main()






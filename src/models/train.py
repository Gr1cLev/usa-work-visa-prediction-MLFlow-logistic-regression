import joblib, yaml, mlflow, pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score

BASE = Path(__file__).resolve().parents[2]
PROC = BASE / "data" / "processed"
ART = BASE / "artifacts"
MLRUNS = BASE / "mlruns"
ART.mkdir(parents=True, exist_ok=True)
MLRUNS.mkdir(parents=True, exist_ok=True)

def load_cfg():
    cfg = yaml.safe_load((BASE / "configs" / "training.yaml").read_text())
    thr = yaml.safe_load((BASE / "configs" / "thresholds.yaml").read_text())
    return cfg, thr

def main():
    cfg, thr = load_cfg()
    df = pd.read_csv(PROC / "features.csv")
    y = df[cfg["target"]]
    X = df.drop(columns=[cfg["target"]])
    num_cols = cfg["numeric"]; cat_cols = cfg["categorical"]

    pre = ColumnTransformer([
        ("num", Pipeline(steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), num_cols),
        ("cat", Pipeline(steps=[("imputer", SimpleImputer(strategy="most_frequent")), ("ohe", OneHotEncoder(handle_unknown="ignore"))]), cat_cols)
    ])
    pipe = Pipeline([("prep", pre), ("clf", LogisticRegression(max_iter=200))])

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    mlflow.set_tracking_uri(MLRUNS.resolve().as_uri())
    mlflow.set_experiment("visa-lca")
    with mlflow.start_run():
        pipe.fit(Xtr, ytr)
        pred = pipe.predict(Xte)
        f1 = f1_score(yte, pred)
        mlflow.log_metric("f1", float(f1))
        mlflow.log_params({"model":"LogReg","test_size":0.2})
        joblib.dump({"model": pipe}, ART / "model.joblib")
        print(f"[Train] F1={f1:.3f}")
        if f1 < float(thr["min_f1"]):
            print(f"[WARN] F1 {f1:.3f} < threshold {thr['min_f1']} - review features/model.")

if __name__ == "__main__":
    main()

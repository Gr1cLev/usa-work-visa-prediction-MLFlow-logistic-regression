setup:
	pip install -r requirements.txt
ingest:
	python -m src.data.ingest
validate:
	python -m src.data.validate
features:
	python -m src.features.build_features
train:
	python -m src.models.train
eval:
	python -m src.models.evaluate
report:
	python -m src.monitoring.generate_report
serve:
	uvicorn src.serving.app:app --reload --port 8000
all: ingest validate features train eval report

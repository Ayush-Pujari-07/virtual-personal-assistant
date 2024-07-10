# Run both frontend and backend from this bash script

NUM_WORKERS=$(grep -c ^processor /proc/cpuinfo)

echo "Number of workers: $NUM_WORKERS"

exec uvicorn backend.main:app --host 0.0.0.0 --port 9000 --reload --workers $NUM_WORKERS &

exec streamlit run frontend/main.py
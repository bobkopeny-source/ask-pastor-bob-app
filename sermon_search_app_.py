# Install sqlite-utils (free)
pip install sqlite-utils

# Convert JSON to SQLite
sqlite-utils convert PASTOR_BOB_MERGED_DATABASE.json PASTOR_BOB_SERMONS.db \
  --table sermons \
  --pk id

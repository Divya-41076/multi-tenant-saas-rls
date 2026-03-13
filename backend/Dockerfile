FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0","--port", "8000"]

# ```

# ---

# ## Why This Order Matters

# We copy `requirements.txt` and install **before** copying code. This is a Docker caching trick:
# ```
# If code changes     → only re-runs step 5, 6, 7  (fast)
# If requirements change → re-runs step 3, 4, 5, 6, 7 (slower)
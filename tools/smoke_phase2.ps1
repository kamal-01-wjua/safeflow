cd D:\SafeFlow\safeflow

Write-Host "== Compose PS =="
docker compose -f .\infra\docker\docker-compose.yml ps

Write-Host "== Health/Ready =="
curl.exe -s http://localhost:8000/health
echo ""
curl.exe -s http://localhost:8000/ready
echo ""

Write-Host "== Produce test events =="
docker exec -it safeflow-risk-worker python /app/tools/produce_test_events.py

Write-Host "== DB latest alerts =="
docker exec -it safeflow-postgres psql -U safeflow -d safeflow -c "SELECT id, transaction_reference, risk_score_0_999, severity, created_at FROM alerts ORDER BY id DESC LIMIT 10;"

Write-Host "== API alerts + summary =="
curl.exe -s "http://localhost:8000/api/v1/alerts/?limit=10&offset=0"
echo ""
curl.exe -s "http://localhost:8000/api/v1/alerts/summary"
echo ""

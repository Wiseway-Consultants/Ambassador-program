docker run --name sfo-postgres \
  -e POSTGRES_DB=sfo_dev \
  -e POSTGRES_USER=sfo_user \
  -e POSTGRES_PASSWORD=sfo_pass \
  -p 5432:5432 \
  -d postgres:17
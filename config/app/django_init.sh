#!/usr/bin/env bash

# 清理所有 migrations
echo "====> Clean migrations <===="
find . -name "[0-9]*_*.py" -print | xargs rm -rfv
# 清理 pyc/ pyo 快取檔
echo "====> Clean Cache <===="
find . -name "*.py[co]" -print | xargs rm -rfv

echo "====> Sync db <===="
python manage.py makemigrations
python manage.py migrate


echo "====> Collect static <===="
python manage.py collectstatic --noinput

echo "====> Load fixtures <===="
python manage.py loaddata ./fixtures/box_data.json

echo "=================== Done ==============="

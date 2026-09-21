# قوانین ضدخطا

## قانون ۱: lowercase
همیشه نام پوشه با حرف کوچک
```bash
mkdir -p lowercase_name
```

## قانون ۲: mkdir قبل از loop
اول همه پوشه‌ها، بعد loop
```bash
mkdir -p dir/{a,b,c}
for i in a b c; do echo "x" > "dir/$i/file"; done
```

## قانون ۳: متغیر در ابتدا
همه متغیرها قبل از هر چیز
```bash
YEAR=$(date +%Y); ISO=$(date -Iseconds)
```

## قانون ۴: pull قبل از push
```bash
git pull --rebase && git push
```

## قانون ۵: check permissions
```bash
chmod -R 755 dir/ 2>/dev/null
echo "dir/" >> .gitignore
```

## تاریخ
2026-09-22T00:24:18+03:30

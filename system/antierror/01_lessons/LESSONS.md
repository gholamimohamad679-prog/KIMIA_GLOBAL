# درس‌های خطا

## خطای ۱: case sensitivity
**خطا:** نام پوشه حرف کوچک، نام متغیر حرف بزرگ
**درس:** همیشه lowercase برای پوشه‌ها
**قانون:** rule_lowercase_folders

## خطای ۲: for loop بدون mkdir
**خطا:** for loop نوشت، ولی mkdir داخلش نبود
**درس:** قبل از loop، همه پوشه‌ها را بساز
**قانون:** rule_mkdir_before_loop

## خطای ۳: متغیر undefined
**خطا:** $ISO خالی بود در nano
**درس:** همیشه متغیرها را در ابتدا تعریف کن
**قانون:** rule_vars_at_top

## خطای ۴: git push بدون pull
**خطا:** push رد شد چون remote جلوتر بود
**درس:** اول pull --rebase، بعد push
**قانون:** rule_pull_before_push

## خطای ۵: permission denied
**خطا:** pct/ اجازه نمی‌دهد
**درس:** chmod یا .gitignore
**قانون:** rule_permissions_check

## تاریخ
2026-09-22T00:24:18+03:30

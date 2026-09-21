#!/data/data/com.termux/files/usr/bin/bash
# چک قبل از اجرا

echo "🛡️ چک قبل از اجرا"
echo ""

# چک ۱: lowercase
echo "▶ چک ۱: lowercase"
if ls */ 2>/dev/null | grep -q "[A-Z]"; then
    echo "  ⚠️ پوشه با حرف بزرگ"
else
    echo "  ✅ همه lowercase"
fi

# چک ۲: متغیرها
echo "▶ چک ۲: متغیرها"
if [ -z "$ISO" ]; then
    echo "  ⚠️ ISO تعریف نشده"
else
    echo "  ✅ ISO: $ISO"
fi

# چک ۳: git status
echo "▶ چک ۳: git"
git status -s | head -3

# چک ۴: remote
echo "▶ چک ۴: remote"
git remote -v | head -2

# چک ۵: permission
echo "▶ چک ۵: permission"
find . -maxdepth 2 -type d ! -perm -u+r 2>/dev/null | head -3

echo ""
echo "✅ چک کامل"

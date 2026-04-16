#!/bin/bash
# Script test download PL-01A/PL-01B qua API (cần JWT token)

API_URL="http://localhost:8000/api/v1"

echo "=================================================="
echo "TEST DOWNLOAD PL-01A và PL-01B"
echo "=================================================="

# Login để lấy token (dùng admin account)
echo ""
echo "1. Login để lấy token..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=20ZZ-0224&password=123456")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Lỗi: Không lấy được token"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Đã lấy token: ${TOKEN:0:50}..."

# Test 1: PL-01A (công chức thường)
echo ""
echo "2. Test download PL-01A (ma_cc=20ZZ-0447, T1/2026)..."
HTTP_CODE=$(curl -s -o /tmp/test_pl01a.docx -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$API_URL/in-bang-ke/phieu-danh-gia/1/2026?ma_cc=20ZZ-0447")

if [ "$HTTP_CODE" = "200" ]; then
  FILE_SIZE=$(stat -f%z /tmp/test_pl01a.docx 2>/dev/null || stat -c%s /tmp/test_pl01a.docx)
  echo "✅ HTTP 200 - Đã tải file ($FILE_SIZE bytes)"
else
  echo "❌ HTTP $HTTP_CODE"
  cat /tmp/test_pl01a.docx
  exit 1
fi

# Test 2: PL-01B (lãnh đạo)
echo ""
echo "3. Test download PL-01B (ma_cc=20ZZ-0224, T2/2026)..."
HTTP_CODE=$(curl -s -o /tmp/test_pl01b.docx -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "$API_URL/in-bang-ke/phieu-danh-gia/2/2026?ma_cc=20ZZ-0224")

if [ "$HTTP_CODE" = "200" ]; then
  FILE_SIZE=$(stat -f%z /tmp/test_pl01b.docx 2>/dev/null || stat -c%s /tmp/test_pl01b.docx)
  echo "✅ HTTP 200 - Đã tải file ($FILE_SIZE bytes)"
else
  echo "❌ HTTP $HTTP_CODE"
  cat /tmp/test_pl01b.docx
  exit 1
fi

# Verify paragraphs bằng Python
echo ""
echo "4. Verify header paragraphs..."
python3 << 'PYEOF'
from docx import Document

for filename, label in [("/tmp/test_pl01a.docx", "PL-01A"), ("/tmp/test_pl01b.docx", "PL-01B")]:
    print(f"\n{'='*60}")
    print(f"{label}: {filename}")
    print('='*60)

    try:
        doc = Document(filename)
        print("Header (paragraphs 5-9):")
        for i in range(5, min(10, len(doc.paragraphs))):
            p = doc.paragraphs[i]
            print(f"  [{i}] {repr(p.text)}")

        # Check dòng trống
        found_vi_tri = False
        found_don_vi = False
        has_empty = False

        for i, p in enumerate(doc.paragraphs[:12]):
            text = p.text
            if "Vị trí việc làm" in text or "Chức vụ, chức danh" in text:
                found_vi_tri = True
                continue
            if found_vi_tri and not found_don_vi:
                if "Đơn vị công tác" in text:
                    found_don_vi = True
                elif text.strip() == "" or text == "\t":
                    has_empty = True
                    print(f"\n⚠️  DÒNG TRỐNG tại [{i}]: {repr(text)}")

        if has_empty:
            print(f"❌ {label}: CÒN DÒNG TRỐNG")
        else:
            print(f"✅ {label}: OK - Không có dòng trống")

    except Exception as e:
        print(f"❌ Lỗi đọc {filename}: {e}")
PYEOF

echo ""
echo "=================================================="
echo "✅ HOÀN THÀNH"
echo "=================================================="

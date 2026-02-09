"""
Script reset xếp loại đề xuất về NULL (để hệ thống dùng xếp loại tự động)
Chạy: cd /root/kpi-haiquan/backend && source venv/bin/activate && python3 fix_xeploai.py
"""
import asyncio
from app.api.deps import get_db
from sqlalchemy import text

async def fix_all():
    async for db in get_db():
        # Đếm trước
        result = await db.execute(text('''
            SELECT COUNT(*) FROM chi_tiet_xep_loai 
            WHERE xep_loai_de_xuat IS NOT NULL 
              AND xep_loai_de_xuat != xep_loai_he_thong
        '''))
        count = result.scalar()
        print(f"Tim thay {count} ban ghi xep_loai_de_xuat != xep_loai_he_thong")
        
        if count > 0:
            # Reset xep_loai_de_xuat = NULL (để hệ thống dùng xep_loai_he_thong)
            await db.execute(text('''
                UPDATE chi_tiet_xep_loai 
                SET xep_loai_de_xuat = NULL
                WHERE xep_loai_de_xuat IS NOT NULL 
                  AND xep_loai_de_xuat != xep_loai_he_thong
            '''))
            await db.commit()
            print(f"Da reset {count} ban ghi xep_loai_de_xuat = NULL")
        else:
            print("Khong co ban ghi nao can sua!")
        break

if __name__ == "__main__":
    asyncio.run(fix_all())
"""
Script kiểm tra xếp loại đề xuất trong database
Chạy: cd /root/kpi-haiquan/backend && source venv/bin/activate && python3 check_xeploai.py
"""
import asyncio
from app.api.deps import get_db
from sqlalchemy import text

async def check():
    async for db in get_db():
        result = await db.execute(text('''
            SELECT cc.ma_cc, cc.ho_ten, ct.diem_tong, 
                   ct.xep_loai_he_thong, ct.xep_loai_de_xuat, ct.xep_loai_quyet_dinh,
                   CASE WHEN ct.xep_loai_de_xuat IS NOT NULL 
                        AND ct.xep_loai_de_xuat != ct.xep_loai_he_thong 
                        THEN 'SAI' ELSE 'OK' END as status
            FROM chi_tiet_xep_loai ct
            JOIN bao_cao_xep_loai bc ON ct.bao_cao_id = bc.id
            JOIN cong_chuc cc ON ct.cong_chuc_id = cc.id
            WHERE bc.thang = 1 AND bc.nam = 2026
            ORDER BY cc.ma_cc
        '''))
        rows = result.fetchall()
        print("Ma CC        Ho ten               Diem   HT  DX   QD  Status")
        print("-" * 70)
        sai_count = 0
        for r in rows:
            status = r[6]
            if status == 'SAI':
                sai_count += 1
            ma = r[0] or "-"
            ten = (r[1] or "-")[:18]
            diem = float(r[2]) if r[2] else 0
            ht = r[3] or "-"
            dx = r[4] or "-"
            qd = r[5] or "-"
            print(f"{ma:<12} {ten:<20} {diem:>6.1f} {ht:>3} {dx:>3} {qd:>4} {status}")
        print(f"\nTong: {len(rows)} | Sai: {sai_count}")
        break

if __name__ == "__main__":
    asyncio.run(check())
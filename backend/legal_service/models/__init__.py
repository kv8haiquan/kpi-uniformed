"""
legal_service/models/__init__.py
==================================
Import tat ca 6 Legal models + Base + READONLY stubs.

Thu tu import quan trong:
  1. base.py (Base + CongChucRef + DonViRef + VaiTroRef)
  2. loai_van_ban.py (khong phu thuoc model khac)
  3. van_ban.py (phu thuoc loai_van_ban, cong_chuc — dung TYPE_CHECKING)
  4. van_ban_lien_ket.py (phu thuoc van_ban)
  5. xac_nhan_doc.py (phu thuoc van_ban, cong_chuc)
  6. quiz_van_ban.py (phu thuoc van_ban, cong_chuc)
  7. ket_qua_quiz.py (phu thuoc quiz_van_ban, cong_chuc)
"""

from legal_service.models.base import Base, CongChucRef, DonViRef, VaiTroRef
from legal_service.models.ket_qua_quiz import KetQuaQuiz
from legal_service.models.loai_van_ban import LoaiVanBan
from legal_service.models.quiz_van_ban import QuizVanBan
from legal_service.models.van_ban import VanBan
from legal_service.models.van_ban_lien_ket import VanBanLienKet
from legal_service.models.xac_nhan_doc import XacNhanDoc

__all__ = [
    # Base + READONLY stubs
    "Base",
    "CongChucRef",
    "DonViRef",
    "VaiTroRef",
    # Legal models
    "LoaiVanBan",
    "VanBan",
    "VanBanLienKet",
    "XacNhanDoc",
    "QuizVanBan",
    "KetQuaQuiz",
]

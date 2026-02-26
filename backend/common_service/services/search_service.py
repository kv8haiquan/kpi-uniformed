"""
common_service/services/search_service.py
==========================================
Unified Search — Tim kiem hop nhat cross-schema.

CHIEN LUOC:
  - Query truc tiep cross-schema (cung database kpi_haiquan)
  - Kiem tra bang ton tai truoc khi query (information_schema)
  - Neu 1 module loi → skip, khong crash toan bo
  - UNION ket qua tu nhieu module, sap xep theo score DESC

Modules:
  - COMMON: common.knowledge_base (tsvector)
  - PORTAL: portal.bai_viet (ILIKE)
  - LEGAL: legal.van_ban (tsvector)
  - LMS: lms.khoa_hoc (ILIKE)
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from common_service.schemas.search import SearchResponse, SearchResultItem, SearchSuggestion

logger = logging.getLogger(__name__)

# Boost factors cho ranking
BOOST_FACTORS = {
    "LEGAL": 1.2,
    "PORTAL": 1.0,
    "LMS": 1.0,
    "COMMON": 1.0,
}


# ---------------------------------------------------------------------------
# Public methods
# ---------------------------------------------------------------------------


async def tim_kiem(
    db: AsyncSession,
    q: str,
    *,
    modules: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> SearchResponse:
    """Tim kiem hop nhat cross-schema.

    Args:
        q: Tu khoa (min 2 ky tu)
        modules: Comma-separated: "lms,forum,legal,portal,common"
        page: Trang
        page_size: So luong moi trang
    """
    requested_modules = _parse_modules(modules)
    all_results: list[SearchResultItem] = []
    total_by_module: dict[str, int] = {}

    # Kiem tra cac bang ton tai
    existing_tables = await _get_existing_tables(db)

    # Search tung module — moi module chay rieng, loi 1 module khong anh huong module khac
    search_funcs = [
        ("COMMON", "common.knowledge_base", _search_knowledge_base),
        ("PORTAL", "portal.bai_viet", _search_portal),
        ("LEGAL", "legal.van_ban", _search_legal),
        ("LMS", "lms.khoa_hoc", _search_lms),
    ]

    for module_name, table_key, search_func in search_funcs:
        if module_name.lower() not in requested_modules:
            continue
        if table_key not in existing_tables:
            logger.debug("Skip %s: bang %s chua ton tai", module_name, table_key)
            continue

        try:
            results = await search_func(db, q)
            total_by_module[module_name] = len(results)
            all_results.extend(results)
        except Exception as e:
            logger.warning("Loi search %s: %s", module_name, e)
            total_by_module[module_name] = 0

    # Sap xep theo score DESC
    all_results.sort(key=lambda r: r.score, reverse=True)

    # Phan trang
    total = len(all_results)
    offset = (page - 1) * page_size
    paged = all_results[offset:offset + page_size]

    return SearchResponse(
        results=paged,
        total_by_module=total_by_module,
        total=total,
        page=page,
        page_size=page_size,
    )


async def goi_y(
    db: AsyncSession,
    q: str,
) -> SearchSuggestion:
    """Goi y tu khoa tim kiem.

    Goi y tu: tags pho bien (JSONB), tieu de gan day.
    Toi da 5 goi y.
    """
    suggestions: list[str] = []

    # Goi y tu tags trong knowledge_base
    existing = await _get_existing_tables(db)
    if "common.knowledge_base" in existing:
        try:
            tag_q = text("""
                SELECT DISTINCT jsonb_array_elements_text(tags) AS tag
                FROM common.knowledge_base
                WHERE is_deleted = FALSE
                  AND trang_thai = 'DA_XUAT_BAN'
                  AND jsonb_array_elements_text(tags) ILIKE :pattern
                LIMIT 3
            """)
            result = await db.execute(tag_q, {"pattern": f"%{q}%"})
            for row in result:
                if row[0] not in suggestions:
                    suggestions.append(row[0])
        except Exception as e:
            logger.debug("Loi goi y tags: %s", e)

    # Goi y tu tieu_de trong knowledge_base
    if "common.knowledge_base" in existing and len(suggestions) < 5:
        try:
            title_q = text("""
                SELECT tieu_de FROM common.knowledge_base
                WHERE is_deleted = FALSE
                  AND trang_thai = 'DA_XUAT_BAN'
                  AND tieu_de ILIKE :pattern
                ORDER BY updated_at DESC
                LIMIT :limit
            """)
            result = await db.execute(title_q, {"pattern": f"%{q}%", "limit": 5 - len(suggestions)})
            for row in result:
                if row[0] not in suggestions:
                    suggestions.append(row[0])
        except Exception as e:
            logger.debug("Loi goi y tieu de: %s", e)

    # Goi y tu portal bai_viet
    if "portal.bai_viet" in existing and len(suggestions) < 5:
        try:
            bv_q = text("""
                SELECT tieu_de FROM portal.bai_viet
                WHERE is_deleted = FALSE
                  AND trang_thai = 'XUAT_BAN'
                  AND tieu_de ILIKE :pattern
                ORDER BY ngay_xuat_ban DESC NULLS LAST
                LIMIT :limit
            """)
            result = await db.execute(bv_q, {"pattern": f"%{q}%", "limit": 5 - len(suggestions)})
            for row in result:
                if row[0] not in suggestions:
                    suggestions.append(row[0])
        except Exception as e:
            logger.debug("Loi goi y bai viet: %s", e)

    return SearchSuggestion(suggestions=suggestions[:5])


# ---------------------------------------------------------------------------
# Search per module — raw SQL for cross-schema
# ---------------------------------------------------------------------------


async def _search_knowledge_base(
    db: AsyncSession,
    q: str,
) -> list[SearchResultItem]:
    """Search common.knowledge_base — co tsvector."""
    sql = text("""
        SELECT id, loai, tieu_de, noi_dung,
               ts_rank(search_vector, plainto_tsquery('simple', :q)) AS rank
        FROM common.knowledge_base
        WHERE is_deleted = FALSE
          AND trang_thai = 'DA_XUAT_BAN'
          AND search_vector @@ plainto_tsquery('simple', :q)
        ORDER BY rank DESC
        LIMIT 50
    """)
    result = await db.execute(sql, {"q": q})
    rows = result.fetchall()

    items = []
    boost = BOOST_FACTORS.get("COMMON", 1.0)
    for row in rows:
        items.append(SearchResultItem(
            module="COMMON",
            type=row[1],  # loai: SOP hoac FAQ
            id=row[0],
            title=row[2],
            snippet=_make_snippet(row[3], q),
            link=f"/kien-thuc/{row[0]}",
            score=float(row[4]) * boost,
        ))
    return items


async def _search_portal(
    db: AsyncSession,
    q: str,
) -> list[SearchResultItem]:
    """Search portal.bai_viet — ILIKE (khong co tsvector)."""
    sql = text("""
        SELECT id, tieu_de, tom_tat, noi_dung, is_ghim
        FROM portal.bai_viet
        WHERE is_deleted = FALSE
          AND trang_thai = 'XUAT_BAN'
          AND (tieu_de ILIKE :pattern OR tom_tat ILIKE :pattern OR noi_dung ILIKE :pattern)
        ORDER BY is_ghim DESC, ngay_xuat_ban DESC NULLS LAST
        LIMIT 50
    """)
    result = await db.execute(sql, {"pattern": f"%{q}%"})
    rows = result.fetchall()

    items = []
    boost = BOOST_FACTORS.get("PORTAL", 1.0)
    for row in rows:
        # Bai ghim duoc boost them
        pin_boost = 1.1 if row[4] else 1.0
        items.append(SearchResultItem(
            module="PORTAL",
            type="BAI_VIET",
            id=row[0],
            title=row[1],
            snippet=_make_snippet(row[2] or row[3] or "", q),
            link=f"/tin-tuc/{row[0]}",
            score=1.0 * boost * pin_boost,
        ))
    return items


async def _search_legal(
    db: AsyncSession,
    q: str,
) -> list[SearchResultItem]:
    """Search legal.van_ban — co tsvector."""
    sql = text("""
        SELECT id, so_hieu, trich_yeu, tom_tat,
               ts_rank(search_vector, plainto_tsquery('simple', :q)) AS rank
        FROM legal.van_ban
        WHERE is_deleted = FALSE
          AND trang_thai_duyet = 'DA_XUAT_BAN'
          AND search_vector @@ plainto_tsquery('simple', :q)
        ORDER BY rank DESC
        LIMIT 50
    """)
    result = await db.execute(sql, {"q": q})
    rows = result.fetchall()

    items = []
    boost = BOOST_FACTORS.get("LEGAL", 1.2)
    for row in rows:
        title = f"{row[1]} — {row[2]}" if row[1] else row[2]
        items.append(SearchResultItem(
            module="LEGAL",
            type="VAN_BAN",
            id=row[0],
            title=title,
            snippet=_make_snippet(row[3] or row[2] or "", q),
            link=f"/phap-luat/{row[0]}",
            score=float(row[4]) * boost,
        ))
    return items


async def _search_lms(
    db: AsyncSession,
    q: str,
) -> list[SearchResultItem]:
    """Search lms.khoa_hoc — ILIKE."""
    sql = text("""
        SELECT id, ten_khoa_hoc, mo_ta, trang_thai
        FROM lms.khoa_hoc
        WHERE trang_thai = 'DA_XUAT_BAN'
          AND (ten_khoa_hoc ILIKE :pattern OR mo_ta ILIKE :pattern)
        ORDER BY created_at DESC
        LIMIT 50
    """)
    result = await db.execute(sql, {"pattern": f"%{q}%"})
    rows = result.fetchall()

    items = []
    boost = BOOST_FACTORS.get("LMS", 1.0)
    for row in rows:
        items.append(SearchResultItem(
            module="LMS",
            type="KHOA_HOC",
            id=row[0],
            title=row[1],
            snippet=_make_snippet(row[2] or "", q),
            link=f"/dao-tao/khoa-hoc/{row[0]}",
            score=1.0 * boost,
        ))
    return items


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_existing_tables(db: AsyncSession) -> set[str]:
    """Kiem tra cac bang ton tai trong database.

    Tra ve set: {'common.knowledge_base', 'portal.bai_viet', ...}
    """
    sql = text("""
        SELECT table_schema || '.' || table_name
        FROM information_schema.tables
        WHERE table_schema IN ('common', 'portal', 'legal', 'lms', 'forum')
          AND table_type = 'BASE TABLE'
    """)
    result = await db.execute(sql)
    return {row[0] for row in result}


def _parse_modules(modules: Optional[str]) -> set[str]:
    """Parse comma-separated module string.

    Default: tat ca modules.
    """
    if not modules:
        return {"common", "portal", "legal", "lms", "forum"}
    return {m.strip().lower() for m in modules.split(",") if m.strip()}


def _make_snippet(text_content: str, query: str, max_len: int = 150) -> str:
    """Tao snippet ~150 ky tu xung quanh tu khoa match.

    Tim vi tri dau tien cua query trong text, trich doan xung quanh.
    """
    if not text_content:
        return ""

    # Loai bo HTML tags
    clean = re.sub(r"<[^>]+>", " ", text_content)
    clean = re.sub(r"\s+", " ", clean).strip()

    # Tim vi tri match (case-insensitive)
    lower_text = clean.lower()
    lower_query = query.lower()
    pos = lower_text.find(lower_query)

    if pos == -1:
        # Khong tim thay → tra dau van ban
        return clean[:max_len] + ("..." if len(clean) > max_len else "")

    # Trich doan xung quanh
    start = max(0, pos - 50)
    end = min(len(clean), pos + len(query) + 100)

    snippet = clean[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(clean):
        snippet = snippet + "..."

    return snippet

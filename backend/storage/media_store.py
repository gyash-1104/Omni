"""
WhatsApp media download and Supabase Storage upload.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

import httpx

from backend.config import get_settings
from backend.schemas.session import Session, AttachmentMeta
from backend.storage import supabase_store

settings = get_settings()


async def download_twilio_media(media_url: str) -> tuple[bytes, str]:
    """Download media from Twilio with basic auth."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            media_url,
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            follow_redirects=True,
        )
        r.raise_for_status()
        ctype = r.headers.get("content-type", "application/octet-stream")
        return r.content, ctype


async def save_attachment(
    session: Session,
    media_url: str,
    content_type: str = "",
    file_name: Optional[str] = None,
) -> Optional[AttachmentMeta]:
    """Download from Twilio, upload to Supabase storage, record metadata."""
    if not media_url:
        return None
    try:
        data, ctype = await download_twilio_media(media_url)
        if not content_type:
            content_type = ctype
        ext = "jpg"
        if "png" in content_type:
            ext = "png"
        elif "pdf" in content_type:
            ext = "pdf"
        fname = file_name or f"{uuid.uuid4().hex[:12]}.{ext}"
        path = f"{session.session_id}/{fname}"

        public_url = await _upload_to_supabase(path, data, content_type)
        if not public_url:
            public_url = f"twilio:{media_url}"

        meta = AttachmentMeta(
            file_name=fname,
            file_url=public_url,
            mime_type=content_type,
            uploaded_at=datetime.utcnow(),
        )
        session.attachments.append(meta)
        await supabase_store.save_attachment_record(
            session_id=session.session_id,
            file_name=fname,
            file_url=public_url,
            mime_type=content_type,
        )
        return meta
    except Exception as e:
        print(f"[MediaStore] save_attachment error: {e}")
        return None


async def _upload_to_supabase(path: str, data: bytes, content_type: str) -> Optional[str]:
    if not supabase_store.is_configured():
        return None
    try:
        client = supabase_store._get_client()
        bucket = "enquiry-files"
        client.storage.from_(bucket).upload(
            path,
            data,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        return client.storage.from_(bucket).get_public_url(path)
    except Exception as e:
        print(f"[MediaStore] supabase upload error: {e}")
        return None

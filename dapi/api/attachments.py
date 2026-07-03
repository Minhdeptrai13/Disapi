"""
api/attachments.py — Discord Attachments / File Upload API
============================================================

Implements Discord's 3-step file upload flow used by the official client:

  1. Request upload URLs via ``POST /channels/{channel_id}/attachments``
  2. Upload raw file bytes to the returned GCS URL via ``PUT``
  3. Reference uploaded files when sending a message

This module handles steps 1 & 2. Step 3 is done via ``MessagesAPI.send()``.
"""

from __future__ import annotations

import asyncio
import mimetypes
import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx

from ..http_client import HTTPClient, Route
from ..exceptions import InvalidArgument, BadRequest


__all__: list[str] = ["AttachmentsAPI", "UploadedFile"]

logger = logging.getLogger("dapi.attachments")


# ─── Upload Result ────────────────────────────────────────────────────────────

@dataclass
class UploadedFile:
    """Represents a file that has been uploaded to Discord's CDN.

    Use this with ``MessagesAPI.send()`` to attach the uploaded file
    to a message.

    Attributes:
        id: The attachment slot ID (int, used in message payload).
        filename: Original filename.
        upload_filename: The ``upload_filename`` returned by Discord.
        upload_url: The GCS URL where the file was uploaded.
        size: File size in bytes.
        content_type: MIME type of the file.
        is_uploaded: Whether the file was successfully uploaded to GCS.
    """

    id: int
    filename: str
    upload_filename: str
    upload_url: str
    size: int
    content_type: str = "application/octet-stream"
    is_uploaded: bool = False

    def to_attachment_payload(self) -> Dict[str, Any]:
        """Convert to attachment payload for message send.

        Returns the dict to include in ``attachments`` list when sending
        a message with ``MessagesAPI.send()``.

        Returns:
            Attachment reference dict.
        """
        return {
            "id": self.id,
            "filename": self.filename,
            "uploaded_filename": self.upload_filename,
        }


# ─── Attachments API ──────────────────────────────────────────────────────────

class AttachmentsAPI:
    """Discord Attachments / File Upload API.

    Implements the full file upload flow used by the official Discord client.

    The upload process:
        1. Call ``request_upload()`` to get pre-signed GCS upload URLs
        2. Call ``upload_to_cloud()`` to PUT file bytes to GCS
        3. Use the returned ``UploadedFile`` with ``messages.send()``

    Or use the convenience method ``upload_files()`` which does steps 1+2.

    Access via ``client.attachments.*``.

    Example::

        # Upload a single file
        uploaded = await client.attachments.upload_file(
            channel_id="123456",
            file_path="screenshot.png",
        )
        await client.messages.send(
            "123456",
            content="Check this out!",
            attachments=[uploaded.to_attachment_payload()],
        )

        # Upload multiple files at once
        uploaded_files = await client.attachments.upload_files(
            channel_id="123456",
            file_paths=["image1.png", "doc.pdf"],
        )
        await client.messages.send(
            "123456",
            content="Here are the files",
            attachments=[f.to_attachment_payload() for f in uploaded_files],
        )
    """

    # Max file size for free users (25 MB)
    MAX_FILE_SIZE_FREE: int = 25 * 1024 * 1024
    # Max file size for Nitro Basic (50 MB)
    MAX_FILE_SIZE_NITRO_BASIC: int = 50 * 1024 * 1024
    # Max file size for Nitro (500 MB)
    MAX_FILE_SIZE_NITRO: int = 500 * 1024 * 1024
    # Max files per message
    MAX_FILES_PER_MESSAGE: int = 10

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    # ─── Step 1: Request Upload URLs ─────────────────────────────────────────

    async def request_upload(
        self,
        channel_id: str,
        files: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Request pre-signed upload URLs from Discord.

        This is Step 1 of the upload flow. Discord returns GCS URLs
        where the files should be uploaded via PUT.

        Args:
            channel_id: Target channel snowflake ID.
            files: List of file descriptors, each containing:
                - ``filename`` (str): The file name.
                - ``file_size`` (int): Size in bytes.
                - ``id`` (str): Attachment slot ID (e.g. "0", "1").
                - ``is_clip`` (bool, optional): Whether it's a clip.

        Returns:
            List of upload slot dicts from Discord, each containing:
                - ``id`` (int): Slot ID.
                - ``upload_url`` (str): GCS pre-signed URL.
                - ``upload_filename`` (str): Discord-assigned filename.

        Raises:
            BadRequest: If file descriptors are invalid.
            Forbidden: If missing permissions.

        Example::

            slots = await client.attachments.request_upload(
                "123456",
                files=[{
                    "filename": "image.png",
                    "file_size": 12345,
                    "id": "0",
                    "is_clip": False,
                }],
            )
        """
        payload = {"files": files}

        data = await self._http.request(
            Route("POST", "/channels/{channel_id}/attachments",
                  channel_id=channel_id),
            json_payload=payload,
        )

        return data.get("attachments", []) if isinstance(data, dict) else []

    # ─── Step 2: Upload to GCS ───────────────────────────────────────────────

    async def upload_to_cloud(
        self,
        upload_url: str,
        file_data: bytes,
        content_type: str = "application/octet-stream",
    ) -> bool:
        """Upload file bytes to Discord's GCS pre-signed URL.

        This is Step 2 of the upload flow. Sends a PUT request to the
        GCS URL returned by ``request_upload()``.

        Args:
            upload_url: The pre-signed GCS URL from ``request_upload()``.
            file_data: Raw file bytes to upload.
            content_type: MIME type of the file.

        Returns:
            ``True`` if upload was successful (2xx status).

        Raises:
            httpx.HTTPError: If the upload request fails.
        """
        # Use a separate httpx client for GCS uploads (not the Discord API client)
        # This mimics the real Discord client which uses a direct PUT to GCS
        headers = {
            "Content-Type": content_type,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/150.0.0.0 Safari/537.36",
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
        }

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(300.0),  # 5 min timeout for large files
            http2=True,
            follow_redirects=True,
        ) as client:
            response = await client.put(
                upload_url,
                content=file_data,
                headers=headers,
            )

        success = 200 <= response.status_code < 300
        if success:
            logger.debug("File uploaded to GCS successfully (%d bytes)", len(file_data))
        else:
            logger.warning(
                "GCS upload failed: %d %s",
                response.status_code,
                response.text[:200] if response.text else "No body",
            )

        return success

    # ─── Convenience: Upload Single File ─────────────────────────────────────

    async def upload_file(
        self,
        channel_id: str,
        file_path: Optional[str] = None,
        *,
        file_data: Optional[bytes] = None,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
        description: Optional[str] = None,
        is_clip: bool = False,
        slot_id: int = 0,
        spoiler: bool = False,
    ) -> UploadedFile:
        """Upload a single file to Discord (Steps 1 + 2 combined).

        Provide either ``file_path`` (reads from disk) or ``file_data``
        + ``filename`` (in-memory bytes).

        Args:
            channel_id: Target channel ID.
            file_path: Path to the file on disk.
            file_data: Raw file bytes (alternative to file_path).
            filename: Filename override (required if using file_data).
            content_type: MIME type override (auto-detected if not set).
            description: Alt text / description for the attachment.
            is_clip: Whether this is a clip upload.
            slot_id: Attachment slot ID (default 0).
            spoiler: If True, prefix filename with ``SPOILER_``.

        Returns:
            An ``UploadedFile`` ready for use with ``messages.send()``.

        Raises:
            InvalidArgument: If neither file_path nor file_data is provided.
            FileNotFoundError: If file_path doesn't exist.

        Example::

            # From disk
            uploaded = await client.attachments.upload_file(
                "123456", "screenshot.png"
            )

            # From memory
            uploaded = await client.attachments.upload_file(
                "123456",
                file_data=image_bytes,
                filename="generated.png",
            )

            # Send the uploaded file
            await client.messages.send(
                "123456",
                content="Here's the file",
                attachments=[uploaded.to_attachment_payload()],
            )
        """
        if file_path is None and file_data is None:
            raise InvalidArgument(
                "file_path or file_data",
                "Either file_path or file_data must be provided.",
            )

        # Read file from disk if path is given
        if file_path is not None:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            file_data = path.read_bytes()
            if filename is None:
                filename = path.name

        if filename is None:
            raise InvalidArgument("filename", "filename is required when using file_data.")

        # Auto-detect MIME type
        if content_type is None:
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        file_size = len(file_data)

        # Spoiler prefix
        if spoiler and not filename.startswith("SPOILER_"):
            filename = f"SPOILER_{filename}"

        # Step 1: Request upload URL
        file_descriptor = {
            "filename": filename,
            "file_size": file_size,
            "id": str(slot_id),
            "is_clip": is_clip,
        }

        slots = await self.request_upload(channel_id, [file_descriptor])

        if not slots:
            raise BadRequest(
                status=400,
                reason="Bad Request",
                method="POST",
                url=f"/channels/{channel_id}/attachments",
                response_data={"error": "No upload slots returned"},
            )

        slot = slots[0]
        upload_url = slot["upload_url"]
        upload_filename = slot["upload_filename"]

        # Step 2: Upload to GCS
        success = await self.upload_to_cloud(upload_url, file_data, content_type)

        uploaded = UploadedFile(
            id=slot_id,
            filename=filename,
            upload_filename=upload_filename,
            upload_url=upload_url,
            size=file_size,
            content_type=content_type,
            is_uploaded=success,
        )

        logger.info(
            "File %r uploaded: %s (%d bytes, %s)",
            filename,
            "success" if success else "FAILED",
            file_size,
            content_type,
        )

        return uploaded

    # ─── Convenience: Upload Multiple Files ──────────────────────────────────

    async def upload_files(
        self,
        channel_id: str,
        file_paths: Optional[List[str]] = None,
        *,
        files_data: Optional[List[Tuple[str, bytes]]] = None,
        spoiler: bool = False,
    ) -> List[UploadedFile]:
        """Upload multiple files to Discord (Steps 1 + 2 for each).

        Provide either ``file_paths`` (from disk) or ``files_data``
        (list of ``(filename, bytes)`` tuples).

        Args:
            channel_id: Target channel ID.
            file_paths: List of file paths on disk.
            files_data: List of (filename, bytes) tuples.
            spoiler: If True, mark all files as spoilers.

        Returns:
            List of ``UploadedFile`` objects ready for ``messages.send()``.

        Raises:
            InvalidArgument: If neither file_paths nor files_data is provided.

        Example::

            uploaded = await client.attachments.upload_files(
                "123456",
                file_paths=["img1.png", "img2.jpg", "doc.pdf"],
            )
            await client.messages.send(
                "123456",
                content="Multiple files!",
                attachments=[f.to_attachment_payload() for f in uploaded],
            )
        """
        if file_paths is None and files_data is None:
            raise InvalidArgument(
                "file_paths or files_data",
                "Either file_paths or files_data must be provided.",
            )

        # Build file list
        prepared: List[Tuple[str, bytes, str]] = []  # (filename, data, mime)

        if file_paths is not None:
            for fp in file_paths:
                path = Path(fp)
                if not path.exists():
                    raise FileNotFoundError(f"File not found: {fp}")
                data = path.read_bytes()
                name = path.name
                if spoiler and not name.startswith("SPOILER_"):
                    name = f"SPOILER_{name}"
                mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
                prepared.append((name, data, mime))
        elif files_data is not None:
            for name, data in files_data:
                if spoiler and not name.startswith("SPOILER_"):
                    name = f"SPOILER_{name}"
                mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
                prepared.append((name, data, mime))

        if len(prepared) > self.MAX_FILES_PER_MESSAGE:
            raise InvalidArgument(
                "files",
                f"Cannot upload more than {self.MAX_FILES_PER_MESSAGE} files per message.",
            )

        # Step 1: Request all upload URLs at once
        file_descriptors = [
            {
                "filename": name,
                "file_size": len(data),
                "id": str(i),
                "is_clip": False,
            }
            for i, (name, data, _) in enumerate(prepared)
        ]

        slots = await self.request_upload(channel_id, file_descriptors)

        if len(slots) != len(prepared):
            logger.warning(
                "Expected %d upload slots, got %d",
                len(prepared),
                len(slots),
            )

        # Step 2: Upload all files concurrently
        results: List[UploadedFile] = []

        async def _upload_one(
            idx: int,
            slot: Dict[str, Any],
            name: str,
            data: bytes,
            mime: str,
        ) -> UploadedFile:
            success = await self.upload_to_cloud(
                slot["upload_url"], data, mime,
            )
            return UploadedFile(
                id=idx,
                filename=name,
                upload_filename=slot["upload_filename"],
                upload_url=slot["upload_url"],
                size=len(data),
                content_type=mime,
                is_uploaded=success,
            )

        tasks = [
            _upload_one(i, slot, name, data, mime)
            for i, (slot, (name, data, mime)) in enumerate(zip(slots, prepared))
        ]

        results = await asyncio.gather(*tasks)

        succeeded = sum(1 for r in results if r.is_uploaded)
        logger.info(
            "Uploaded %d/%d files to channel %s",
            succeeded,
            len(results),
            channel_id,
        )

        return list(results)

    # ─── Send with File (all-in-one convenience) ─────────────────────────────

    async def upload_and_send(
        self,
        channel_id: str,
        content: Optional[str] = None,
        *,
        file_path: Optional[str] = None,
        file_data: Optional[bytes] = None,
        filename: Optional[str] = None,
        spoiler: bool = False,
        reply_to: Optional[str] = None,
        tts: bool = False,
        stickers: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Upload a file and send it in a message (all-in-one).

        Combines upload + send into a single call for convenience.

        Args:
            channel_id: Target channel ID.
            content: Message text content.
            file_path: Path to file on disk.
            file_data: Raw file bytes (requires ``filename``).
            filename: Filename override.
            spoiler: Mark file as spoiler.
            reply_to: Message ID to reply to.
            tts: Enable text-to-speech.
            stickers: Sticker IDs to include.

        Returns:
            The raw message data dict from Discord.

        Example::

            await client.attachments.upload_and_send(
                "123456",
                content="Look at this!",
                file_path="screenshot.png",
            )
        """
        from ..utils import generate_nonce

        # Step 1+2: Upload
        uploaded = await self.upload_file(
            channel_id,
            file_path=file_path,
            file_data=file_data,
            filename=filename,
            spoiler=spoiler,
        )

        if not uploaded.is_uploaded:
            raise BadRequest(
                status=400,
                reason="Upload Failed",
                method="PUT",
                url=uploaded.upload_url,
                response_data={"error": "File upload to cloud storage failed"},
            )

        # Step 3: Send message with attachment reference
        payload: Dict[str, Any] = {
            "content": content or "",
            "nonce": generate_nonce(),
            "channel_id": channel_id,
            "type": 0,
            "sticker_ids": stickers or [],
            "attachments": [uploaded.to_attachment_payload()],
            "flags": 0,
            "tts": tts,
        }

        if reply_to:
            payload["message_reference"] = {
                "message_id": reply_to,
                "fail_if_not_exists": False,
            }

        data = await self._http.request(
            Route("POST", "/channels/{channel_id}/messages",
                  channel_id=channel_id),
            json_payload=payload,
        )

        return data

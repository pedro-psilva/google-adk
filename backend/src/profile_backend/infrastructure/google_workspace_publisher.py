from __future__ import annotations

from typing import Any

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build

from profile_backend.infrastructure.google_oauth import GOOGLE_WORKSPACE_OAUTH_SCOPES


class GoogleWorkspacePublisher:
    def publish_document(self, authorized_user_info: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
        credentials = _build_credentials(authorized_user_info)
        docs = build("docs", "v1", credentials=credentials, cache_discovery=False)
        created = docs.documents().create(body={"title": package["document_title"]}).execute()
        document_id = created["documentId"]
        docs.documents().batchUpdate(
            documentId=document_id,
            body={"requests": package.get("google_docs_requests", [])},
        ).execute()
        return {
            "document_id": document_id,
            "document_url": f"https://docs.google.com/document/d/{document_id}/edit",
            "authorized_user_info": _authorized_user_info(credentials),
        }

    def publish_spreadsheet(self, authorized_user_info: dict[str, Any], package: dict[str, Any]) -> dict[str, Any]:
        credentials = _build_credentials(authorized_user_info)
        sheets = build("sheets", "v4", credentials=credentials, cache_discovery=False)
        requested_sheets = package.get("sheets", [])
        first_sheet = requested_sheets[0]["title"] if requested_sheets else "Overview"
        created = sheets.spreadsheets().create(
            body={
                "properties": {"title": package["spreadsheet_title"]},
                "sheets": [{"properties": {"title": first_sheet}}],
            }
        ).execute()
        spreadsheet_id = created["spreadsheetId"]

        if len(requested_sheets) > 1:
            sheets.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    "requests": [
                        {"addSheet": {"properties": {"title": sheet["title"]}}}
                        for sheet in requested_sheets[1:]
                    ]
                },
            ).execute()

        for sheet in requested_sheets:
            sheets.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"'{sheet['title']}'!A1",
                valueInputOption="RAW",
                body={"values": sheet.get("rows", [])},
            ).execute()

        return {
            "spreadsheet_id": spreadsheet_id,
            "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
            "authorized_user_info": _authorized_user_info(credentials),
        }


def _build_credentials(authorized_user_info: dict[str, Any]) -> Credentials:
    credentials = Credentials.from_authorized_user_info(
        authorized_user_info,
        GOOGLE_WORKSPACE_OAUTH_SCOPES,
    )
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(GoogleAuthRequest())
    return credentials


def _authorized_user_info(credentials: Credentials) -> dict[str, Any]:
    return {
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "refresh_token": credentials.refresh_token,
        "token": credentials.token,
        "token_uri": credentials.token_uri,
        "scopes": list(credentials.scopes or GOOGLE_WORKSPACE_OAUTH_SCOPES),
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    }

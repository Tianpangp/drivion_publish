import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlsplit

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import Base
from app.core.permissions import Permission
from app.core.sso import SsoClient
from app.core.sso_permissions import map_sso_permissions
from app.models.sso import SsoAuthTransaction, SsoSession


class SsoBffTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.original = {
            "AUTH_MODE": settings.AUTH_MODE,
            "SSO_CLIENT_SECRET": settings.SSO_CLIENT_SECRET,
            "SSO_SESSION_SECRET": settings.SSO_SESSION_SECRET,
        }
        settings.AUTH_MODE = "sso"
        settings.SSO_CLIENT_SECRET = "test-client-secret"
        settings.SSO_SESSION_SECRET = "test-session-secret-with-sufficient-entropy"
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        self.client = SsoClient()

    async def asyncTearDown(self) -> None:
        for key, value in self.original.items():
            setattr(settings, key, value)
        await self.engine.dispose()

    async def test_pkce_callback_stores_only_encrypted_tokens(self) -> None:
        metadata = {
            "authorization_endpoint": "https://sso.test/api/auth/oauth/authorize",
            "token_endpoint": "https://sso.test/api/auth/oauth/token",
        }
        self.client._metadata = AsyncMock(return_value=(metadata, {"keys": []}))
        async with self.sessions() as db:
            handle, authorize_url = await self.client.create_auth_transaction(db)
            await db.commit()
            transaction = await db.get(SsoAuthTransaction, self.client._digest(handle))
            query = parse_qs(urlsplit(authorize_url).query)
            self.assertEqual("S256", query["code_challenge_method"][0])
            self.assertEqual(transaction.state, query["state"][0])
            self.assertNotIn(self.client.decrypt(transaction.code_verifier), authorize_url)

            tokens = {
                "access_token": "access-token-value",
                "refresh_token": "refresh-token-value",
                "id_token": "id-token-value",
            }
            self.client._token_request = AsyncMock(return_value=tokens)
            self.client.verify_token = AsyncMock(side_effect=[
                {"sub": "user-1", "token_use": "id", "nonce": transaction.nonce},
                {"sub": "user-1", "token_use": "access", "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())},
            ])
            self.client.userinfo = AsyncMock(return_value={
                "sub": "user-1", "preferred_username": "tester", "name": "Tester",
                "roles": ["automation.developer"],
                "permissions": ["autounit.definition.upload"],
                "permission_grants": [{"permission": "autounit.definition.upload", "scopeType": "tenant", "scopeId": "*"}],
            })
            session_handle = await self.client.complete_callback(db, handle, transaction.state, "one-time-code")
            await db.commit()

            self.assertIsNone(await db.get(SsoAuthTransaction, self.client._digest(handle)))
            session = await db.get(SsoSession, self.client._digest(session_handle))
            self.assertNotEqual("access-token-value", session.access_token)
            self.assertNotEqual("refresh-token-value", session.refresh_token)
            self.assertEqual("access-token-value", self.client.decrypt(session.access_token))

    async def test_expired_access_token_rotates_refresh_token(self) -> None:
        raw_handle = "session-handle"
        async with self.sessions() as db:
            db.add(SsoSession(
                id=self.client._digest(raw_handle), subject="user-1", username="tester",
                roles=[], permissions=[], permission_grants=[],
                access_token=self.client.encrypt("old-access"),
                refresh_token=self.client.encrypt("old-refresh"),
                access_expires_at=datetime.utcnow() - timedelta(seconds=1),
            ))
            await db.commit()
            self.client._token_request = AsyncMock(return_value={
                "access_token": "new-access", "refresh_token": "new-refresh"
            })
            self.client.verify_token = AsyncMock(return_value={
                "sub": "user-1", "token_use": "access",
                "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            })
            self.client.userinfo = AsyncMock(return_value={
                "roles": ["platform.user"], "permissions": [], "permission_grants": []
            })
            session = await self.client.load_session(db, raw_handle)
            await db.commit()
            self.assertEqual("new-access", self.client.decrypt(session.access_token))
            self.assertEqual("new-refresh", self.client.decrypt(session.refresh_token))
            request = self.client._token_request.await_args.args[0]
            self.assertEqual("old-refresh", request["refresh_token"])

    async def test_rs256_verification_checks_audience_use_and_nonce(self) -> None:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key()))
        public_jwk.update({"kid": "test-key", "alg": "RS256", "use": "sig"})
        self.client._metadata = AsyncMock(return_value=(
            {"issuer": settings.SSO_ISSUER, "jwks_uri": "https://sso.test/jwks"},
            {"keys": [public_jwk]},
        ))
        now = datetime.utcnow()
        token = jwt.encode({
            "iss": settings.SSO_ISSUER, "aud": settings.SSO_CLIENT_ID,
            "sub": "user-1", "iat": now, "exp": now + timedelta(minutes=5),
            "token_use": "id", "nonce": "expected-nonce",
        }, private_key, algorithm="RS256", headers={"kid": "test-key"})
        claims = await self.client.verify_token(token, "id", nonce="expected-nonce")
        self.assertEqual("user-1", claims["sub"])

    def test_sso_permissions_are_mapped_without_local_role_lookup(self) -> None:
        mapped = map_sso_permissions(
            ["autounit.definition.upload", "release.request.create"],
            ["automation.developer"],
        )
        self.assertIn(Permission.AUTOUNIT_UPLOAD.value, mapped)
        self.assertIn(Permission.AUTOUNIT_SUBMIT_PUBLISH.value, mapped)
        self.assertNotIn(Permission.AUTOUNIT_DELETE.value, mapped)


if __name__ == "__main__":
    unittest.main()

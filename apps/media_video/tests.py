from django.test import SimpleTestCase, override_settings

from apps.media_video.services import build_embed_url, is_bunny_video_id, sign_embed_token


class BunnyTokenTests(SimpleTestCase):
    def test_pending_no_es_id_real(self):
        self.assertFalse(is_bunny_video_id(''))
        self.assertFalse(is_bunny_video_id('pending://bienvenida-video-1'))
        self.assertTrue(is_bunny_video_id('eb1c4f77-0cda-46be-b47d-1118ad7c2ffe'))

    def test_sign_es_sha256_hex_de_concatenacion(self):
        token = sign_embed_token('video-1', 1623440202, token_security_key='secret')
        self.assertEqual(len(token), 64)
        self.assertEqual(token, sign_embed_token('video-1', 1623440202, token_security_key='secret'))
        self.assertNotEqual(token, sign_embed_token('video-2', 1623440202, token_security_key='secret'))

    @override_settings(
        BUNNY_LIBRARY_ID='759',
        BUNNY_TOKEN_SECURITY_KEY='secret',
        BUNNY_EMBED_HOST='player.mediadelivery.net',
        BUNNY_EMBED_TOKEN_TTL=100,
    )
    def test_build_embed_url_incluye_token_y_expires(self):
        url = build_embed_url('eb1c4f77-0cda-46be-b47d-1118ad7c2ffe', now_ts=1_000_000)
        self.assertTrue(url.startswith(
            'https://player.mediadelivery.net/embed/759/eb1c4f77-0cda-46be-b47d-1118ad7c2ffe?'
        ))
        self.assertIn('expires=1000100', url)
        self.assertIn('token=', url)

    @override_settings(BUNNY_LIBRARY_ID='', BUNNY_TOKEN_SECURITY_KEY='')
    def test_sin_credenciales_no_arma_url(self):
        self.assertIsNone(build_embed_url('eb1c4f77-0cda-46be-b47d-1118ad7c2ffe'))
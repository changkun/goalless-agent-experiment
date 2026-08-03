import unittest

from passgen.cipher import decrypt, encrypt, MAGIC, SALT_LEN, NONCE_LEN


class CipherTest(unittest.TestCase):
    def test_round_trip(self):
        data = b"attack at dawn"
        blob = encrypt(data, "correct horse battery staple")
        self.assertEqual(decrypt(blob, "correct horse battery staple"), data)

    def test_randomness(self):
        blob1 = encrypt(b"same", "pw")
        blob2 = encrypt(b"same", "pw")
        self.assertNotEqual(blob1, blob2)

    def test_wrong_password(self):
        blob = encrypt(b"secret", "right")
        with self.assertRaises(ValueError):
            decrypt(blob, "wrong")

    def test_tamper_detected(self):
        blob = bytearray(encrypt(b"secret data here", "pw"))
        head = len(MAGIC) + SALT_LEN + NONCE_LEN  # start of ciphertext
        self.assertGreater(len(blob) - 16, head)
        blob[head] ^= 0x01  # flip a byte in the ciphertext
        with self.assertRaises(ValueError):
            decrypt(bytes(blob), "pw")

    def test_tamper_body_trimmed(self):
        blob = bytearray(encrypt(b"secret", "pw"))
        blob = blob[:-1]  # drop the final tag byte
        with self.assertRaises(ValueError):
            decrypt(bytes(blob), "pw")

    def test_corrupt_header(self):
        with self.assertRaises(ValueError):
            decrypt(b"garbage", "pw")

    def test_unicode_password_and_data(self):
        blob = encrypt("héllo wörld".encode("utf-8"), "pässwörd")
        self.assertEqual(decrypt(blob, "pässwörd"), "héllo wörld".encode("utf-8"))


if __name__ == "__main__":
    unittest.main()

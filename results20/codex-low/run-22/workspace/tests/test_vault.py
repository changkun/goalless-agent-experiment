import os
import tempfile
import unittest

from passgen.vault import Vault


class VaultTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "vault.json")

    def test_create_and_persist(self):
        vault = Vault.open(self.path, "pw")
        vault.set("email", username="alice", password="s3cret")
        vault.save()

        reopened = Vault.open(self.path, "pw")
        self.assertEqual(reopened.get("email"), {"username": "alice", "password": "s3cret"})

    def test_wrong_password_on_open(self):
        vault = Vault.open(self.path, "pw")
        vault.set("a", password="x")
        vault.save()
        with self.assertRaises(ValueError):
            Vault.open(self.path, "nope")

    def test_delete(self):
        vault = Vault.open(self.path, "pw")
        vault.set("a", password="1")
        vault.set("b", password="2")
        self.assertTrue(vault.delete("a"))
        self.assertFalse(vault.delete("missing"))
        self.assertEqual(vault.names(), ["b"])

    def test_change_password(self):
        vault = Vault.open(self.path, "pw")
        vault.set("a", password="1")
        vault.change_password("newpw")
        vault.save()
        reopened = Vault.open(self.path, "newpw")
        self.assertEqual(reopened.get("a"), {"password": "1"})

    def test_wrong_password_after_change(self):
        vault = Vault.open(self.path, "pw")
        vault.set("a", password="1")
        vault.change_password("newpw")
        vault.save()
        with self.assertRaises(ValueError):
            Vault.open(self.path, "pw")


if __name__ == "__main__":
    unittest.main()

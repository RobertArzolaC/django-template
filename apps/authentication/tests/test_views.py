"""Tests for the ``apps.authentication.views`` module."""

from django.test import TestCase
from django.urls import reverse

from apps.users.factories import UserFactory

OLD_PASSWORD = "Passw0rd!123"
NEW_PASSWORD = "NewPassw0rd!456"


class ChangePasswordViewTests(TestCase):
    """Tests for the change-password endpoint."""

    def setUp(self) -> None:
        self.user = UserFactory(password=OLD_PASSWORD)
        self.client.force_login(self.user)
        self.url = reverse("apps.authentication:api_change_password")

    def test_wrong_old_password_returns_400(self) -> None:
        """An incorrect old password returns an error JSON response."""
        response = self.client.post(
            self.url,
            {
                "old_password": "wrong-old",
                "new_password1": NEW_PASSWORD,
                "new_password2": NEW_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")

    def test_change_password_success(self) -> None:
        """Valid credentials update the user password."""
        response = self.client.post(
            self.url,
            {
                "old_password": OLD_PASSWORD,
                "new_password1": NEW_PASSWORD,
                "new_password2": NEW_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))


class DeactivateAccountViewTests(TestCase):
    """Tests for the deactivate-account endpoint."""

    def setUp(self) -> None:
        self.user = UserFactory(is_active=True)
        self.client.force_login(self.user)
        self.url = reverse("apps.authentication:api_deactivate_account")

    def test_unknown_email_returns_400(self) -> None:
        """An unregistered email returns an error JSON response."""
        response = self.client.post(self.url, {"email": "ghost@example.com"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")

    def test_deactivate_success(self) -> None:
        """A registered email deactivates the related user."""
        response = self.client.post(self.url, {"email": self.user.email})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


STRONG_PASSWORD = "9fK2!vX7qL4zM"


class ValidatePasswordViewTests(TestCase):
    """Tests for the live password-validation endpoint."""

    def setUp(self) -> None:
        self.user = UserFactory()
        self.url = reverse("apps.authentication:validate_password_api")

    def test_anonymous_user_redirected(self) -> None:
        """Anonymous requests are redirected to login."""
        response = self.client.post(self.url, {"password": STRONG_PASSWORD})
        self.assertEqual(response.status_code, 302)

    def test_strong_password_returns_all_passed(self) -> None:
        """A strong password yields checks all marked as passed."""
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"password": STRONG_PASSWORD})
        self.assertEqual(response.status_code, 200)
        checks = response.json()["checks"]
        self.assertTrue(checks)
        for check in checks:
            self.assertTrue(check["passed"], msg=check["id"])

    def test_weak_password_returns_some_unpassed(self) -> None:
        """A purely numeric password reports failures."""
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"password": "12345678"})
        self.assertEqual(response.status_code, 200)
        checks = response.json()["checks"]
        self.assertTrue(any(not c["passed"] for c in checks))

    def test_empty_password_returns_all_unpassed(self) -> None:
        """Missing input is reported as not yet valid, not as an error."""
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"password": ""})
        self.assertEqual(response.status_code, 200)
        checks = response.json()["checks"]
        self.assertTrue(checks)
        for check in checks:
            self.assertFalse(check["passed"])

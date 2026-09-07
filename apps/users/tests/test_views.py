"""Tests for the ``apps.users.views`` module."""

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.users.factories import AccountFactory, UserFactory


class ProfileViewTests(TestCase):
    """Tests for :class:`ProfileView`."""

    def setUp(self) -> None:
        self.user = UserFactory()
        self.url = reverse("apps.users:profile")

    def test_anonymous_user_redirected_to_login(self) -> None:
        """Anonymous users are redirected to the login page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_profile_page_renders(self) -> None:
        """Authenticated users can access their profile page."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/profile.html")


class SettingsViewTests(TestCase):
    """Tests for :class:`SettingsView`."""

    def setUp(self) -> None:
        self.user = UserFactory(first_name="Old", last_name="Name")
        self.client.force_login(self.user)
        self.url = reverse("apps.users:settings")

    def test_settings_page_renders(self) -> None:
        """Authenticated users can access their settings page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/settings.html")

    def test_post_updates_user_profile(self) -> None:
        """Posting valid data updates the user profile and redirects."""
        response = self.client.post(
            self.url, {"first_name": "New", "last_name": "Person"}
        )
        self.assertRedirects(response, self.url)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "New")
        self.assertEqual(self.user.last_name, "Person")


class AccountListViewTests(TestCase):
    """Tests for :class:`AccountListView`."""

    def setUp(self) -> None:
        self.account = AccountFactory()
        self.url = reverse("apps.users:account_list")

    def test_anonymous_user_redirected_to_login(self) -> None:
        """Anonymous users are redirected to the login page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_user_without_permission_forbidden(self) -> None:
        """Authenticated users without permission get a 403 response."""
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_superuser_can_list_accounts(self) -> None:
        """Users with the view permission can list accounts."""
        admin = UserFactory(is_staff=True, is_superuser=True)
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/account/list.html")
        self.assertIn(self.account, response.context["accounts"])


class AccountCreateViewTests(TestCase):
    """Tests for :class:`AccountCreateView`."""

    def setUp(self) -> None:
        self.url = reverse("apps.users:account_create")

    def test_user_without_permission_forbidden(self) -> None:
        """Authenticated users without permission get a 403 response."""
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_superuser_can_open_create_form(self) -> None:
        """Users with the add permission can open the create form."""
        admin = UserFactory(is_staff=True, is_superuser=True)
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/account/form.html")


class AccountUpdateViewTests(TestCase):
    """Tests for :class:`AccountUpdateView`."""

    def setUp(self) -> None:
        self.account = AccountFactory()
        self.url = reverse("apps.users:account_update", kwargs={"pk": self.account.pk})

    def test_user_without_permission_forbidden(self) -> None:
        """Authenticated users without permission get a 403 response."""
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_superuser_can_open_update_form(self) -> None:
        """Users with the change permission can open the update form."""
        admin = UserFactory(is_staff=True, is_superuser=True)
        self.client.force_login(admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/account/form.html")
        self.assertEqual(response.context["account"], self.account)


class AccountDeleteViewTests(TestCase):
    """Tests for :class:`AccountDeleteView`."""

    def setUp(self) -> None:
        self.account = AccountFactory()

    def delete_url(self, pk: int) -> str:
        """Return the delete URL for the given account pk."""
        return reverse("apps.users:account_delete", kwargs={"pk": pk})

    def add_delete_permission(self, user) -> None:
        """Grant the delete permission to the user."""
        permission = Permission.objects.get(codename="delete_account")
        user.user_permissions.add(permission)

    def test_anonymous_user_gets_json_403(self) -> None:
        """Anonymous delete attempts receive a JSON 403 response."""
        response = self.client.post(self.delete_url(self.account.pk))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["status"], "error")

    def test_user_without_permission_gets_json_403(self) -> None:
        """Authenticated users without permission get a JSON 403 response."""
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.post(self.delete_url(self.account.pk))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["status"], "error")

    def test_delete_account_success(self) -> None:
        """Authorized users can delete an account (soft delete)."""
        user = UserFactory()
        self.add_delete_permission(user)
        self.client.force_login(user)
        response = self.client.post(self.delete_url(self.account.pk))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.account.refresh_from_db()
        self.assertTrue(self.account.is_removed)

    def test_delete_missing_account_returns_json_404(self) -> None:
        """Deleting a non-existing account returns a JSON 404 response."""
        user = UserFactory()
        self.add_delete_permission(user)
        self.client.force_login(user)
        response = self.client.post(self.delete_url(999999))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["status"], "error")

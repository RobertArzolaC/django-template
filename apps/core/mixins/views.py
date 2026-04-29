from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from django_filters.views import FilterView

from apps.core import mixins as core_mixins


class BaseCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SuccessMessageMixin,
    core_mixins.UserStampMixin,
    CreateView,
):
    pass


class BaseUpdateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    SuccessMessageMixin,
    core_mixins.UserStampMixin,
    UpdateView,
):
    pass


class BaseListView(
    LoginRequiredMixin, PermissionRequiredMixin, FilterView, ListView
):
    pass


class BaseTemplateView(
    LoginRequiredMixin, PermissionRequiredMixin, TemplateView
):
    pass


class BaseFormView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    pass


class BaseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        object_id = kwargs.get("pk")
        entity_name = self.model._meta.verbose_name
        try:
            current_object = self.model.objects.get(pk=object_id)
            current_object.delete()
            return JsonResponse(
                {
                    "status": "success",
                    "message": _(
                        f"The {entity_name} was successfully deleted."
                    ),
                }
            )
        except self.model.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": _(f"{entity_name} not found.")},
                status=404,
            )
        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": str(e)}, status=500
            )

    def handle_no_permission(self):
        return JsonResponse(
            {
                "status": "error",
                "message": _(
                    "You do not have permission to delete this account."
                ),
            },
            status=403,
        )

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "home.html"

    def get(
        self, request: HttpRequest, *args: object, **kwargs: object
    ) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("inventory:my-items")
        return super().get(request, *args, **kwargs)

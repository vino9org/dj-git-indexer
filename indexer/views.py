import re

from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView

from indexer.models import Author, Commit, Repository

_PAGE_SIZE_ = 30


class SearchForm(forms.Form):
    query = forms.CharField(label="", max_length=60)


class SearchPageView(FormView):
    template_name = "indexer/search.html"
    form_class = SearchForm

    def get(self, request):
        query = request.GET.get("query")
        # query = "li.a.lin@accenture.com"
        message, commits = None, []

        if query and len(query) == 40 and re.match(r"[0-9a-f]{40}", query):
            try:
                commits = [Commit.objects.get(sha=query)]
            except Commit.DoesNotExist:
                message = f"cannot find commit {query}"

        elif query and "@" in query:  # search by email address
            match = re.search(r"\b(\S+@\S+)\b", query)  # extract the email address
            if match:
                search_email = match[0]
                authors = Author.objects.filter(real_email=search_email).all()
                if len(authors) > 0:
                    commits = Commit.objects.filter(author__id__in=[a.id for a in authors],).order_by(
                        "-n_lines_changed"
                    )[:_PAGE_SIZE_]
                else:
                    message = f"cannot find any author with the email {search_email}"
            else:
                message = "please enter a valid email address"

        elif query:  # search by repository name
            repo = Repository.objects.filter(repo_name=query).first()
            if repo:
                commits = Commit.objects.filter(repos__id=repo.id,).order_by(
                    "-n_lines_changed"
                )[:_PAGE_SIZE_]
            else:
                message = f"cannot find any repository that matchs {query}"

        if message:
            messages.error(request, message)

        return render(request, self.template_name, {"form": SearchForm(), "commits": commits})


def index(request):
    return HttpResponseRedirect(reverse("indexer:search"))

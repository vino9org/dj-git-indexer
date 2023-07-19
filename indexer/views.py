import re

from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from indexer.models import Author, Commit, Repository

_PAGE_SIZE_ = 30


class SearchForm(forms.Form):
    query = forms.CharField(label="", max_length=60)


def search(request):
    query = request.GET.get("query")
    message, commits, xfilter = None, [], None

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
                xfilter = {"author__id__in": [a.id for a in authors]}
            else:
                message = f"cannot find any author with the email {search_email}"
        else:
            message = "please enter a valid email address"

    elif query:  # search by repository name
        repo = Repository.objects.filter(repo_name=query).first()
        if repo:
            xfilter = {"repos__id": repo.id}
        else:
            message = f"cannot find any repository that matchs {query}"

    if xfilter:
        commits = _commits_by_filter_(xfilter)
    elif message:
        messages.error(request, message)

    return render(request, "indexer/search.html", {"form": SearchForm(), "commits": commits})


def index(request):
    return HttpResponseRedirect(reverse("indexer:search"))


def _commits_by_filter_(kwargs):
    return Commit.objects.filter(**kwargs).order_by("-n_lines_changed")[:_PAGE_SIZE_]

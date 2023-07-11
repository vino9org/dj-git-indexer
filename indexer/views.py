import re

from django import forms
from django.contrib import messages
from django.shortcuts import render
from django.views.generic import FormView

from indexer.models import Author, Commit, Repository

_PAGE_SIZE_ = 30


class SearchForm(forms.Form):
    query = forms.CharField(label="", max_length=80)


class SearchPageView(FormView):
    template_name = "indexer/search.html"
    form_class = SearchForm

    def form_valid(self, form):
        query = form.cleaned_data["query"].strip()
        message = None

        if len(query) == 40 and re.match(r"[0-9a-f]{40}", query):
            try:
                commits = [Commit.objects.get(sha=query)]
                title = "Single Commit"
            except Commit.DoesNotExist:
                message = f"cannot find commit {query}"

        elif "@" in query:
            # extract the email address from the search_term
            match = re.search(r"\b(\S+@\S+)\b", query)
            if match:
                search_email = match[0]
                authors = Author.objects.filter(real_email=search_email).all()
                if len(authors) > 0:
                    title = f"Commits by {search_email}"
                    commits = Commit.objects.filter(author__id__in=[a.id for a in authors]).order_by(
                        "-n_lines_changed"
                    )[:_PAGE_SIZE_]
                else:
                    message = f"cannot find any author with the email {search_email}"
            else:
                message = "please enter a valid email address"

        else:
            # assume the serach term is a repository name
            repo = Repository.objects.filter(repo_name=query).first()
            if repo:
                title = f"Commits in repository {repo.repo_name}"
                commits = Commit.objects.filter(repos__id=repo.id).order_by("-n_lines_changed")[:_PAGE_SIZE_]
            else:
                message = f"cannot find any repo that matchs {query}"

        if message:
            messages.error(self.request, message)
            return render(self.request, "indexer/search.html", {"form": SearchForm()})
        else:
            context = {"commits": commits, "title": title}
            return render(self.request, "indexer/commits.html", context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from .forms import IdeaForm
from .models import idea
from django.forms import modelformset_factory
from django.conf import settings
from .forms import IdeaForm, IdeaTranslationsForm, IdeaFilterForm, IdeaSearchForm
from .models import Idea, IdeaTranslations, RATING_CHOICES
from django.core.paginator import EmptyPage, PageNotAnInteger, Pagin

PAGE_SIZE = getattr(settings, "PAGE_SIZE", 24)

class IdeaList(ListView):
    model = Idea

class IdeaDetail(DetailView):
    model = Idea
    context_object_name = "idea"

class IdeaListView(View):
    form_class = IdeaFilterForm
    template_name = "ideas/idea_list.html"

    def get(self, request, *args, **kwargs):
        form = self.form_class(data=request.GET)
        qs, facets = self.get_queryset_and_facets(form)
        page = self.get_page(request, qs)
        context = {"form": form, "facets": facets, "object_list": page}
        return render(request, self.template_name, context)

    def get_queryset_and_facets(self, form):
        qs = Idea.objects.order_by("title")
        facets = {
            "selected": {},
            "categories": {
                "authors": form.fields["author"].queryset,
                "categories": form.fields["category"].queryset,
                "ratings": RATING_CHOICES,
            },
        }
        if form.is_valid():
            filters = (
                ("author", "author"),
                ("category", "categories"),
                ("rating", "rating"),
            )
            qs = self.filter_facets(facets, qs, form, filters)
        return qs, facets

    @staticmethod
    def filter_facets(facets, qs, form, filters):
        for query_param, filter_param in filters:
            value = form.cleaned_data[query_param]
            if value:
                selected_value = value
                if query_param == "rating":
                    rating = int(value)
                    selected_value = (rating, dict(RATING_CHOICES)[rating])
                facets["selected"][query_param] = selected_value
                filter_args = {filter_param: value}
                qs = qs.filter(**filter_args).distinct()
        return qs

    def get_page(self, request, qs):
        paginator = Paginator(qs, PAGE_SIZE)
        page_number = request.GET.get("page")
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return page

	
class = IdeaFilterForm
    template_name = "ideas/idea_list.html"

    def get(self, request, *args, **kwargs):
        form = self.form_class(data=request.GET)
        qs, facets = self.get_queryset_and_facets(form)
        page = self.get_page(request, qs)
        context = {"form": form, "facets": facets, "object_list": page}
        return render(request, self.template_name, context)

    def get_queryset_and_facets(self, form):
        qs = Idea.objects.order_by("title")
        facets = {
            "selected": {},
            "categories": {
                "authors": form.fields["author"].queryset,
                "categories": form.fields["category"].queryset,
                "ratings": RATING_CHOICES,
            },
        }
        if form.is_valid():
            filters = (
                ("author", "author"),
                ("category", "categories"),
                ("rating", "rating"),
            )
            qs = self.filter_facets(facets, qs, form, filters)
        return qs, facets

    @staticmethod
    def filter_facets(facets, qs, form, filters):
        for query_param, filter_param in filters:
            value = form.cleaned_data[query_param]
            if value:
                selected_value = value
                if query_param == "rating":
                    rating = int(value)
                    selected_value = (rating, dict(RATING_CHOICES)[rating])
                facets["selected"][query_param] = selected_value
                filter_args = {filter_param: value}
                qs = qs.filter(**filter_args).distinct()
        return qs

    def get_page(self, request, qs):
        paginator = Paginator(qs, PAGE_SIZE)
        page_number = request.GET.get("page")
        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return page

class SearchResults(LazyObject):
    def __init__(self, search_object):
        self._wrapped = search_object

    def __len__(self):
        return self._wrapped.count()

    def __getitem__(self, index):
        search_results = self._wrapped[index]
        if isinstance(index, slice):
            search_results = list(search_results)
        return search_results

def idea_handout_pdf(request, pk):

    from django.template.loader import render_to_string
    from django.utils.timezone import now as timezone_now
    from django.utils.text import slugify
    from django.http import HttpResponse

    from weasyprint import HTML
    from weasyprint.fonts import FontConfiguration

    idea = get_object_or_404(Idea, pk=pk)
    context = {"idea": idea}
    html = render_to_string("ideas/idea_handout_pdf.html", context)

    response = HttpResponse(content_type="application/pdf")
    response[
        "Content-Disposition"
    ] = "inline; filename={date}-{name}-handout.pdf".format(
        date=timezone_now().strftime("%Y-%m-%d"), name=slugify(idea.translated_title)
    )

    font_config = FontConfiguration()
    HTML(string=html).write_pdf(response, font_config=font_config)

    return response


def idea_list(request):
    qs = Idea.objects.order_by("title")
    form = IdeaFilterForm(data=request.GET)

    facets = {
        "selected": {},
        "categories": {
            "authors": form.fields["author"].queryset,
            "categories": form.fields["category"].queryset,
            "ratings": RATING_CHOICES,
        },
    }

    if form.is_valid():
        filters = (
            ("author", "author"),
            ("category", "categories"),
            ("rating", "rating"),
        )
        qs = filter_facets(facets, qs, form, filters)

    if settings.DEBUG:
        import logging

        logger = logging.getLogger(__name__)
        logger.info(facets)

    paginator = Paginator(qs, PAGE_SIZE)
    page_number = request.GET.get("page")
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    context = {"form": form, "facets": facets, "object_list": page}
    return render(request, "ideas/idea_list.html", context)

def search_with_elasticsearch(request):
    from .documents import IdeaDocument
    from elasticsearch_dsl.query import Q
    form = IdeaSearchForm(request, data=request.GET)
    search = IdeaDocument.search()
    if form.is_valid():
        value = form.cleaned_data["q"]
        lang_code_underscored = request.LANGUAGE_CODE.replace("-", "_")
        search = search.query(
            Q("match_phrase", **{f"title_{lang_code_underscored}": value})
            | Q("match_phrase", **{f"content_{lang_code_underscored}": value})
            | Q(
                "nested",
                path="categories",
                query=Q(
                    "match_phrase",
                    **{f"categories__title_{lang_code_underscored}": value},
                ),
            )
        )
    search_results = SearchResults(search)

    paginator = Paginator(search_results, PAGE_SIZE)
    page_number = request.GET.get("page")
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    context = {"form": form, "object_list": page}
    return render(request, "ideas/idea_search.html", context)
	
def filter_facets(facets, qs, form, filters):
    for query_param, filter_param in filters:
        value = form.cleaned_data[query_param]
        if value:
            selected_value = value
            if query_param == "rating":
                rating = int(value)
                selected_value = (rating, dict(RATING_CHOICES)[rating])
            facets["selected"][query_param] = selected_value
            filter_args = {filter_param: value}
            qs = qs.filter(**filter_args).distinct()
    return qs
	
@login_required
def add_or_change_idea(request, pk=None):
    idea = None
    if pk:
        idea = get_object_or_404(Idea, pk=pk)
	IdeaTranslationsFormSet = modelformset_factory(
        IdeaTranslations, form=IdeaTranslationsForm, extra=0, can_delete=True	
    )
    if request.method == "POST":
        # form = IdeaForm(
			# data=request.POST, files=request.FILES, instance=idea
		# )
		form = IdeaForm(request, data=request.POST, files=request.FILES, instance=idea)
		translations_formset = IdeaTranslationsFormSet(
            queryset=IdeaTranslations.objects.filter(idea=idea),
            data=request.POST,
            files=request.FILES,
            prefix="translations",
            form_kwargs={"request": request},
        if form.is_valid():
            idea = form.save()
            translations = translations_formset.save(commit=False)
            for translation in translations:
                translation.idea = idea
                translation.save()
            translations_formset.save_m2m()
            for translation in translations_formset.deleted_objects:
                translation.delete()
            return redirect("ideas:idea_detail", pk=idea.pk)
	else:
		form = IdeaForm(request, instance=idea)
        translations_formset = IdeaTranslationsFormSet(
            queryset=IdeaTranslations.objects.filter(idea=idea),
            prefix="translations",
            form_kwargs={"request": request},
		)
	context = {"idea": idea, "form": form, "translations_formset": translations_formset}
    return render(request, "ideas/idea_form.html", context)

@login_required
def delete_idea(request, pk):
    idea = get_object_or_404(Idea, pk=pk)
    if request.method == "POST":
        idea.delete()
        return redirect("ideas:idea_list")
    context = {"idea": idea}
    return render(request, "ideas/idea_deleting_confirmation.html", context)
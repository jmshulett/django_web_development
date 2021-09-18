import uuid
import contextlib
import os
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from pilkit.processors import ResizeToFill

from myproject.apps.core.model_fields import (
    MultilingualCharField,
    MultilingualTextField,
)
from myproject.apps.core.models import (
    CreationModificationDateBase,
    MetaTagsBase,
    UrlBase,
    object_relation_base_factory as generic_relation,
)

from myproject.apps.core.model_fields import TranslatedField
from myproject.apps.core.models import CreationModificationDateBase, UrlBase

def upload_to(instance, filename):
    now = timezone_now()
    base, extension = os.path.splitext(filename)
    extension = extension.lower()
    return f"ideas/{now:%Y/%m}/{instance.pk}{extension}"

RATING_CHOICES = ((1, "★☆☆☆☆"), (2, "★★☆☆☆"), (3, "★★★☆☆"), (4, "★★★★☆"), (5, "★★★★★"))

FavoriteObjectBase = generic_relation(
    is_required=True,
)


OwnerBase = generic_relation(
    prefix="owner",
    prefix_verbose=_("Owner"),
    is_required=True,
    add_related_name=True,
    limit_content_type_choices_to={
        "model__in": (
            "user",
            "group",
        )
    }
)

class Idea(CreationModificationDateBase, UrlBase):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Author"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="authored_ideas",
    )
    title = models.CharField(_("Title"), max_length=200)
    content = models.TextField(_("Content"))
    picture = models.ImageField(
        _("Picture"), upload_to=upload_to
    )
    picture_social = ImageSpecField(
        source="picture",
        processors=[ResizeToFill(1024, 512)],
        format="JPEG",
        options={"quality": 100},
    )
    picture_large = ImageSpecField(
        source="picture", processors=[ResizeToFill(800, 400)], format="PNG"
    )
    picture_thumbnail = ImageSpecField(
        source="picture", processors=[ResizeToFill(728, 250)], format="PNG"
    )
    categories = models.ManyToManyField(
        "categories.Category",
        verbose_name=_("Categories"),
        related_name="category_ideas",
    )
    rating = models.PositiveIntegerField(
        _("Rating"), choices=RATING_CHOICES, blank=True, null=True
    )
    translated_title = TranslatedField("title")
    translated_content = TranslatedField("content")

    class Meta:
        verbose_name = _("Idea")
        verbose_name_plural = _("Ideas")

    def __str__(self):
        return self.title

    def get_url_path(self):
        return reverse("ideas:idea_detail", kwargs={"pk": self.pk})

    @property
    def structured_data(self):
        from django.utils.translation import get_language

        lang_code = get_language()
        data = {
            "@type": "CreativeWork",
            "name": self.translated_title,
            "description": self.translated_content,
            "inLanguage": lang_code,
        }
        if self.author:
            data["author"] = {
                "@type": "Person",
                "name": self.author.get_full_name() or self.author.username,
            }
        if self.picture:
            data["image"] = self.picture_social.url
        return data

    def delete(self, *args, **kwargs):
        from django.core.files.storage import default_storage
        if self.picture:
            with contextlib.suppress(FileNotFoundError):
                default_storage.delete(self.picture_social.path)
                default_storage.delete(self.picture_large.path)
                default_storage.delete(self.picture_thumbnail.path)
            self.picture.delete()
        super().delete(*args, **kwargs)

class IdeaTranslations(models.Model):
    idea = models.ForeignKey(
        Idea,
        verbose_name=_("Idea"),
        on_delete=models.CASCADE,
        related_name="translations",
    )
    language = models.CharField(_("Language"), max_length=7)

    title = models.CharField(_("Title"), max_length=200)
    content = models.TextField(_("Content"))

    class Meta:
        verbose_name = _("Idea Translations")
        verbose_name_plural = _("Idea Translations")
        ordering = ["language"]
        unique_together = [["idea", "language"]]

    def __str__(self):
        return self.title
			
class Like(FavoriteObjectBase, OwnerBase):
    class Meta:
        verbose_name = _("Like")
        verbose_name_plural = _("Likes")

    def __str__(self):
        return _("{owner} likes {object}").format(
            owner=self.owner_content_object,
            object=self.content_object
        )


class Idea(CreationModificationDateBase, MetaTagsBase, UrlBase):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Author"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="authored_ideas",
    )
    title = MultilingualCharField(
        _("Title"),
        max_length=200,
    )
    content = MultilingualTextField(
        _("Content"),
    )

    # category = models.ForeignKey(
        # "categories.Category",
        # verbose_name=_("Category"),
        # blank=True,
        # null=True,
        # on_delete=models.SET_NULL,
        # related_name="category_ideas",
    # )
	
    categories = models.ManyToManyField(
        "categories.Category",
        verbose_name=_("Categories"),
        blank=True,
        related_name="ideas",
    )
	
    class Meta:
        verbose_name = _("Idea")
        verbose_name_plural = _("Ideas")

        constraints = [
            models.UniqueConstraint(
                fields=[f"title_{settings.LANGUAGE_CODE}"],
                condition=~models.Q(author=None),
                name="unique_titles_for_each_author",
            ),
            models.CheckConstraint(
                check=models.Q(**{
                    f"title_{settings.LANGUAGE_CODE}__iregex": r"^\S.*\S$"
                    # starts with non-whitespace,
                    # ends with non-whitespace,
                    # anything in the middle
                }),
                name="title_has_no_leading_and_trailing_whitespaces",
            )
        ]

    def __str__(self):
        return self.title

    def get_url_path(self):
        return reverse("idea_details", kwargs={
            "idea_id": str(self.pk),
        })

    def clean(self):
        import re
        lang_code_underscored = settings.LANGUAGE_CODE.replace("-", "_")
        title_field = f"title_{lang_code_underscored}"
        title_value = getattr(self, f"title_{lang_code_underscored}")
        if self.author and Idea.objects.exclude(pk=self.pk).filter(**{
            "author": self.author,
            title_field: title_value,
        }).exists():
            raise ValidationError(_("Each idea of the same user should have a unique title."))
        if not re.match(r"^\S.*\S$", title_value):
            raise ValidationError(_("The title cannot start or end with a whitespace."))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        print("save() from Idea called")

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        print("delete() from Idea called")

    def test(self):
        super().test()
        print("test() from Idea called")

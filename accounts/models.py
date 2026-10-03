import uuid
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin,
)
from django.conf import settings
from django.utils.text import slugify

# Create your models here.


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError("User Must Has an Email Address")

        if not username:
            raise ValueError("User Must Has an username")

        user = self.create(
            email=self.normalize_email(email),
            username=username,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            password=password,
        )

        user.is_superuser = True
        user.is_active = True
        user.is_admin = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=300, unique=True)

    img = models.ImageField(
        default="1.png", upload_to="ProfileImg", null=True, blank=True
    )

    bio = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    place = models.CharField(max_length=100, null=True, blank=True)
    is_private = models.BooleanField(default=False)
    show_followers = models.BooleanField(default=True)
    show_following = models.BooleanField(default=True)
    check_follower = models.BooleanField(default=False)

    slug = models.SlugField(null=True, blank=True)

    verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser or super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        return self.is_superuser or super().has_module_perms(app_label)

    def get_all_permissions(self, obj=None):
        if self.is_superuser:
            return set()
        return super().get_all_permissions(obj)

    def get_group_permissions(self, obj=None):
        if self.is_superuser:
            return set()
        return super().get_group_permissions(obj)

    def location(self):
        if self.city and not self.place:
            return f"{self.city}"
        elif self.place and not self.city:
            return f"{self.place}"
        elif self.city and self.place:
            return f"{self.city} ({self.place})"
        else:
            return f""

    def save(self, *args, **kwargs):
        self.slug = slugify(self.username)
        return super(User, self).save(*args, **kwargs)


class Follow(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="following", on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="followers", on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=8, choices=Status.choices, default=Status.PENDING
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"], name="unique_follow"
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.follower} → {self.following} ({self.status})"


class Contact(models.Model):
    email = models.EmailField(max_length=250)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"

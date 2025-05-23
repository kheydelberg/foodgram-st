from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """Custom user model with email as username field and avatar support."""

    email = models.EmailField(_('email address'), unique=True, max_length=70)
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/',
        blank=True,
        null=True
    )
    first_name = models.CharField(_('first name'), max_length=100)
    last_name = models.CharField(_('last name'), max_length=100)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        """Meta options for CustomUser model."""

        ordering = ['username']
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        """String representation of the user."""
        return self.username


class Follow(models.Model):
    """Model representing user subscriptions (who follows whom)."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name=_('user'),
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name=_('author'),
    )

    class Meta:
        """Meta options for Follow model."""

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_follow'
            )
        ]
        ordering = ['user__username', 'author__username']
        verbose_name = _('subscription')
        verbose_name_plural = _('subscriptions')

    def __str__(self):
        """String representation of the follow relationship."""
        return f'{self.user} → {self.author}'

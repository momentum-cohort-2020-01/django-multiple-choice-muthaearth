from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist

# Select from list of available Python interpreters for current project.
from rest_framework.authtoken.models import Token

from datetime import timedelta

# # Consider creating a custom user model from scratch as detailed at
# # https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#specifying-a-custom-user-model


# class User(AbstractUser):
#     pass

class Deck(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(default='')

    def __str__(self):
        return self.name

    def get_cards_num(self):
        cards = Flashcard.objects.get_cards_to_study(
            user=self.owner, deck_id=self.id, days=0)
        return len(cards)


class FlashcardManager(models.Manager):
    def create_flashcard(self, user, question, answer, deck_name):
        try:
            deck = Deck.objects.get(owner=user, name=deck_name)
        except ObjectDoesNotExist:
            deck = Deck(owner=user, name=deck_name)
            deck.save()

        self.create(owner=user, question=question, answer=answer,
                    deck=deck)
        return deck

    def get_cards_to_study(self, user, deck_id, days):
        ##import ipdb; ipdb.set_trace()
        next_due_date = timezone.now() + timedelta(days=days)
        cards = Flashcard.objects.filter(deck__id=deck_id, deck__owner=user,
                                         next_due_date__lte=next_due_date)
        return cards


class Flashcard(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_shown_at = models.DateTimeField(auto_now_add=True)
    # items past due date queued for review by user
    next_due_date = models.DateTimeField(default=timezone.now)
    # how easy question is
    easiness = models.FloatField(default=2.5)
    consec_correct_answers = models.IntegerField(default=0)

    objects = FlashcardManager()

    def __str__(self):
        return self.question

    def get_next_due_date(self, rating):
        """ Supermemo-2 algorithm realization.
        http://www.blueraja.com/blog/477/a-better-spaced-repetition-learning-algorithm-sm2
        Args:
            easiness (int) - answer rating (0=worst, 5=best)

        Returns:
            next_due_date,easiness,consec_correct_answers (tuple) - information
                to update Flashcard data
        """
        # user gives themself a performance rating after review of item
        correct = (rating >= 3)
        blank = (rating < 2)
        # performance rating calc
        easiness = self.easiness - 0.8 + 0.28*rating + 0.02*rating**2
        if easiness < 1.3:
            easiness = 1.3
        if correct:
            consec_correct_answers = self.consec_correct_answers + 1
            # next_due_date to review item
            interval = 6*easiness**(consec_correct_answers-1)
        elif blank:
            consec_correct_answers = 0
            interval = 0
        else:
            consec_correct_answers = 0
            interval = 1

        next_due_date = timezone.now() + timedelta(days=interval)
        return next_due_date, easiness, consec_correct_answers

    def save(self, rating=None, *args, **kwargs):
        if rating:
            result = self.get_next_due_date(rating)
            self.next_due_date = result[0]
            self.easiness = result[1]
            self.consec_correct_answers = result[2]
        # Call the "real" save() method.
        super(Flashcard, self).save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

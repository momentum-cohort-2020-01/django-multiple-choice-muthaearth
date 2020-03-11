from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie

import random
import json

from api.models import Deck, Flashcard
from .forms import CardForm

CARD_LIMIT = 5


@login_required
def home(request):
    """
    App home page
    """
    if request.method == 'GET':
        decks = Deck.objects.filter(owner=request.user)
        context = {'user': request.user, 'decks': decks}
        return render(request, 'flashcards/index.html', context)


def profile(request):
    """
    ...
    """
    if request.method == 'GET':
        pass


def about(request):
    """
    ...
    """
    if request.method == 'GET':
        return render(request, 'flashcards/about.html')


@login_required
def add(request):
    """
    Add new flashcard
    """
    if request.method == 'POST':
        form = CardForm(request.POST)
        if form.is_valid():
            deck_name = form.cleaned_data['deck']
            question = form.cleaned_data['question']
            answer = form.cleaned_data['answer']
            user = request.user
            Flashcard.objects.create_flashcard(user=user, question=question,
                                               answer=answer, deck_name=deck_name)
            return HttpResponseRedirect(reverse('add-card'))
    else:
        form = CardForm()

    return render(request, 'flashcards/add.html', {'form': form})


@login_required
@ensure_csrf_cookie
def study(request, deck_id):
    """
    Study cards page (JS driven)
    """
    if request.method == 'GET':
        return render(request, 'flashcards/study.html')


@login_required
@ensure_csrf_cookie
def get_cards(request, deck_id):
    """
    Get cards to study (ajax)
    """

    if request.method == 'GET':
        cards = Flashcard.objects.filter(owner=request.user, deck=deck_id,
                                         next_due_date__lte=timezone.now())
        count = len(cards)
        data = {'count': count, 'cards': []}

        num = count if count < CARD_LIMIT else CARD_LIMIT
        if num:
            # generate list of random indexes
            idx = random.sample(range(count), num)
            for i in idx:
                card = cards[i]
                # split question into a word list on new line
                question = '<p>' + \
                    '</p><p>'.join(card.question.split('\r\n'))+'</p>'
                answer = '<p>'+'</p><p>'.join(card.answer.split('\r\n'))+'</p>'
                data['cards'].append({'id': card.pk, 'question': question,
                                      'answer': answer})

        return JsonResponse(data)
    else:
        data = json.loads(str(request.body, 'utf-8'))
        for response in data:
            card = Flashcard.objects.get(
                owner=request.user, pk=response['id'])
            card.save(rating=res['result'])

        return JsonResponse({'status': 'OK'})


@login_required
def delete_deck(request):
    """
    Delete deck (ajax)
    """
    if request.method == 'POST':
        data = json.loads(str(request.body, 'utf-8'))
        if 'deck_id' in data:
            deck = Deck.objects.get(owner=request.user, pk=data['deck_id'])
            deck.delete()
            return JsonResponse({'status': 'OK'})

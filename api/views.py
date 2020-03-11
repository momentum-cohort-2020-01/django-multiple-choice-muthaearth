from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response

from .models import Deck, Flashcard
from .serializers import DeckSerializer, CardSerializer, RatingSerializer


@api_view(['GET', 'POST'])
@csrf_exempt
def decks_list(request):
    """
    List all decks
    """
    # get specified resource name
    if request.method == 'GET':
        if 'name' in request.GET:
            decks = Deck.objects.filter(
                owner=request.user, name=request.GET['name'])
        else:
            # return resource name
            decks = Deck.objects.filter(owner=request.user)
        serializer = DeckSerializer(decks, many=True)
        return Response(serializer.data)

    # user send data to Deck resource
    elif request.method == 'POST':
        serializer = DeckSerializer(data=request.data)
        if serializer.is_valid():
            if request.user.is_anonymous:
                return Response(serializer.errors,
                                status=status.HTTP_401_UNAUTHORIZED)
            else:
                serializer.save(owner=request.user)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
def deck_details(request, deck_id):
    """
    Deck details
    """
    if request.method == 'GET':
        deck = get_object_or_404(Deck, pk=deck_id, owner=request.user)
        serializer = DeckSerializer(deck)
        return Response(serializer.data)
    elif request.method == 'DELETE':
        deck = get_object_or_404(Deck, pk=deck_id, owner=request.user)
        deck.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@csrf_exempt
def cards_list(request, deck_id):
    """
    List all flashcards
    """
    # get card list resource
    if request.method == 'GET':
        if 'days' in request.GET:
            cards = Flashcard.objects.get_cards_to_study(deck_id=deck_id,
                                                         user=request.user, days=int(request.GET['days']))
        else:
            cards = Flashcard.objects.filter(
                deck__id=deck_id, deck__owner=request.user)
        serializer = CardSerializer(cards, many=True)
        return Response(serializer.data)

    # post data to card list resource
    elif request.method == 'POST':
        try:
            deck = Deck.objects.get(id=deck_id)
        except ObjectDoesNotExist:
            return Response(serializer.errors,
                            status=status.HTTP_401_BAD_REQUEST)

        serializer = CardSerializer(data=request.data)
        if serializer.is_valid():
            if request.user.is_anonymous:
                return Response(serializer.errors,
                                status=status.HTTP_401_UNAUTHORIZED)
            else:
                # saves deck if user authenticated, deck id, and serialized card data has been rendered
                serializer.save(owner=request.user, deck=deck)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_401_BAD_REQUEST)


@api_view(['GET'])
def card_details(request, deck_id, card_id):
    """
    Card details
    """
    if request.method == 'GET':
        card = get_object_or_404(Flashcard, pk=card_id, deck__id=deck_id,
                                 owner=request.user)
        serializer = CardSerializer(card)
        # return deck and serialized card data
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_401_BAD_REQUEST)


@api_view(['GET', 'POST'])
def card_ratings(request, deck_id, card_id):
    """
    Card ratings (state)
    """
    if request.method == 'GET':
        card = get_object_or_404(Flashcard, pk=card_id, deck__id=deck_id,
                                 owner=request.user)
        serializer = RatingSerializer(card)
        return Response(serializer.data)

    elif request.method == 'POST':
        card = get_object_or_404(Flashcard, pk=card_id, deck__id=deck_id,
                                 owner=request.user)
        serializer = RatingSerializer(card, data=request.data)
        if serializer.is_valid():
            serializer.save(rating=request.data['rating'])
            # return serialized item performance rating
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_401_BAD_REQUEST)

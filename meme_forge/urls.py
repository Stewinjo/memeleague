from django.urls import path
from . import views

app_name = 'memeforge'

urlpatterns = [
    path('start/<str:lobby_code>/', views.start_game, name='start_game'),  # Start the game
    path('reroll/<str:lobby_code>/', views.reroll_template, name='reroll_template'),  # Handle reroll requests
    path('submit/<str:lobby_code>/', views.submit_meme, name='submit_meme'),  # Submit a meme
    path('vote/<str:lobby_code>/', views.vote_meme, name='vote_meme'),  # Handle voting
    path('leaderboard/<str:lobby_code>/', views.final_leaderboard, name='final_leaderboard'),  # Final leaderboard
    path('next-round/<str:lobby_code>/', views.next_round, name='next_round'),  # Transition to the next round
]

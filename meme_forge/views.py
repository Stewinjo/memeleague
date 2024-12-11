from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import MemeTemplate
from random import sample
from lobby.views import redis_client, load_lobby_from_redis, save_lobby_to_redis
from core.dataclasses import MemeForge
from enum import Enum

class Likes(Enum):
    LIKE = "like"
    SUPERLIKE = "superlike"
    DISLIKE = "dislike"

    @staticmethod
    def validate_like(like):
        valid_likes = {like.value for like in Likes}
        if not like in valid_likes:
            raise ValueError(f"Invalid like. Valid options are: {valid_likes}")

#-------- Helper Functions --------

def select_templates(participants, rounds, rerolls, constraints):
    """
    Selects templates for the game based on the given constraints.
    Ensures duplicates are avoided unless the database lacks enough templates.
    """
    templates = MemeTemplate.objects.filter(tags__overlap=constraints.get("tags", []))
    total_required = participants * rounds * rerolls
    total_available = templates.count()

    if total_available <= total_required:
        # Not enough templates, allow duplicates
        selected_templates = list(templates)
    else:
        # Sample without duplicates
        selected_templates = sample(list(templates), total_required)

    return selected_templates

def load_templates_to_redis(lobby_code, templates):
    """
    Load templates into Redis for use during the game.
    """
    redis_key = f"lobby:{lobby_code}:templates"
    existing_templates = redis_client.hkeys(redis_key)  # Get already loaded templates

    new_templates = {}
    for template in templates:
        if template.id not in existing_templates:
            new_templates[template.id] = {
                "name": template.name,
                "image_url": template.image_url,
                "text_input_count": template.text_input_count,
                "tags": template.tags,
            }

    # Add new templates to Redis
    if new_templates:
        redis_client.hmset(redis_key, new_templates)
        redis_client.expire(redis_key, 7200)  # TTL of 2 hours

def calculate_scores(lobby_code):
    """
    Calculate scores based on votes stored in Redis.
    """
    votes_key = f"lobby:{lobby_code}:votes"
    submissions_key = f"lobby:{lobby_code}:submissions"

    votes = redis_client.hgetall(votes_key)
    submissions = redis_client.hgetall(submissions_key)

    scores = {}

    for submission_id, submission_data in submissions.items():
        submission = json.loads(submission_data)
        participant_id = submission_id  # Assuming submission ID maps to participant
        participant_score = scores.get(participant_id, 0)

        # Calculate scores based on votes
        for vote_key, vote_type in votes.items():
            if submission_id in vote_key:  # Check if vote is for this submission
                if vote_type == Likes.LIKE.value:
                    participant_score += 2
                elif vote_type == Likes.SUPERLIKE.value:
                    participant_score += 5
                elif vote_type == Likes.DISLIKE.value:
                    participant_score -= 1

        scores[participant_id] = participant_score

    # Save scores to Redis for the current round
    leaderboard_key = f"lobby:{lobby_code}:leaderboard"
    redis_client.hmset(leaderboard_key, scores)

    return scores

def update_leaderboard(lobby_code):
    """
    Calculate scores and broadcast updated leaderboard to all participants.
    """
    scores = calculate_scores(lobby_code)

    # Send updated leaderboard via WebSocket
    group_name = f"lobby_{lobby_code}"
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "leaderboard_update",
            "data": {"scores": scores},
        },
    )

#-------- View Functions --------

def reroll_template(request:HttpResponse, lobby_code):
    """
    Handle template reroll requests from a participant.
    """
    lobby = load_lobby_from_redis(lobby_code)
    if not lobby:
        return JsonResponse({"error": "Lobby not found"}, status=404)

    participant_id = request.user.id
    remaining_rerolls_key = f"lobby:{lobby_code}:rerolls:{participant_id}"
    remaining_rerolls = redis_client.get(remaining_rerolls_key)

    if not remaining_rerolls or int(remaining_rerolls) <= 0:
        return JsonResponse({"error": "No rerolls remaining"}, status=400)

    # Get a new random template from Redis
    redis_key = f"lobby:{lobby_code}:templates"
    all_templates = redis_client.hgetall(redis_key)
    new_template = sample(list(all_templates.values()), 1)[0]

    # Deduct one reroll and return the new template
    redis_client.decr(remaining_rerolls_key)
    return JsonResponse({"template": new_template})

def submit_meme(request:HttpResponse, lobby_code):
    """
    Handle meme submissions from participants.
    """
    lobby = load_lobby_from_redis(lobby_code)
    if not lobby:
        return JsonResponse({"error": "Lobby not found"}, status=404)

    participant_id = request.user.id
    submission_text = request.POST.get("submission_text")
    template_id = request.POST.get("template_id")

    # Validate the template belongs to this participant
    redis_key = f"lobby:{lobby_code}:submissions"
    submissions = redis_client.hgetall(redis_key)

    redis_client.hset(
        redis_key,
        participant_id,
        json.dumps({"template_id": template_id, "text": submission_text}),
    )

    return JsonResponse({"message": "Meme submitted successfully"})

def start_game(request: HttpResponse, lobby_code):
    """
    Start the game by updating the Lobby with the MemeForge gamemode
    and notifying all participants to redirect to the game interface.
    """
    if request.method == "POST":
        lobby = load_lobby_from_redis(lobby_code)
        if not lobby:
            return JsonResponse({"error": "Lobby not found"}, status=404)

        # Ensure the request is made by the host
        if request.session.get("host_lobby_code") != lobby_code:
            return JsonResponse({"error": "Only the host can start the game."}, status=403)

        memeforge = MemeForge.from_post_request(request)

        if memeforge:
            # Assign the game mode to the lobby and mark the game as started
            lobby.gamemode = memeforge
            lobby.game_started = True

            # Select and load templates into Redis
            participants = len(lobby.participants)
            templates = select_templates(
                participants, memeforge.rounds, memeforge.rerolls_per_player, memeforge.template_constraints
            )
            load_templates_to_redis(lobby_code, templates)

            # Save the updated lobby to Redis
            save_lobby_to_redis(lobby)

            # Notify all participants via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"lobby_{lobby_code}",
                {
                    "type": "game_start",
                    "message": {
                        "redirect_url": f"/meme-forge/game/{lobby_code}/",
                    },
                },
            )

            return JsonResponse({"message": "Game started", "redirect_url": f"/memeforge/game/{lobby_code}/"})
        else:
            return JsonResponse({"error": "Invalid game mode settings."}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)

def vote_meme(request:HttpResponse, lobby_code):
    """
    Handle voting on memes.
    """
    lobby = load_lobby_from_redis(lobby_code)
    if not lobby:
        return JsonResponse({"error": "Lobby not found"}, status=404)

    voter_id = request.user.id
    submission_id = request.POST.get("submission_id")
    like = request.POST.get("like")

    # Ensure valid vote type
    if not Likes.validate_like(like):
        return JsonResponse({"error": "Invalid vote type"}, status=400)

    # Track votes in Redis
    votes_key = f"lobby:{lobby_code}:votes"
    redis_client.hset(
        votes_key,
        f"{voter_id}:{submission_id}",
        like,
    )

    return JsonResponse({"message": "Vote recorded"})

def final_leaderboard(request:HttpResponse, lobby_code):
    """
    Aggregate scores from all rounds and display the final leaderboard.
    """
    leaderboard_key = f"lobby:{lobby_code}:leaderboard"
    scores = redis_client.hgetall(leaderboard_key)

    # Sort participants by score
    sorted_scores = sorted(scores.items(), key=lambda x: int(x[1]), reverse=True)

    return JsonResponse({"leaderboard": sorted_scores})

def next_round(request: HttpResponse, lobby_code):
    """
    Transition to the next round or end the game.
    """
    current_round_key = f"lobby:{lobby_code}:current_round"
    current_round = int(redis_client.get(current_round_key) or 0)
    lobby = load_lobby_from_redis(lobby_code)

    if current_round >= lobby.gamemode.rounds:
        # End game if rounds are complete
        return final_leaderboard(request, lobby_code)

    # Increment round and reset submissions and votes
    redis_client.set(current_round_key, current_round + 1)
    redis_client.delete(f"lobby:{lobby_code}:submissions")
    redis_client.delete(f"lobby:{lobby_code}:votes")

    return JsonResponse({"message": f"Round {current_round + 1} started"})

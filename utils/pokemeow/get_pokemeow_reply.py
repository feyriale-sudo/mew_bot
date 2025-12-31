import discord


# ❀─────────────────────────────────────────❀
#      💖  Get Pokemeow Reply
# ❀─────────────────────────────────────────❀
async def get_pokemeow_reply_member(message: discord.Message) -> discord.Member | None:
    """
    Determines if the message is a PokéMeow bot reply.
    If yes, returns the member that PokéMeow replied to.
    Returns None otherwise.
    """
    # 🛑 Only process messages from PokéMeow
    author_str = str(message.author).lower()
    if "pokémeow" not in author_str and "pokemeow" not in author_str:
        return None

    # 🛑 Ensure the message is a reply
    if not getattr(message, "reference", None):
        return None

    resolved_msg = getattr(message.reference, "resolved", None)
    if not isinstance(resolved_msg, discord.Message):
        return None

    member = (
        resolved_msg.author if isinstance(resolved_msg.author, discord.Member) else None
    )
    return member


async def get_command_user(interaction: discord.Interaction) -> discord.Member | None:
    """
    Returns the member object of the user who invoked the slash command.
    """
    if hasattr(interaction, "user") and isinstance(interaction.user, discord.Member):
        return interaction.user
    if hasattr(interaction, "author") and isinstance(
        interaction.author, discord.Member
    ):
        return interaction.author
    return None

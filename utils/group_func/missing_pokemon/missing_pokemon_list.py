import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

from config.aesthetic import *
from config.settings import Channels
from utils.db.missing_pokemon_db_func import (
    fetch_user_missing_dict,
    fetch_user_missing_list,
    fetch_user_missing_pokemon,
    remove_all_missing_for_user,
    remove_missing_pokemon,
)
from utils.logs.pretty_log import pretty_log
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer, pretty_error


# 🌸───────────────────────────────────────────────🌸
# 🩷 ⏰ PAGINATED MISSING POKEMON LIST FUNCTION          🩷
# 🌸───────────────────────────────────────────────🌸
class MissingPokemonPaginator(View):
    def __init__(self, bot, user, entries, per_page=20, timeout=120):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user = user
        self.entries = entries
        self.per_page = per_page
        self.page = 0
        self.max_page = (len(entries) - 1) // per_page
        self.message: discord.Message | None = None  # store the sent message

        # 🟣 If there's only one page, remove buttons entirely
        if self.max_page == 0:
            self.clear_items()  # <-- removes all buttons

    @discord.ui.button(emoji=Emojis.back, style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This is not your paginator.", ephemeral=True
            )
            return
        self.page -= 1
        if self.page < 0:
            self.page = self.max_page
        await interaction.response.edit_message(embed=(await self.get_embed()))

    @discord.ui.button(emoji=Emojis.next, style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This is not your paginator.", ephemeral=True
            )
            return
        self.page += 1
        if self.page > self.max_page:
            self.page = 0
        await interaction.response.edit_message(embed=(await self.get_embed()))

    #
    async def get_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page
        page_entries = self.entries[start:end]

        # 🩷 Build a beautiful list display
        description_lines = []
        for idx, r in enumerate(page_entries, start=start + 1):
            pokemon = r["pokemon_name"].title()
            dex = r["dex"]
            role_id = r.get("role_id")
            channel_id = r.get("channel_id")

            # 🌸 Handle optional fields prettily
            extra_info = []
            if role_id:
                extra_info.append(f"<@&{role_id}>")  # mention the role
            if channel_id:
                extra_info.append(f"<#{channel_id}>")  # mention the channel

            extras = f" 〔{'・'.join(extra_info)}〕" if extra_info else ""
            description_lines.append(f"`{idx:>02}.` **{pokemon}** — #{dex}{extras}")

        # 🌸 Handle empty gracefully
        if not description_lines:
            description_lines = ["*No missing Pokémon entries found.*"]

        embed = discord.Embed(
            title=f"🐰 Missing Pokémon Checklist ({len(self.entries)})",
            description="\n".join(description_lines),
        )

        # 🪞 Add footer with page info
        footer_text = f"Page {self.page + 1} of {self.max_page + 1}"
        embed = await design_embed(
            user=self.user,
            embed=embed,
            footer_text=footer_text,
            thumbnail_url=Thumbnails.Missing_List,
        )
        return embed

    async def on_timeout(self):
        """Disable all buttons when paginator times out."""
        for child in self.children:
            if isinstance(child, Button):
                child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception as e:
                pretty_log("error", f"Failed to disable paginator buttons: {e}")


# ❀─────────────────────────────────────────❀
#      💖  Missing Pokémon List Function
# ❀─────────────────────────────────────────❀
async def missing_pokemon_list_func(
    bot: commands.Bot, interaction: discord.Interaction
):
    """List all of the user's missing Pokémon entries."""
    user = interaction.user
    user_id = user.id
    user_name = user.name

    handler = await pretty_defer(
        interaction=interaction,
        content="Fetching your missing Pokémon entries...",
        ephemeral=False,
    )

    entries = await fetch_user_missing_list(bot, user_id)
    if not entries:
        await handler.error("You have no missing Pokémon entries.")
        return

    # 🟣 Sort reminders by dex (ascending)
    entries.sort(key=lambda r: r["dex"])

    paginator = MissingPokemonPaginator(bot, interaction.user, entries)
    embed = await paginator.get_embed()

    sent = await handler.success(embed=embed, view=paginator, content="")
    paginator.message = sent  # keep reference so on_timeout can edit

import discord

from config.aesthetic import *
from utils.logs.pretty_log import pretty_log
from utils.visuals.design_embed import design_embed
from utils.visuals.pretty_defer import pretty_defer
from utils.visuals.name_helpers import format_display_pokemon_name

# 🍇──────────────────────────────
#      🌀 Market Alert Paginator
# 🍇──────────────────────────────
class MarketAlertPaginator(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__(timeout=120)
        self.embeds = embeds
        self.index = 0

    @discord.ui.button(emoji=Emojis.back, style=discord.ButtonStyle.secondary)
    async def prev_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.index = (self.index - 1) % len(self.embeds)
        await interaction.response.edit_message(
            embed=self.embeds[self.index], view=self
        )

    @discord.ui.button(emoji=Emojis.next, style=discord.ButtonStyle.secondary)
    async def next_page(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.index = (self.index + 1) % len(self.embeds)
        await interaction.response.edit_message(
            embed=self.embeds[self.index], view=self
        )


# 🌸──────────────────────────────
#       💜 Mine Market Alerts
# 🌸──────────────────────────────
async def mine_market_alerts_func(bot, interaction: discord.Interaction):
    """
    Fetch all market alerts for a user, build embeds with pagination if needed,
    and send them directly to the interaction.
    """
    from utils.cache.market_alert_cache import (
        fetch_user_alerts_from_cache,
        get_user_alert_count,
    )

    user = interaction.user
    user_id = user.id

    # ⏳ Pretty loader while fetching
    handle = await pretty_defer(
        interaction=interaction,
        content="Fetching your Market Alerts...",
        ephemeral=False,
    )

    # 📊 Get user status
    count = get_user_alert_count(user_id)
    display_count = f"Total Alerts: {count}"
    status_message = display_count if count > 0 else "No Active Alerts"

    try:
        # 🔹 Use cache instead of hitting DB
        alerts = fetch_user_alerts_from_cache(user_id)

        # ✅ Sort alerts by dex_number
        alerts = sorted(alerts, key=lambda a: int(a.get("dex_number", 0)))

        # 🟣 No alerts case
        if not alerts:
            embed = discord.Embed(
                title=f"No Market Alerts",
                description="You don’t have any active market alerts right now.",
                color=0xFF9BBF,
            )
            embed = await design_embed(
                embed=embed,
                user=user,
                footer_text="Use /market-alert add to create one ✨",
                thumbnail_url=Thumbnails.Market_Mine,
            )
            await handle.success(embed=embed, content="")
            return

        # 🟣 Build alert embeds
        embeds = []
        embed = discord.Embed(
            title=f"Your Market Alerts",
            description=f"{status_message}\nHere’s a list of your current market alerts:\n\n",
            color=0xFF9BBF,
        )

        # embed.set_thumbnail(url=Espeon_Thumbnail.purple_list)
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)

        char_count = len(embed.description)

        for alert in alerts:
            pokemon_name = alert["pokemon"]
            display_name = format_display_pokemon_name(pokemon_name)
            field_name = f"{display_name} (Dex #{alert['dex_number']})"
            role_mention = f"<@&{alert['role_id']}>" if alert.get("role_id") else "None"
            notify_status = "✅ Enabled" if alert.get("notify", True) else "❌ Disabled"
            field_value = (
                f"> - **Max Price:** {Emojis.PokeCoin} {alert['max_price']:,}\n"
                f"> - **Channel:** <#{alert['channel_id']}>\n"
                f"> - **Role:** {role_mention}\n"
                f"> - **Notify:** {notify_status}"
            )

            # Split embeds if field/char limits exceeded
            if (
                len(embed.fields) >= 25
                or (char_count + len(field_name) + len(field_value)) > 5500
            ):
                embeds.append(embed)
                embed = discord.Embed(
                    title="🌸 Your Market Alerts (continued)",
                    color=0xAA88FF,
                )
                char_count = 0

            embed.add_field(name=field_name, value=field_value, inline=False)
            char_count += len(field_name) + len(field_value)
            embed.set_thumbnail(url=Thumbnails.Market_Mine)

        embeds.append(embed)

        # Footer & pagination info
        total_pages = len(embeds)
        for i, e in enumerate(embeds, start=1):
            e.set_footer(
                text=f"🌸 Use /market-alert remove or /market-alert toggle to manage these alerts! | Page {i}/{total_pages}"
            )

        # 🟢 Send single or paginated embed
        if len(embeds) == 1:
            await handle.success(embed=embeds[0], content="")
        else:
            view = MarketAlertPaginator(embeds)
            await handle.success(embed=embeds[0], view=view, content="")

        # 📦 Log success
        pretty_log(
            "sent",
            f"Sent market alerts to user {user_id} ({len(alerts)} alerts) from cache",
        )

    except Exception as e:
        # ❌ Error handling
        pretty_log(
            "error",
            f"Failed to fetch or send market alerts: {e}",
            include_trace=True,
        )
        await interaction.followup.send(
            f"❌ Failed to fetch market alerts: {e}", ephemeral=True
        )
